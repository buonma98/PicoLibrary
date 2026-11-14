"""
KioskView.py
View class coordinating visual output devices (LCD 1602 display and NeoPixel LightStrip)
Author: buonma98
"""

import time
from Log import Log
from Lights import RED, GREEN, BLUE, YELLOW, WHITE, BLACK


class KioskView:
    """
    KioskView encapsulates the presentation layer for the QuickRate kiosk.
    It drives the two-line 1602 LCD and the 8-pixel NeoPixel LED ring.
    The LED ring acts as a live satisfaction meter:
      - Each LED represents 12.5% satisfaction
      - >= 75%: Green LEDs (e.g., 100% = 8 green, 75% = 6 green)
      - 50% - 74%: Yellow LEDs (e.g., 50% = 4 yellow)
      - < 50%: Red LEDs (e.g., 25% = 2 red)
      - Remaining LEDs are off
    All LCD lines are strictly formatted to 16 characters max.
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
        self._alarm_flash_state: bool = False
        self._last_flash_time: int = 0
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

    def showWelcome(self, has_votes: bool = False, percent: float = 100.0) -> None:
        """
        Display the idle welcome screen on LCD.
        If nobody has voted yet, keep the blue welcome lights.
        If votes have been submitted, keep showing the current satisfaction meter.
        Line 1: Welcome!
        Line 2: Step closer
        """
        self._write_lcd("Welcome!", "Step closer")
        if self._leds:
            if has_votes:
                self.showMood(percent)
            else:
                self._leds.setColor(BLUE)
        Log.i(f"KioskView: Showing Welcome screen (has_votes={has_votes})")

    def showPrompt(self) -> None:
        """
        Display the rating prompt on LCD and illuminate LEDs for customer input.
        Line 1: How was your
        Line 2: experience?
        """
        self._write_lcd("How was your", "experience?")
        if self._leds:
            self._leds.setColor(WHITE)
        Log.i("KioskView: Showing Rating Prompt")

    def showResult(self, good: bool, percent: float) -> None:
        """
        Display feedback confirmation on LCD and update the live satisfaction meter on LEDs.

        Parameters:
        -----------
        good : bool
            True if positive feedback was given, False if negative.
        percent : float
            Current overall satisfaction percentage.
        """
        if good:
            # Line 1: Love to hear it!
            # Line 2: Thank you! XX%
            self._write_lcd("Love to hear it!", f"Thank you! {percent:.0f}%")
        else:
            # Line 1: We're sorry!
            # Line 2: Shortened from "Thanks for sharing" (18 chars) to fit 16 chars
            self._write_lcd("We're sorry!", f"Thanks! {percent:.0f}%")

        # Update the 8-LED ring as a live satisfaction meter
        self.showMood(percent)
        Log.i(f"KioskView: Showing Result (good={good}, score={percent:.1f}%)")

    def showMood(self, percent: float) -> None:
        """
        Display the 8-LED ring as a live satisfaction meter:
        Each LED represents 12.5% satisfaction.
        - >= 75%: Green LEDs (e.g., 100% = 8 green, 75% = 6 green)
        - 50% - 74%: Yellow LEDs (e.g., 50% = 4 yellow)
        - < 50%: Red LEDs (e.g., 25% = 2 red)
        Remaining LEDs are turned off.
        """
        if not self._leds:
            return

        # Calculate number of LEDs to light up (each LED = 12.5%)
        num_leds = int(round(percent / 12.5))
        num_leds = max(0, min(8, num_leds))

        # Determine color based on satisfaction tier
        if percent >= 75.0:
            color = GREEN
        elif percent >= 50.0:
            color = YELLOW
        else:
            color = RED

        self._leds.setColor(color, num_leds)
        Log.i(f"KioskView: Satisfaction meter set to {percent:.1f}% ({num_leds} LEDs, color={color})")

    def showAlarm(self) -> None:
        """
        Display manager alert warning on LCD and red on LEDs.
        Line 1: Low satisfaction
        Line 2: Manager needed
        """
        self._write_lcd("Low satisfaction", "Manager needed")
        if self._leds:
            self._leds.setColor(RED)
        self._alarm_flash_state = True
        self._last_flash_time = time.ticks_ms()
        Log.w("KioskView: Showing Manager Alert screen")

    def flashAlarm(self) -> None:
        """
        Toggle red LED ring on and off at a normal, steady speed (every 500 ms).
        Prevents flickering on every loop iteration.
        """
        if not self._leds:
            return
        now = time.ticks_ms()
        if time.ticks_diff(now, self._last_flash_time) >= 500:
            self._last_flash_time = now
            self._alarm_flash_state = not self._alarm_flash_state
            if self._alarm_flash_state:
                self._leds.setColor(RED)
            else:
                self._leds.setColor(BLACK)

    def showSilenced(self) -> None:
        """
        Display alert silenced screen with action needed instruction.
        Line 1: Alarm silenced
        Line 2: Action needed
        """
        self._write_lcd("Alarm silenced", "Action needed")
        if self._leds:
            self._leds.setColor(YELLOW)
        Log.i("KioskView: Showing Alert Silenced screen")
