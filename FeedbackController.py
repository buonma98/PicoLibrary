"""
FeedbackController.py
Controller class implementing the State Machine for QuickRate kiosk.
Author: buonma98
"""

import time
from Log import Log
from StateModel import StateModel
from Counters import SoftwareTimer
from KioskView import KioskView
from FeedbackStats import FeedbackStats
from ManagerAlert import ManagerAlert


class FeedbackController:
    """
    FeedbackController coordinates the entire QuickRate satisfaction kiosk system.
    It integrates hardware sensors and buttons into a 6-state state machine:
      - State 0: Welcome (idle / waiting for customer)
      - State 1: Selection (prompting customer for feedback)
      - State 2: Happy (positive feedback recorded)
      - State 3: Unhappy (negative feedback recorded)
      - State 4: Alarm (manager alert activated on low satisfaction < 30%)
      - State 5: Alarm Silenced (buzzer silenced, ratings preserved, awaiting reset)
    """

    STATE_WELCOME = 0
    STATE_SELECTION = 1
    STATE_HAPPY = 2
    STATE_UNHAPPY = 3
    STATE_ALARM = 4
    STATE_ALARM_SILENCED = 5

    def __init__(self, view: KioskView, stats: FeedbackStats, alert: ManagerAlert,
                 greenButton, redButton, managerButton, ultrasonicSensor,
                 debug: bool = True):
        """
        Initialize the FeedbackController and configure the state model.

        Parameters:
        -----------
        view : KioskView
            The kiosk view presenting LCD and LED outputs.
        stats : FeedbackStats
            Statistics tracker for positive/negative votes and thresholds.
        alert : ManagerAlert
            Manager alert controller driving the buzzer.
        greenButton : Button
            Button on GP13 (Positive feedback / Reset during alert).
        redButton : Button
            Button on GP14 (Negative feedback).
        managerButton : Button
            Button on GP15 (Manager silence button).
        ultrasonicSensor : UltrasonicSensor
            Ultrasonic sensor on GP2 (trig) / GP3 (echo) with 10 cm threshold.
        debug : bool
            Enable debug logging for state transitions.
        """
        self.view: KioskView = view
        self.stats: FeedbackStats = stats
        self.alert: ManagerAlert = alert

        # Internal SoftwareTimer generating 'timer_timeout' events
        self.timer: SoftwareTimer = SoftwareTimer(name="timer", handler=None)

        # 6-state StateModel with self as handler
        self.stateModel: StateModel = StateModel(6, self, debug=debug)

        # Configure buttons
        # Button names dictate events: [name]_press and [name]_release
        self.greenButton = greenButton
        self.redButton = redButton
        self.managerButton = managerButton
        self.ultrasonicSensor = ultrasonicSensor

        self.stateModel.addButton(self.greenButton)
        self.stateModel.addButton(self.redButton)
        self.stateModel.addButton(self.managerButton)

        # Configure ultrasonic sensor
        # Sensor name dictates event: [name]_trip and [name]_untrip
        self.stateModel.addSensor(self.ultrasonicSensor)

        # Configure software timer
        self.stateModel.addTimer(self.timer)

        # Set up state transitions as specified in the state machine diagram:
        # State 0 (Welcome): trips on uss_trip (person within 10 cm) -> goes to State 1 (Selection)
        self.stateModel.addTransition(self.STATE_WELCOME, ["uss_trip"], self.STATE_SELECTION)

        # State 1 (Selection):
        # green_press -> State 2 (Happy)
        # red_press -> State 3 (Unhappy)
        # timer_timeout (customer left without voting) -> State 0 (Welcome)
        self.stateModel.addTransition(self.STATE_SELECTION, ["green_press"], self.STATE_HAPPY)
        self.stateModel.addTransition(self.STATE_SELECTION, ["red_press"], self.STATE_UNHAPPY)
        self.stateModel.addTransition(self.STATE_SELECTION, ["timer_timeout"], self.STATE_WELCOME)

        # States 2 (Happy) & 3 (Unhappy):
        # On timer_timeout, guarded transition:
        # If stats.belowThreshold() (< 30%) -> State 4 (Alarm)
        # If !stats.belowThreshold() (>= 30%) -> State 0 (Welcome)
        # These guards are resolved dynamically in stateEvent()

        # State 4 (Alarm):
        # manager_press (blue button silences buzzer, keeps ratings) -> State 5 (Alarm Silenced)
        # timer_timeout -> State 5 (Alarm Silenced)
        # green_press (resets stats) -> State 0 (Welcome)
        self.stateModel.addTransition(self.STATE_ALARM, ["manager_press", "timer_timeout"], self.STATE_ALARM_SILENCED)
        self.stateModel.addTransition(self.STATE_ALARM, ["green_press"], self.STATE_WELCOME)

        # State 5 (Alarm Silenced):
        # green_press (resets stats) -> State 0 (Welcome)
        self.stateModel.addTransition(self.STATE_ALARM_SILENCED, ["green_press"], self.STATE_WELCOME)

        Log.i("FeedbackController: Configured 6 states and transitions successfully.")

    # -------------------------------------------------------------------------
    # StateModel Handler Callbacks: stateEntered, stateLeft, stateEvent, stateDo
    # -------------------------------------------------------------------------

    def stateEntered(self, state: int, event: str) -> None:
        """Execute entry actions when entering a state."""
        Log.d(f"FeedbackController: stateEntered -> State {state} on event '{event}'")

        if state == self.STATE_WELCOME:
            # 0 - Welcome: entry / showWelcome
            self.view.showWelcome()

        elif state == self.STATE_SELECTION:
            # 1 - Selection: entry / showPrompt
            self.view.showPrompt()
            # Start a 10-second timer to wait for customer rating
            self.timer.start(10)

        elif state == self.STATE_HAPPY:
            # 2 - Happy: entry / recordPositiveFeedback
            self.greenPressed()
            # Display results for 3 seconds before evaluating next state
            self.timer.start(3)

        elif state == self.STATE_UNHAPPY:
            # 3 - Unhappy: entry / recordNegativeFeedback
            self.redPressed()
            # Display results for 3 seconds before evaluating next state
            self.timer.start(3)

        elif state == self.STATE_ALARM:
            # 4 - Alarm: entry / activateManagerAlert
            self.alert.start()
            self.view.showAlarm()
            # Alarm sounds for 10 seconds before automatically moving to silenced
            self.timer.start(10)

        elif state == self.STATE_ALARM_SILENCED:
            # 5 - Alarm Silenced: entry / silenceManagerAlert (keeps ratings intact)
            self.alert.silence()
            self.view.showSilenced()

    def stateLeft(self, state: int, event: str) -> None:
        """Execute exit actions when leaving a state."""
        Log.d(f"FeedbackController: stateLeft <- State {state} on event '{event}'")

        # Cancel active timer when exiting timed states
        if state in (self.STATE_SELECTION, self.STATE_HAPPY, self.STATE_UNHAPPY, self.STATE_ALARM):
            self.timer.cancel()

        # In States 4 (Alarm) and 5 (Alarm Silenced), pressing green resets the statistics
        if state in (self.STATE_ALARM, self.STATE_ALARM_SILENCED) and event == "green_press":
            self.resetPressed()

    def stateEvent(self, state: int, event: str) -> bool:
        """
        Handle events that require guard conditions or in-state processing.
        Returns True if the event was handled.
        """
        # Handle guarded timeout transitions for Happy (2) and Unhappy (3)
        if state in (self.STATE_HAPPY, self.STATE_UNHAPPY) and event == "timer_timeout":
            if self.stats.belowThreshold():
                Log.w(f"FeedbackController: Satisfaction ({self.stats.getSatisfaction():.1f}%) below 30% threshold -> Alarm!")
                self.stateModel.gotoState(self.STATE_ALARM, event)
            else:
                Log.i(f"FeedbackController: Satisfaction ({self.stats.getSatisfaction():.1f}%) OK -> Welcome")
                self.stateModel.gotoState(self.STATE_WELCOME, event)
            return True

        return False

    def stateDo(self, state: int) -> None:
        """Perform continuous / in-state background activities."""
        # Flash the LED ring red during active alarm
        if state == self.STATE_ALARM:
            self.view.flashAlarm()

    # -------------------------------------------------------------------------
    # Public Controller Methods (from UML Class Diagram)
    # -------------------------------------------------------------------------

    def greenPressed(self) -> None:
        """Handle positive rating action."""
        self.stats.recordPositive()
        self.view.showResult(good=True, percent=self.stats.getSatisfaction())

    def redPressed(self) -> None:
        """Handle negative rating action."""
        self.stats.recordNegative()
        self.view.showResult(good=False, percent=self.stats.getSatisfaction())

    def managerPressed(self) -> None:
        """Handle manager button press to silence an active alarm without clearing ratings."""
        self.alert.silence()
        self.view.showSilenced()

    def resetPressed(self) -> None:
        """Reset stats and clear alerts back to normal."""
        self.alert.clear()
        self.stats.reset()
        Log.i("FeedbackController: System reset via green button.")

    def update(self) -> None:
        """Alias to drive state model execution."""
        self.run()

    def run(self) -> None:
        """Start and run the StateModel main event loop."""
        Log.i("FeedbackController: Starting QuickRate Kiosk State Model loop...")
        self.stateModel.run(delay=0.1)
