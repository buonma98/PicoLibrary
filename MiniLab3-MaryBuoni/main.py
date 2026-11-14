"""
main.py
Main entry point for "QuickRate" customer satisfaction kiosk (Mini Lab 3 - 3-Button Layout).
Connects physical hardware peripherals to the Controller, View, and Model.
Author: buonma98
"""

import time
from Displays import LCDDisplay
from PioLightStrip import PioLightStrip
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
    print("Starting QuickRate Satisfaction Kiosk (3-Button Layout)...")

    # 1. Hardware setup matching physical kit and Wokwi circuit
    # LCD 1602 Display (I2C): SDA on GP0, SCL on GP1
    lcd = LCDDisplay(sda=0, scl=1)

    # Hardware PIO-based WS2812 LED ring (8 LEDs): DIN on GP16
    # Uses official rp2 PIO state machine for stable 800kHz timing on RP2040 and RP2350 (Pico 2 W)
    # Brightness 0.2 provides clear visibility while limiting current consumption on the 3V3 rail
    led_ring = PioLightStrip(pin=16, name="ring1", numleds=8, brightness=0.2)

    # Passive Buzzer: GP21
    buzzer = PassiveBuzzer(pin=21, name="bz1")

    # Three Pushbuttons (all lowActive / pull-up to ground):
    # - Green button on GP13: Customer Positive feedback (State 1)
    # - Red button on GP14: Customer Negative feedback (State 1)
    # - Blue button on GP15: Manager button (1st press = silence, 2nd press = reset)
    green_btn = Button(13, "green", handler=None)
    red_btn = Button(14, "red", handler=None)
    manager_btn = Button(15, "manager", handler=None)

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
        ultrasonicSensor=uss,
        debug=True
    )

    # 4. Start the Kiosk State Model loop
    controller.run()


if __name__ == '__main__':
    main()
