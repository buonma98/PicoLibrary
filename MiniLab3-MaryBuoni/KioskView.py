"""
KioskView.py
View class coordinating visual output devices (LCD 1602 display and NeoPixel LightStrip)
Author: buonma98
"""

from Log import Log
from Lights import RED, GREEN, BLUE, YELLOW, WHITE, BLACK


class KioskView:
    """
    KioskView encapsulates the presentation layer for The Pit Stop satisfaction kiosk.
    It drives the two-line 1602 LCD and the 8-pixel NeoPixel LED ring.
    """

    def __init__(self, lcd, leds):
        """
        Initialize KioskView with output hardware instances.

        Parameters:
        -----------
        lcd : LCDDisplay
            The 1602 LCD display instance.
        leds : LightStrip
            The NeoPixel ring / light strip instance.
        """
        self._lcd = lcd
        self._leds = leds
        Log.i("KioskView initialized with LCD and LightStrip")

    @property
    def lcd(self):
        """Return the LCD display instance."""
        return self._lcd

    @property
    def leds(self):
        """Return the LightStrip instance."""
        return self._leds

    def _write_lcd(self, line1: str, line2: str = "") -> None:
        """Helper to format and render two 16-character lines on the LCD."""
        if not self._lcd:
            return
        # Pad or truncate strings to exactly 16 characters
        l1 = f"{line1[:16]:<16}"
        l2 = f"{line2[:16]:<16}"
        
        # Displays.py uses showText(text, row, col)
        if hasattr(self._lcd, 'showText'):
            self._lcd.showText(l1, 0, 0)
            self._lcd.showText(l2, 1, 0)
        elif hasattr(self._lcd, 'display'):
            self._lcd.display(f"{l1}\n{l2}")

    def showWelcome(self) -> None:
        """Display the idle welcome screen on LCD and calm blue light on LEDs."""
        self._write_lcd("  The Pit Stop  ", "Step Up to Rate ")
        if self._leds:
            self._leds.setColor(BLUE)
        Log.i("KioskView: Showing Welcome screen")

    def showPrompt(self) -> None:
        """Display the rating prompt on LCD and illuminate LEDs for customer input."""
        self._write_lcd("Rate Your Visit ", "Grn=Good Red=Bad")
        if self._leds:
            self._leds.setColor(WHITE)
        Log.i("KioskView: Showing Rating Prompt")

    def showResult(self, good: bool, percent: float) -> None:
        """
        Display feedback confirmation and updated satisfaction score.

        Parameters:
        -----------
        good : bool
            True if positive feedback was given, False if negative.
        percent : float
            Current overall satisfaction percentage.
        """
        if good:
            self._write_lcd(" Thank You! :D  ", f"Score: {percent:.0f}%")
            if self._leds:
                self._leds.setColor(GREEN)
        else:
            self._write_lcd("We're Sorry! :( ", f"Score: {percent:.0f}%")
            if self._leds:
                self._leds.setColor(RED)
        Log.i(f"KioskView: Showing Result (good={good}, score={percent:.1f}%)")

    def showMood(self, percent: float) -> None:
        """
        Reflect current satisfaction mood on the LED ring:
        - 75% - 100%: Green
        - 50% - 74%: Yellow
        - < 50%: Red
        """
        if not self._leds:
            return
        if percent >= 75.0:
            self._leds.setColor(GREEN)
        elif percent >= 50.0:
            self._leds.setColor(YELLOW)
        else:
            self._leds.setColor(RED)

    def showAlarm(self) -> None:
        """Display manager alert warning on LCD and flashing/solid red on LEDs."""
        self._write_lcd(" MANAGER ALERT! ", "Low Satisfaction")
        if self._leds:
            self._leds.setColor(RED)
        Log.w("KioskView: Showing Manager Alert screen")

    def showSilenced(self) -> None:
        """Display alert silenced screen with instructions to reset."""
        self._write_lcd(" Alert Silenced ", "Grn=Reset Kiosk ")
        if self._leds:
            self._leds.setColor(YELLOW)
        Log.i("KioskView: Showing Alert Silenced screen")
