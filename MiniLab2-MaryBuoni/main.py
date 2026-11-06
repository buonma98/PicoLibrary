import time

from Displays import LCDDisplay
from LightStrip import LightStrip
from Buzzer import PassiveBuzzer
from Button import Button
from Employee import Calendar, Administrator, Faculty, Staff, StudentWorker
from NamePlateView import NamePlateView
from NamePlate import NamePlate

# Hardware
lcd = LCDDisplay(sda=0, scl=1)
lights = LightStrip(pin=2, numleds=8)
buzzer = PassiveBuzzer(pin=16)

# Three buttons
previous = Button(13, "btn_prev")
next_btn = Button(14, "btn_next")
availability = Button(15, "btn_status")

# Sample employee roster
employees = [
    Administrator("Dean Garcia", calendar=Calendar(["Meeting"])),
    Faculty("Dr. Mark Miller", courses=["COP4338"], officeHours="MWF 10-12"),
    Staff("Sarah Connor", department="IT Support"),
    StudentWorker("Emily Clark")
]

# Connect the view and controller
view = NamePlateView(lcd, lights, buzzer)

nameplate = NamePlate(
    view=view,
    previousButton=previous,
    nextButton=next_btn,
    availabilityButton=availability,
    employees=employees
)

# Keep the program running and handle any queued button presses
while True:
    if nameplate._pending_button is not None:
        pressed = nameplate._pending_button
        nameplate._pending_button = None
        nameplate._on_button_event(pressed)

    time.sleep(0.05)