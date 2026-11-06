"""
# NamePlateView.py
# View class managing output devices (LCD display, NeoPixel light strip, and buzzer) for the NamePlate system
# Author: buonma98
"""

import time
from Log import *
from Employee import Employee, STATUS_AVAILABLE, STATUS_AWAY, STATUS_BUSY

# Status RGB colors for NeoPixel LightStrip
COLOR_AVAILABLE = (0, 255, 0)      # Green
COLOR_AWAY = (255, 180, 0)         # Amber / Yellow
COLOR_BUSY = (255, 0, 0)           # Red
COLOR_OFF = (0, 0, 0)              # Off / Black


class NamePlateView:
    """
    **NamePlateView** encapsulates the presentation layer of the digital nameplate system.

    It coordinates all physical output peripherals:
    - **lcd** (`LCDDisplay`): Displays employee name on Line 1 and formatted status/info on Line 2.
    - **lightStrip** (`LightStrip`): Indicates occupant availability via Green, Amber, or Red LEDs.
    - **buzzer** (`PassiveBuzzer`): Emits a short audible feedback tone when switching employees.

    Parameters:
    ----------
    lcd : LCDDisplay or Display
        The LCD display instance used to render lines 1 and 2.
    lightStrip : LightStrip
        NeoPixel light strip for visual availability indication.
    buzzer : PassiveBuzzer or Buzzer
        Buzzer for audible feedback tones.

    Examples:
    ---------
    1. Instantiating and using NamePlateView with hardware instances:
       ```python
       from Displays import LCDDisplay
       from LightStrip import LightStrip
       from Buzzer import PassiveBuzzer
       from Employee import Staff

       lcd = LCDDisplay(sda=0, scl=1)
       strip = LightStrip(pin=2, numleds=8)
       buzzer = PassiveBuzzer(pin=16)

       view = NamePlateView(lcd=lcd, lightStrip=strip, buzzer=buzzer)
       staff = Staff("Sarah Connor", department="IT Support")

       view.showEmployee(staff)
       view.showAvailability("Available")
       view.playChangeSound()
       ```
    """

    def __init__(self, lcd, lightStrip, buzzer):
        """
        Initialize NamePlateView with connected output hardware components.

        Parameters:
        ----------
        lcd : LCDDisplay or Display
            LCD display instance.
        lightStrip : LightStrip
            NeoPixel LED strip instance.
        buzzer : PassiveBuzzer or Buzzer
            Buzzer instance.
        """
        self.lcd = lcd
        self.lightStrip = lightStrip
        self.buzzer = buzzer
        Log.i("NamePlateView: Initialized output components (LCD, LightStrip, Buzzer)")

    def showEmployee(self, employee):
        """
        Display employee name and information on the two-line 1602 LCD.

        Line 1 displays the employee name (padded or truncated to 16 characters).
        Line 2 displays the bracketed availability tag and custom display info.

        Parameters:
        ----------
        employee : Employee
            The Employee instance to render, or None if the roster is empty.
        """
        if self.lcd is None:
            return

        if employee is None:
            line1 = f"{'No Employee':<16}"
            line2 = f"{'':<16}"
        else:
            # Line 1: Employee Name
            line1 = f"{employee.name[:16]:<16}"

            # Line 2: [Status] Info (e.g. "[Avail] COP4338 MWF")
            status = employee.getAvailability()
            status_tag = f"[{status[:5]:<5}]"
            info = employee.getDisplayInfo()
            line2 = f"{status_tag} {info[:8]:<8}"[:16]
            line2 = f"{line2:<16}"

        Log.i(f"NamePlateView: LCD L1: '{line1}' | L2: '{line2}'")
        if hasattr(self.lcd, 'showText'):
            self.lcd.showText(line1, row=0, col=0)
            self.lcd.showText(line2, row=1, col=0)

    def showAvailability(self, status):
        """
        Update the NeoPixel light strip with the color corresponding to availability status.

        - 'Available' -> Green (0, 255, 0)
        - 'Away'      -> Amber/Yellow (255, 180, 0)
        - 'Busy'      -> Red (255, 0, 0)

        Parameters:
        ----------
        status : str
            Availability status string ('Available', 'Away', or 'Busy').
        """
        if self.lightStrip is None:
            return

        if status == STATUS_AVAILABLE:
            color = COLOR_AVAILABLE
        elif status == STATUS_AWAY:
            color = COLOR_AWAY
        elif status == STATUS_BUSY:
            color = COLOR_BUSY
        else:
            color = COLOR_OFF

        Log.i(f"NamePlateView: Setting LightStrip status '{status}' -> {color}")
        if hasattr(self.lightStrip, 'setColor'):
            self.lightStrip.setColor(color)

    def playChangeSound(self):
        """
        Play a short audible tone on the buzzer to signal employee or status changes.
        """
        if self.buzzer is None:
            return

        Log.i("NamePlateView: Playing change sound (1000 Hz, 40 ms)")
        try:
            if hasattr(self.buzzer, 'beep'):
                self.buzzer.beep(tone=1000, duration=40)
            elif hasattr(self.buzzer, 'play') and hasattr(self.buzzer, 'stop'):
                self.buzzer.play(1000)
                time.sleep(0.04)
                self.buzzer.stop()
        except Exception as e:
            Log.w(f"NamePlateView: Buzzer audio warning: {e}")


if __name__ == "__main__":
    Log.i("Starting self-contained verification for NamePlateView...")

    # Mock hardware components to test NamePlateView in software
    class MockDisplay:
        def __init__(self):
            self.lines = ["", ""]
        def showText(self, text, row=0, col=0):
            self.lines[row] = text

    class MockLightStrip:
        def __init__(self):
            self.current_color = (0, 0, 0)
        def setColor(self, color, numPixels=None):
            self.current_color = color

    class MockBuzzer:
        def __init__(self):
            self.last_tone = 0
            self.last_duration = 0
            self.is_playing = False
        def beep(self, tone=500, duration=150):
            self.last_tone = tone
            self.last_duration = duration
        def play(self, tone=500):
            self.last_tone = tone
            self.is_playing = True
        def stop(self):
            self.is_playing = False

    # Instantiate mock hardware
    display = MockDisplay()
    strip = MockLightStrip()
    buzzer = MockBuzzer()

    view = NamePlateView(lcd=display, lightStrip=strip, buzzer=buzzer)
    assert view.lcd is display
    assert view.lightStrip is strip
    assert view.buzzer is buzzer

    # 1. Test showEmployee with Faculty
    from Employee import Faculty, Staff, StudentWorker, Administrator, Calendar
    faculty = Faculty("Dr. Mark Miller", courses=["COP4338"], officeHours="MWF 10-12")
    view.showEmployee(faculty)

    assert len(display.lines[0]) == 16, f"Line 1 length must be 16, got {len(display.lines[0])}"
    assert len(display.lines[1]) == 16, f"Line 2 length must be 16, got {len(display.lines[1])}"
    assert "Dr. Mark Miller" in display.lines[0]
    assert "[Avail]" in display.lines[1]

    # 2. Test showEmployee with Staff
    staff = Staff("Sarah Connor", department="IT Support")
    staff.cycleAvailability()  # Away
    view.showEmployee(staff)
    assert "Sarah Connor" in display.lines[0]
    assert "[Away ]" in display.lines[1]

    # 3. Test showAvailability colors
    view.showAvailability(STATUS_AVAILABLE)
    assert strip.current_color == COLOR_AVAILABLE, "Expected green for Available"

    view.showAvailability(STATUS_AWAY)
    assert strip.current_color == COLOR_AWAY, "Expected amber for Away"

    view.showAvailability(STATUS_BUSY)
    assert strip.current_color == COLOR_BUSY, "Expected red for Busy"

    # 4. Test playChangeSound
    view.playChangeSound()
    assert buzzer.last_tone == 1000, f"Expected 1000 Hz tone, got {buzzer.last_tone}"
    assert buzzer.last_duration == 40, f"Expected 40 ms duration, got {buzzer.last_duration}"

    # 5. Test None employee edge case
    view.showEmployee(None)
    assert display.lines[0] == "No Employee     "
    assert display.lines[1] == "                "

    Log.i("Testing complete - all checks passed for NamePlateView")
