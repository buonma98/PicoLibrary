"""
# MysteryGadget.py
# A class that simulates an engine dashboard combining an LCD display, buzzer, NeoPixel light strip, and potentiometer
# Author: insert your name here
"""

import time
from Log import *

class MysteryGadget:
    """
    **MysteryGadget** simulates an interactive automotive engine dashboard.

    It integrates four hardware components:
    - An LCD display (e.g., `LCDDisplay`) to show engine status, RPM, and speed.
    - A buzzer (e.g., `PassiveBuzzer`) to synthesize engine rumble and rev sounds.
    - A NeoPixel light strip (e.g., `LightStrip`) to serve as a visual tachometer / rev-meter.
    - A potentiometer (e.g., `AnalogSensor`) to throttle and adjust engine RPM.

    Parameters:
    ----------
    display : LCDDisplay or Display
        The LCD display instance used to render RPM, speed, and status messages.
    buzzer : PassiveBuzzer or Buzzer
        The buzzer instance used to generate starting rumble and revving audio tones.
    light_strip : LightStrip
        The NeoPixel light strip instance used to display visual RPM levels.
    potentiometer : AnalogSensor or machine.ADC
        The potentiometer instance providing raw analog input (0-65535) for throttle control.
    min_rpm : int, optional
        Idle engine RPM (default: 800).
    max_rpm : int, optional
        Maximum redline engine RPM (default: 8000).
    max_speed : int, optional
        Maximum simulated vehicle speed in mph (default: 140).

    Examples:
    ---------
    1. Basic Engine Simulation:
       ```python
       from Displays import LCDDisplay
       from Buzzer import PassiveBuzzer
       from LightStrip import LightStrip
       from Sensors import AnalogSensor
       from MysteryGadget import MysteryGadget

       lcd = LCDDisplay(sda=0, scl=1)
       buzzer = PassiveBuzzer(pin=15)
       strip = LightStrip(pin=2, numleds=8)
       pot = AnalogSensor(pin=26)

       gadget = MysteryGadget(lcd, buzzer, strip, pot)
       gadget.start()
       gadget.control(duration=5.0)  # Monitor and throttle for 5 seconds
       gadget.stop()
       ```

    2. Continuous Loop in an Application:
       ```python
       gadget = MysteryGadget(lcd, buzzer, strip, pot)
       gadget.start()
       try:
           while True:
               gadget.control()  # Single monitoring update step
               time.sleep(0.05)
       except KeyboardInterrupt:
           gadget.stop()
       ```
    """

    COLOR_OFF = (0, 0, 0)
    COLOR_LOW = (0, 255, 0)     # Green: Safe RPM range
    COLOR_MID = (255, 200, 0)   # Yellow/Orange: High RPM range
    COLOR_HIGH = (255, 0, 0)    # Red: Redline range

    def __init__(self, display, buzzer, light_strip, potentiometer, min_rpm=800, max_rpm=8000, max_speed=140):
        """
        Initialize the MysteryGadget with connected hardware components.

        Parameters:
        ----------
        display : Display
            LCD display for metrics and status.
        buzzer : Buzzer
            Buzzer for sound output.
        light_strip : LightStrip
            NeoPixel LED strip for tachometer visualization.
        potentiometer : AnalogSensor or ADC
            Analog sensor for throttle control.
        min_rpm : int, optional
            Idle RPM value (default: 800).
        max_rpm : int, optional
            Redline RPM value (default: 8000).
        max_speed : int, optional
            Top speed in mph (default: 140).
        """
        Log.i("MysteryGadget: Initializing engine dashboard components")
        self._display = display
        self._buzzer = buzzer
        self._light_strip = light_strip
        self._potentiometer = potentiometer

        self._min_rpm = min_rpm
        self._max_rpm = max_rpm
        self._max_speed = max_speed

        self._running = False
        self._current_rpm = 0
        self._current_speed = 0

    def start(self):
        """
        Simulate starting of the engine.

        Produces a low-frequency rumble sound on the buzzer, initializes the
        display with idle RPM and zero speed, and marks the engine as running.

        Examples:
        ---------
        1. Starting the gadget:
           ```python
           gadget.start()
           ```
        """
        Log.i("MysteryGadget: Starting engine...")
        self._running = True
        self._current_rpm = self._min_rpm
        self._current_speed = 0

        # Simulate engine starter cranking and low-frequency idle rumble (60 Hz)
        if hasattr(self._buzzer, 'play'):
            Log.i("MysteryGadget: Playing starter rumble (60 Hz)")
            self._buzzer.play(60)

        # Show initial simulated speed and RPM on the display
        if hasattr(self._display, 'clear'):
            self._display.clear()
        if hasattr(self._display, 'showText'):
            self._display.showText(f"RPM: {self._current_rpm:<5}", row=0, col=0)
            self._display.showText(f"Speed: {self._current_speed:<3} mph", row=1, col=0)

        # Initialize light strip with base idle indication (first LED green)
        self._update_light_strip(0.0)

        Log.i(f"MysteryGadget: Engine started at idle ({self._current_rpm} RPM, {self._current_speed} mph)")

    def stop(self):
        """
        Stop the engine, display 'ENGINE STOPPED', and stop any sound.

        Turns off the buzzer and light strip, resets running metrics, and
        updates the LCD display screen.

        Examples:
        ---------
        1. Stopping the gadget:
           ```python
           gadget.stop()
           ```
        """
        Log.i("MysteryGadget: Stopping engine...")
        self._running = False
        self._current_rpm = 0
        self._current_speed = 0

        # Silence the buzzer
        if hasattr(self._buzzer, 'stop'):
            self._buzzer.stop()

        # Turn off the tachometer light strip
        if hasattr(self._light_strip, 'off'):
            self._light_strip.off()

        # Update the display to show ENGINE STOPPED
        if hasattr(self._display, 'clear'):
            self._display.clear()
        if hasattr(self._display, 'showText'):
            self._display.showText("ENGINE STOPPED", row=0, col=0)
            self._display.showText("                ", row=1, col=0)

        Log.i("MysteryGadget: Engine stopped successfully")

    def control(self, duration=None, iterations=1, delay=0.05):
        """
        Monitor the potentiometer and simulate dynamic engine response.

        Reads the raw potentiometer value to adjust engine RPM and vehicle speed,
        visualizes current RPM on the NeoPixel light strip tachometer, updates
        the LCD display with current figures, and shifts buzzer frequency to match RPM.

        Parameters:
        ----------
        duration : float, optional
            Number of seconds to monitor continuously before returning (default: None).
        iterations : int, optional
            Number of monitoring cycles to execute. Pass 1 for a single step,
            or None to run indefinitely while running (default: 1).
        delay : float, optional
            Delay in seconds between monitoring cycles (default: 0.05).

        Examples:
        ---------
        1. Perform a single update cycle:
           ```python
           gadget.control()
           ```
        2. Monitor and adjust engine for 3 seconds:
           ```python
           gadget.control(duration=3.0)
           ```
        3. Execute 50 control updates:
           ```python
           gadget.control(iterations=50, delay=0.02)
           ```
        """
        if not self._running:
            Log.w("MysteryGadget: Cannot control - engine is not running. Call start() first.")
            return

        start_time = time.time()
        cycles = 0

        while self._running:
            self._update_engine_step()
            cycles += 1

            if iterations is not None and cycles >= iterations:
                break
            if duration is not None and (time.time() - start_time) >= duration:
                break

            time.sleep(delay)

    def _read_potentiometer(self):
        """
        Helper method to retrieve the raw analog value from the potentiometer.

        Supports instances of `AnalogSensor`, `machine.ADC`, or callable mocks.
        Returns an integer in the range 0 to 65535.
        """
        if hasattr(self._potentiometer, 'rawValue'):
            return self._potentiometer.rawValue()
        elif hasattr(self._potentiometer, 'read_u16'):
            return self._potentiometer.read_u16()
        elif callable(self._potentiometer):
            return self._potentiometer()
        elif hasattr(self._potentiometer, 'value'):
            v = self._potentiometer.value()
            return int(v * 65535) if v <= 1 else int(v)
        return 0

    def _update_engine_step(self):
        """
        Execute a single monitoring update step based on potentiometer input.
        """
        raw_val = self._read_potentiometer()
        # Constrain raw value to 16-bit range (0 - 65535) and compute ratio
        raw_val = max(0, min(65535, raw_val))
        ratio = raw_val / 65535.0

        # Calculate simulated RPM and speed
        self._current_rpm = int(self._min_rpm + ratio * (self._max_rpm - self._min_rpm))
        self._current_speed = int(ratio * self._max_speed)

        # Update LCD display with current RPM and speed
        if hasattr(self._display, 'showText'):
            self._display.showText(f"RPM: {self._current_rpm:<5}", row=0, col=0)
            self._display.showText(f"Speed: {self._current_speed:<3} mph", row=1, col=0)

        # Visualize RPM on the NeoPixel light strip
        self._update_light_strip(ratio)

        # Adjust engine acoustic frequency with RPM (50 Hz idle up to 250 Hz rev)
        engine_freq = int(50 + ratio * 200)
        if hasattr(self._buzzer, 'play'):
            self._buzzer.play(engine_freq)

        Log.i(f"MysteryGadget: Throttle={ratio:.2f} -> RPM={self._current_rpm}, Speed={self._current_speed} mph, Freq={engine_freq} Hz")

    def _update_light_strip(self, ratio):
        """
        Visualize current RPM ratio as a tachometer bar on the light strip.

        Parameters:
        ----------
        ratio : float
            Fraction of throttle / RPM from 0.0 (idle) to 1.0 (max redline).
        """
        if not hasattr(self._light_strip, 'setPixel'):
            return

        num_leds = getattr(self._light_strip, '_numleds', 8)
        lit_count = int(round(ratio * num_leds))

        for i in range(num_leds):
            if i < lit_count:
                # Color staging: Green -> Yellow -> Red
                if i < int(num_leds * 0.5):
                    color = self.COLOR_LOW
                elif i < int(num_leds * 0.8):
                    color = self.COLOR_MID
                else:
                    color = self.COLOR_HIGH
            else:
                color = self.COLOR_OFF

            self._light_strip.setPixel(i, color, show=False)

        if hasattr(self._light_strip, 'show'):
            self._light_strip.show()


if __name__ == "__main__":
    # Self-contained verification and testing using mock hardware components
    Log.i("MysteryGadget: Starting self-contained verification tests")

    class MockDisplay:
        def __init__(self):
            self.lines = ["", ""]
        def clear(self, line=-1):
            if line < 0:
                self.lines = ["", ""]
            else:
                self.lines[line] = ""
            Log.i("MockDisplay: Cleared")
        def showText(self, text, row=0, col=0):
            self.lines[row] = text
            Log.i(f"MockDisplay [Row {row}]: '{text}'")

    class MockBuzzer:
        def __init__(self):
            self.frequency = 0
            self.is_playing = False
        def play(self, tone=500):
            self.frequency = tone
            self.is_playing = True
            Log.i(f"MockBuzzer: Playing tone {tone} Hz")
        def stop(self):
            self.is_playing = False
            Log.i("MockBuzzer: Stopped")

    class MockLightStrip:
        def __init__(self, numleds=8):
            self._numleds = numleds
            self.pixels = [(0, 0, 0)] * numleds
        def setPixel(self, pixelno, color, show=True):
            if 0 <= pixelno < self._numleds:
                self.pixels[pixelno] = color
        def show(self):
            Log.i(f"MockLightStrip: Updated pixels: {self.pixels}")
        def off(self):
            self.pixels = [(0, 0, 0)] * self._numleds
            Log.i("MockLightStrip: Turned off all pixels")

    class MockPotentiometer:
        def __init__(self, initial_value=0):
            self.value = initial_value
        def rawValue(self):
            return self.value

    # Instantiate mock hardware
    display = MockDisplay()
    buzzer = MockBuzzer()
    strip = MockLightStrip(numleds=8)
    pot = MockPotentiometer(initial_value=0)

    # 1. Instantiate MysteryGadget
    gadget = MysteryGadget(display=display, buzzer=buzzer, light_strip=strip, potentiometer=pot)
    assert not gadget._running, "Engine should initially be stopped"

    # 2. Test start() method
    gadget.start()
    assert gadget._running, "Engine should be running after start()"
    assert buzzer.is_playing, "Buzzer should be playing low-frequency rumble"
    assert buzzer.frequency == 60, f"Expected 60 Hz tone, got {buzzer.frequency}"
    assert "RPM: 800" in display.lines[0], f"Display row 0 should show idle RPM, got {display.lines[0]}"
    assert "Speed: 0" in display.lines[1], f"Display row 1 should show 0 speed, got {display.lines[1]}"

    # 3. Test control() method with throttle increase (50% throttle -> 32768)
    pot.value = 32768
    gadget.control(iterations=1)
    assert 4300 <= gadget._current_rpm <= 4500, f"Expected mid RPM (~4400), got {gadget._current_rpm}"
    assert 65 <= gadget._current_speed <= 75, f"Expected mid speed (~70 mph), got {gadget._current_speed}"
    assert buzzer.frequency > 60, "Buzzer frequency should increase with RPM"

    # 4. Test control() method with max throttle (100% throttle -> 65535)
    pot.value = 65535
    gadget.control(iterations=1)
    assert gadget._current_rpm == 8000, f"Expected max RPM 8000, got {gadget._current_rpm}"
    assert gadget._current_speed == 140, f"Expected top speed 140 mph, got {gadget._current_speed}"
    # Tachometer should have all 8 pixels lit at 100%
    assert all(color != (0, 0, 0) for color in strip.pixels), "All pixels should be lit at redline"

    # 5. Test control() method with min throttle (0% throttle -> 0)
    pot.value = 0
    gadget.control(iterations=1)
    assert gadget._current_rpm == 800, f"Expected idle RPM 800, got {gadget._current_rpm}"
    assert gadget._current_speed == 0, f"Expected 0 mph speed, got {gadget._current_speed}"

    # 6. Test stop() method
    gadget.stop()
    assert not gadget._running, "Engine should be stopped after stop()"
    assert not buzzer.is_playing, "Buzzer should be silent after stop()"
    assert display.lines[0] == "ENGINE STOPPED", f"Display should show 'ENGINE STOPPED', got {display.lines[0]}"
    assert all(color == (0, 0, 0) for color in strip.pixels), "LightStrip should be turned off after stop()"

    Log.i("Testing complete - all checks passed")
