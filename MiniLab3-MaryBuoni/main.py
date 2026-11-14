"""
main.py
Main entry point for "QuickRate" customer satisfaction kiosk (Mini Lab 3).
Connects physical hardware peripherals to the Controller, View, and Model.
Author: buonma98
"""

import time
from Displays import LCDDisplay
from LightStrip import LightStrip
from Buzzer import PassiveBuzzer
from Button import Button

try:
    from Sensors_advanced import UltrasonicSensor
except ImportError:
    from Sensors import UltrasonicSensor

from FeedbackStats import FeedbackStats
from ManagerAlert import ManagerAlert
from KioskView import KioskView
from FeedbackController import FeedbackController

# Ensure UML method names match PicoLibrary methods seamlessly
if not hasattr(UltrasonicSensor, 'getDistance'):
    UltrasonicSensor.getDistance = UltrasonicSensor.distance
if not hasattr(PassiveBuzzer, 'playTone'):
    PassiveBuzzer.playTone = PassiveBuzzer.play


def main():
    print("Starting QuickRate Satisfaction Kiosk...")

    # 1. Hardware setup matching Wokwi circuit
    # LCD 1602 Display (I2C): SDA on GP0, SCL on GP1
    lcd = LCDDisplay(sda=0, scl=1)

    # NeoPixel LightStrip (8 LEDs ring): DIN on GP16
    led_ring = LightStrip(pin=16, name="ring1", numleds=8, brightness=0.5)

    # Passive Buzzer: GP21
    buzzer = PassiveBuzzer(pin=21, name="bz1")

    # Four Pushbuttons (all lowActive / pull-up to ground):
    # - Green button on GP13: Customer Positive feedback
    # - Red button on GP14: Customer Negative feedback
    # - Blue button on GP15: Manager silence button (preserves ratings)
    # - Yellow button on GP18: Manager reset button (clears ratings & alarm)
    green_btn = Button(13, "green", handler=None)
    red_btn = Button(14, "red", handler=None)
    manager_btn = Button(15, "manager", handler=None)
    reset_btn = Button(18, "reset", handler=None)

    # Ultrasonic Sensor on GP2 (TRIG) and GP3 (ECHO)
    # Tripped when customer is within 10 cm (distance < 10.0 cm)
    uss = UltrasonicSensor(trigger=2, echo=3, name="uss", lowActive=True, threshold=10.0)

    # 2. Instantiate View, Model, and Alert components
    view = KioskView(lcd=lcd, leds=led_ring)
    # Alert threshold is set to 30.0% satisfaction
    stats = FeedbackStats(threshold=30.0, minVotes=1)
    alert = ManagerAlert(buzzer=buzzer, tone=880)

    # 3. Instantiate Controller with State Model
    controller = FeedbackController(
        view=view,
        stats=stats,
        alert=alert,
        greenButton=green_btn,
        redButton=red_btn,
        managerButton=manager_btn,
        resetButton=reset_btn,
        ultrasonicSensor=uss,
        debug=True
    )

    # 4. Start the Kiosk State Model loop
    controller.run()


if __name__ == '__main__':
    main()
