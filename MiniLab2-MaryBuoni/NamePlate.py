"""
# NamePlate.py
# Controller class for the digital office NamePlate application on Raspberry Pi Pico
# Author: buonma98
"""

import time
from Log import *
from Employee import Employee, Administrator, Faculty, Staff, StudentWorker, Calendar
from NamePlateView import NamePlateView

# Safe top-level import of micropython module for ISR scheduling on RP2040
try:
    import micropython
    # Pre-allocate emergency exception buffer so MicroPython can safely print exceptions from ISRs
    micropython.alloc_emergency_exception_buf(100)
except (ImportError, AttributeError):
    micropython = None


class NamePlate:
    """
    **NamePlate** acts as the controller for the dynamic office nameplate application.

    It coordinates user inputs from three physical pushbuttons and directs the
    presentation layer (`NamePlateView`) to update the 1602 LCD, NeoPixel light strip,
    and passive buzzer:
    - **previousButton**: Scrolls backward to the previous employee in the roster (wraps around).
    - **nextButton**: Scrolls forward to the next employee in the roster (wraps around).
    - **availabilityButton**: Cycles availability (*Available* -> *Away* -> *Busy* -> *Available*)
      for non-administrators. For `Administrator`, manual availability cycling is prevented because
      availability is automatically driven by the `Calendar`.

    Parameters:
    ----------
    view : NamePlateView
        The view instance managing LCD display, light strip, and buzzer.
    previousButton : Button, optional
        Button instance used to navigate backward (default: None).
    nextButton : Button, optional
        Button instance used to navigate forward (default: None).
    availabilityButton : Button, optional
        Button instance used to cycle availability (default: None).
    employees : list of Employee, optional
        Initial list of employees to populate the roster (default: None).

    Examples:
    ---------
    1. Instantiating and using NamePlate with hardware components:
       ```python
       from Displays import LCDDisplay
       from LightStrip import LightStrip
       from Buzzer import PassiveBuzzer
       from Button import Button
       from Employee import Faculty, Administrator, Calendar
       from NamePlateView import NamePlateView
       from NamePlate import NamePlate

       # Initialize hardware
       lcd = LCDDisplay(sda=0, scl=1)
       strip = LightStrip(pin=2, numleds=8)
       buzzer = PassiveBuzzer(pin=16)
       btn_prev = Button(pin=13, name="btn_prev")
       btn_next = Button(pin=14, name="btn_next")
       btn_avail = Button(pin=15, name="btn_avail")

       # Create view and controller
       view = NamePlateView(lcd=lcd, lightStrip=strip, buzzer=buzzer)
       roster = [
           Faculty("Dr. Mark Miller", courses=["COP4338"], officeHours="MWF 10-12"),
           Administrator("Dean Garcia", calendar=Calendar())
       ]
       controller = NamePlate(view=view, previousButton=btn_prev, nextButton=btn_next,
                              availabilityButton=btn_avail, employees=roster)
       ```
    """

    def __init__(self, view, previousButton=None, nextButton=None, availabilityButton=None, employees=None):
        """
        Initialize the NamePlate controller.

        Parameters:
        ----------
        view : NamePlateView
            View instance managing output peripherals.
        previousButton : Button, optional
            Navigation button for previous employee.
        nextButton : Button, optional
            Navigation button for next employee.
        availabilityButton : Button, optional
            Navigation button for availability toggling.
        employees : list of Employee, optional
            Initial roster list.
        """
        Log.i("NamePlate: Initializing controller...")
        self.view = view
        self.previousButton = previousButton
        self.nextButton = nextButton
        self.availabilityButton = availabilityButton

        self.employees = list(employees) if employees is not None else []
        self.currentIndex = 0
        self._pending_button = None

        # Bind button handlers
        self.handleButtons()

        # Render initial employee if roster is populated
        if self.employees:
            self.updateDisplay()

    def handleButtons(self):
        """
        Register self as the interrupt callback handler for all three buttons.
        """
        Log.i("NamePlate: Configuring button event handlers...")
        for btn in (self.previousButton, self.nextButton, self.availabilityButton):
            if btn is not None and hasattr(btn, 'setHandler'):
                btn.setHandler(self)

    def getCurrentEmployee(self):
        """
        Return the employee currently selected for display.

        Returns:
        -------
        Employee or None
            The currently active Employee object, or None if the roster is empty.
        """
        if not self.employees:
            return None
        return self.employees[self.currentIndex]

    def previousEmployee(self):
        """
        Navigate to the previous employee in the roster (wraps around).
        """
        if not self.employees:
            Log.w("NamePlate: previousEmployee called but roster is empty")
            return

        self.currentIndex = (self.currentIndex - 1) % len(self.employees)
        emp = self.getCurrentEmployee()
        Log.i(f"NamePlate: Switched to previous employee [{self.currentIndex}]: {emp.name}")

        if self.view is not None:
            self.view.playChangeSound()
        self.updateDisplay()

    def nextEmployee(self):
        """
        Navigate to the next employee in the roster (wraps around).
        """
        if not self.employees:
            Log.w("NamePlate: nextEmployee called but roster is empty")
            return

        self.currentIndex = (self.currentIndex + 1) % len(self.employees)
        emp = self.getCurrentEmployee()
        Log.i(f"NamePlate: Switched to next employee [{self.currentIndex}]: {emp.name}")

        if self.view is not None:
            self.view.playChangeSound()
        self.updateDisplay()

    def changeAvailability(self):
        """
        Cycle availability for the active employee.

        For Administrators, manual availability changes are blocked because availability
        is determined automatically by their Calendar.
        """
        emp = self.getCurrentEmployee()
        if emp is None:
            Log.w("NamePlate: changeAvailability called but no employee selected")
            return

        # Prevent manual availability changes for Administrators
        if isinstance(emp, Administrator):
            Log.i(f"NamePlate: {emp.name} is an Administrator. Availability is managed automatically by Calendar.")
            return

        # Cycle availability for non-administrators
        emp.cycleAvailability()
        Log.i(f"NamePlate: Cycled {emp.name}'s availability to '{emp.getAvailability()}'")

        if self.view is not None:
            self.view.playChangeSound()
        self.updateDisplay()

    def updateDisplay(self):
        """
        Render current employee details and availability onto the view.
        """
        if self.view is None:
            return

        emp = self.getCurrentEmployee()
        self.view.showEmployee(emp)
        status = emp.getAvailability() if emp is not None else "Available"
        self.view.showAvailability(status)

    def buttonPressed(self, name):
        """
        Callback triggered by Button.py when any button is pressed.

        To guarantee complete hardware safety on the Raspberry Pi Pico, this method
        does NOT perform module imports, string formatting, logging, I2C writes, or
        sleep calls inside the interrupt context. Instead, it defers execution to the
        main thread via micropython.schedule.

        Parameters:
        ----------
        name : str
            Identifier string of the button pressed.
        """
        if micropython is not None:
            try:
                micropython.schedule(self._on_button_event, name)
                return
            except RuntimeError:
                # Scheduler queue is full under rapid presses; buffer event
                self._pending_button = name
                return

        # Fallback for desktop Python / non-MicroPython testing environments
        self._on_button_event(name)

    def buttonReleased(self, name):
        """
        Callback triggered by Button.py when any button is released.

        Parameters:
        ----------
        name : str
            Identifier string of the button released.
        """
        pass

    def _on_button_event(self, name):
        """
        Internal dispatcher executed on the main thread outside of interrupt context.

        Performs logging, LCD updates, buzzer sounds, and availability changes safely.
        """
        Log.i(f"NamePlate: Button event dispatched -> '{name}'")

        prev_name = getattr(self.previousButton, '_name', None)
        next_name = getattr(self.nextButton, '_name', None)
        avail_name = getattr(self.availabilityButton, '_name', None)

        if name == prev_name or name in ("btn_prev", "prev"):
            self.previousEmployee()
        elif name == next_name or name in ("btn_next", "next"):
            self.nextEmployee()
        elif name == avail_name or name in ("btn_avail", "btn_status", "avail", "status"):
            self.changeAvailability()
        else:
            Log.w(f"NamePlate: Unrecognized button name '{name}'")


if __name__ == "__main__":
    Log.i("Starting self-contained verification for NamePlate controller...")

    # Mock View for testing
    class MockView:
        def __init__(self):
            self.last_employee = None
            self.last_status = None
            self.sound_played_count = 0

        def showEmployee(self, employee):
            self.last_employee = employee

        def showAvailability(self, status):
            self.last_status = status

        def playChangeSound(self):
            self.sound_played_count += 1

    # Mock Button for testing
    class MockButton:
        def __init__(self, name):
            self._name = name
            self.handler = None
            self.is_down = False

        def setHandler(self, handler):
            self.handler = handler

        def press(self):
            self.is_down = True
            if self.handler:
                self.handler.buttonPressed(self._name)

        def release(self):
            self.is_down = False
            if self.handler:
                self.handler.buttonReleased(self._name)

    # Instantiate mock peripherals
    view = MockView()
    btn_prev = MockButton("btn_prev")
    btn_next = MockButton("btn_next")
    btn_avail = MockButton("btn_avail")

    # Create test roster
    cal = Calendar(events=["Dean Meeting"])
    admin = Administrator("Dean Garcia", calendar=cal)
    prof = Faculty("Dr. Mark Miller", courses=["COP4338"], officeHours="MWF 10-12")
    staff = Staff("Sarah Connor", department="IT Support")
    student = StudentWorker("Emily Clark")

    roster = [admin, prof, staff, student]

    # Instantiate controller
    controller = NamePlate(view=view, previousButton=btn_prev, nextButton=btn_next,
                           availabilityButton=btn_avail, employees=roster)

    # 1. Verify button handlers attached
    assert btn_prev.handler is controller, "btn_prev handler not attached"
    assert btn_next.handler is controller, "btn_next handler not attached"
    assert btn_avail.handler is controller, "btn_avail handler not attached"

    # 2. Verify initial display state (First employee is Dean Garcia - Busy from calendar)
    assert controller.getCurrentEmployee() is admin
    assert view.last_employee is admin
    assert view.last_status == "Busy"

    # 3. Test nextEmployee via Button press (Index 0 -> Index 1: Dr. Mark Miller)
    btn_next.press()
    btn_next.release()
    assert controller.getCurrentEmployee() is prof
    assert view.last_employee is prof
    assert view.last_status == "Available"
    assert view.sound_played_count == 1, "Sound should play on nextEmployee"

    # 4. Test changeAvailability on non-administrator (Faculty: Available -> Away)
    btn_avail.press()
    btn_avail.release()
    assert prof.getAvailability() == "Away"
    assert view.last_status == "Away"
    assert view.sound_played_count == 2, "Sound should play on changeAvailability"

    # 5. Test previousEmployee via Button press (Index 1 -> Index 0: Dean Garcia)
    btn_prev.press()
    btn_prev.release()
    assert controller.getCurrentEmployee() is admin
    assert view.last_employee is admin
    assert view.last_status == "Busy"
    assert view.sound_played_count == 3

    # 6. Test Administrator availability guard (Button press MUST NOT change status)
    initial_sound_count = view.sound_played_count
    btn_avail.press()
    btn_avail.release()
    assert admin.getAvailability() == "Busy", "Administrator availability must remain Busy from Calendar"
    assert view.last_status == "Busy"
    assert view.sound_played_count == initial_sound_count, "No sound should play when change is blocked"

    # 7. Test backward circular wrap-around (Index 0 -> Index 3: StudentWorker)
    btn_prev.press()
    btn_prev.release()
    assert controller.getCurrentEmployee() is student
    assert view.last_employee is student

    # 8. Test forward circular wrap-around (Index 3 -> Index 0: Dean Garcia)
    btn_next.press()
    btn_next.release()
    assert controller.getCurrentEmployee() is admin

    Log.i("Testing complete - all checks passed for NamePlate controller")
