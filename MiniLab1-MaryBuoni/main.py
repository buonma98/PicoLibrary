"""
# main.py
# Main entrypoint script to run the MysteryGadget engine simulation on Raspberry Pi Pico
# Author: Mary Buoni
"""

import time
from Log import *
from Displays import LCDDisplay
from Buzzer import PassiveBuzzer
from LightStrip import LightStrip
from Sensors import AnalogSensor
from MysteryGadget import MysteryGadget

def main():
    Log.i("main: Initializing hardware components for MysteryGadget...")

    # Hardware pin mapping:
    # - LCD Display: I2C on GP0 (SDA) and GP1 (SCL)
    # - Passive Buzzer: GP16
    # - NeoPixel Light Strip: GP2 (8 LEDs, 50% brightness)
    # - Potentiometer: ADC0 (GP26)
    display = LCDDisplay(sda=0, scl=1)
    buzzer = PassiveBuzzer(pin=16, name="EngineBuzzer")
    light_strip = LightStrip(pin=2, name="TachometerStrip", numleds=8, brightness=0.5)
    potentiometer = AnalogSensor(pin=26, name="ThrottlePotentiometer")

    # Create an instance of MysteryGadget
    gadget = MysteryGadget(
        display=display,
        buzzer=buzzer,
        light_strip=light_strip,
        potentiometer=potentiometer
    )

    try:
        # 1. Start the mystery gadget (initiates low-frequency rumble & displays idle values)
        Log.i("main: Starting MysteryGadget...")
        gadget.start()

        # 2. Control it for about 10 seconds (monitors throttle, adjusts RPM/speed, tachometer & audio)
        Log.i("main: Controlling MysteryGadget for 10 seconds...")
        gadget.control(duration=10.0, iterations=None, delay=0.05)


    except KeyboardInterrupt:
        Log.w("main: Execution interrupted by user")

    finally:
        # 3. Stop the mystery gadget (silences buzzer, shuts off light strip, shows ENGINE STOPPED)
        Log.i("main: Stopping MysteryGadget...")
        gadget.stop()

    Log.i("main: Program completed successfully")

if __name__ == "__main__":
    main()
