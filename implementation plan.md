# Implementation Plan: Dynamic Office NamePlate System

**Course:** Systems Analysis — Mini-Lab 2  
**Target Platform:** Raspberry Pi Pico (MicroPython) / Wokwi Simulator  
**Architecture:** Model-View-Controller (MVC) Pattern  

---

## 1. Architecture & Design Alignment

This implementation plan strictly mirrors the exact classes, attributes, methods, and relationships defined in your revised UML class diagram (`media_1793934443187_416e8bc1.png`). No extra methods, helper classes, or unnecessary features are added.

### Key Design Principles:
1. **Strict 1:1 UML Conformance:** Every class, attribute, and method matches your diagram exactly.
2. **String-based `getDisplayInfo()`:** Each employee type returns a single descriptive string via `getDisplayInfo() : string`. `NamePlateView` handles formatting this text across the 2-line LCD.
3. **Controller-Guarded Administrator Availability:** In `NamePlate.changeAvailability()`, the controller checks whether the current employee is an `Administrator`. If so, manual button cycling is blocked because availability is automated by `Calendar`. `Administrator` does not require extra methods.
4. **Complete Button Event Callbacks:** Both `buttonPressed(name)` and `buttonReleased(name)` are implemented in `NamePlate`. `handleButtons()` serves to bind and initialize the button handlers.
5. **Exact `Calendar` Interface:** `Calendar` contains only the `events: list` attribute and the `getAvailability() : string` method.

---

## 2. System Architecture & Class Specifications

```
┌────────────────────────────────────────────────────────┐
│                      CONTROLLER                        │
│                      NamePlate                         │
│  - employees: list                                     │
│  - currentIndex: int                                   │
│  - view: NamePlateView                                 │
│  - previousButton, nextButton, availabilityButton      │
│  - buttonPressed() & buttonReleased() callbacks        │
│  - Prevents manual availability for Administrator      │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
       Updates / Reads              Renders to
                ▼                        ▼
┌───────────────────────────┐  ┌─────────────────────────┐
│          MODEL            │  │          VIEW           │
│   Employee (Base Class)   │  │      NamePlateView      │
│   ├── Faculty             │  │  - Formats LCDDisplay   │
│   ├── Staff               │  │  - Sets LightStrip color│
│   ├── Administrator       │  │  - Plays PassiveBuzzer  │
│   └── StudentWorker       │  └─────────────────────────┘
│   Calendar (Admin only)   │
└───────────────────────────┘
```

---

### 2.1 Model Layer

#### `Calendar`
* **Attributes:**
  * `events : list`: List of scheduled calendar event strings (e.g., `["Meeting", "Office Hours"]`).
* **Methods:**
  * `getAvailability() -> string`: Evaluates `events` to return `"Available"`, `"Away"`, or `"Busy"`.

#### `Employee` (Base Class)
* **Attributes:**
  * `name : string`
  * `position : string`
  * `department : string`
  * `email : string`
  * `phoneNumber : string`
  * `availability : string` (`"Available"`, `"Away"`, `"Busy"`)
* **Methods:**
  * `getAvailability() -> string`: Returns current availability status.
  * `cycleAvailability() -> void`: Cycles sequentially: `Available` $\rightarrow$ `Away` $\rightarrow$ `Busy` $\rightarrow$ `Available`.
  * `getDisplayInfo() -> string`: Returns a baseline information string (e.g., `self.position`).

#### `Administrator` (Inherits from `Employee`)
* **Attributes:**
  * `calendar : Calendar`: Associated calendar object.
* **Methods:**
  * `getAvailability() -> string`: Queries `self.calendar.getAvailability()`.
  * `getDisplayInfo() -> string`: Returns administrative information string (e.g., `"Admin Office"`).

#### `Faculty` (Inherits from `Employee`)
* **Attributes:**
  * `courses : list`: List of course codes (e.g., `["COP4338", "CIS3931"]`).
  * `officeHours : string`: Office hours schedule string (e.g., `"MWF 10-12"`).
* **Methods:**
  * `getDisplayInfo() -> string`: Returns course and office hours string (e.g., `"COP4338 MWF 10-12"`).

#### `Staff` (Inherits from `Employee`)
* **Methods:**
  * `getDisplayInfo() -> string`: Returns staff information string (e.g., `f"{self.department} Staff"`).

#### `StudentWorker` (Inherits from `Employee`)
* **Methods:**
  * `getDisplayInfo() -> string`: Returns student worker information string (e.g., `"Student Assistant"`).

---

### 2.2 View Layer: `NamePlateView`

Encapsulates all physical output devices (`LCDDisplay`, `LightStrip`, `PassiveBuzzer`).

* **Attributes:**
  * `lcd : LCDDisplay`: 1602 LCD display instance.
  * `lightStrip : LightStrip`: NeoPixel RGB strip instance.
  * `buzzer : PassiveBuzzer`: Passive buzzer instance.
* **Methods:**
  * `showEmployee(employee : Employee) -> void`:
    * Retrieves employee name and specific info string: `info = employee.getDisplayInfo()`.
    * Formats Line 1 for the 1602 LCD: Employee name (padded/truncated to 16 chars).
    * Formats Line 2 for the 1602 LCD: `[Status] Info` (e.g., `"[Avail] COP4338"`, padded/truncated to 16 chars).
    * Writes both lines using `self.lcd.showText()`.
  * `showAvailability(status : string) -> void`:
    * Maps status to standard RGB colors:
      * `"Available"` $\rightarrow$ Green `(0, 255, 0)`
      * `"Away"` $\rightarrow$ Amber/Yellow `(255, 180, 0)`
      * `"Busy"` $\rightarrow$ Red `(255, 0, 0)`
    * Calls `self.lightStrip.setColor(color)`.
  * `playChangeSound() -> void`:
    * Emits a brief click/tone via `self.buzzer.play(1000)` followed by `self.buzzer.stop()` (or `beep()`) to give feedback when navigation or status changes occur.

---

### 2.3 Controller Layer: `NamePlate`

Coordinates hardware button inputs, manages the employee roster, and directs `NamePlateView`.

* **Attributes:**
  * `employees : list`: List of `Employee` instances.
  * `currentIndex : int`: Index of the currently displayed employee (starts at `0`).
  * `view : NamePlateView`: Reference to view instance.
  * `previousButton : Button`: Navigation button for previous employee.
  * `nextButton : Button`: Navigation button for next employee.
  * `availabilityButton : Button`: Status toggle button.
* **Methods:**
  * `handleButtons() -> void`:
    * Sets `self` as the callback handler for `previousButton`, `nextButton`, and `availabilityButton` using `btn.setHandler(self)`.
  * `buttonPressed(name : string) -> void`:
    * Dispatches actions based on which button triggered the hardware interrupt:
      * If `name == self.previousButton._name` $\rightarrow$ calls `self.previousEmployee()`.
      * If `name == self.nextButton._name` $\rightarrow$ calls `self.nextEmployee()`.
      * If `name == self.availabilityButton._name` $\rightarrow$ calls `self.changeAvailability()`.
  * `buttonReleased(name : string) -> void`:
    * Implements the release callback required by `Button.py` (logs debug info).
  * `previousEmployee() -> void`:
    * Decrements `currentIndex` with wrap-around: `(currentIndex - 1) % len(employees)`.
    * Calls `self.view.playChangeSound()`.
    * Calls `self.updateDisplay()`.
  * `nextEmployee() -> void`:
    * Increments `currentIndex` with wrap-around: `(currentIndex + 1) % len(employees)`.
    * Calls `self.view.playChangeSound()`.
    * Calls `self.updateDisplay()`.
  * `changeAvailability() -> void`:
    * Retrieves active employee: `emp = self.getCurrentEmployee()`.
    * **Administrator Guard:** Checks `if isinstance(emp, Administrator):`
      * If `Administrator`: Does **not** change status; logs that administrator availability is automated by `Calendar`.
      * If non-administrator: Calls `emp.cycleAvailability()`.
    * Calls `self.view.playChangeSound()`.
    * Calls `self.updateDisplay()`.
  * `getCurrentEmployee() -> Employee`:
    * Returns `self.employees[self.currentIndex]` if roster is non-empty, otherwise `None`.
  * `updateDisplay() -> void`:
    * Retrieves `emp = self.getCurrentEmployee()`.
    * Calls `self.view.showEmployee(emp)`.
    * Calls `self.view.showAvailability(emp.getAvailability())`.

---

## 3. Hardware Pinout & Wokwi Connections

| Component | Wokwi Part ID | Pico Pin | Connection Notes |
| :--- | :--- | :--- | :--- |
| **LCD 1602 (I2C)** | `wokwi-lcd1602` | `GP0` (SDA), `GP1` (SCL) | VCC $\rightarrow$ 5V, GND $\rightarrow$ GND |
| **NeoPixel Ring (8)** | `wokwi-led-ring` | `GP2` (DIN) | VCC $\rightarrow$ 3.3V, GND $\rightarrow$ GND |
| **Previous Button** | `wokwi-pushbutton` | `GP13` | Pin 1.L $\rightarrow$ GP13, Pin 2.R $\rightarrow$ GND (`lowActive=True`) |
| **Next Button** | `wokwi-pushbutton` | `GP14` | Pin 1.L $\rightarrow$ GP14, Pin 2.R $\rightarrow$ GND (`lowActive=True`) |
| **Availability Button** | `wokwi-pushbutton` | `GP15` | Pin 1.L $\rightarrow$ GP15, Pin 2.R $\rightarrow$ GND (`lowActive=True`) |
| **Passive Buzzer** | `wokwi-buzzer` | `GP16` | Pin 1 $\rightarrow$ GND, Pin 2 $\rightarrow$ GP16 |

---

## 4. Execution Flow Diagram

```
[Button Pressed] ──> Button._callback() ──> NamePlate.buttonPressed(name)
                                                    │
                 ┌──────────────────────────────────┼──────────────────────────────────┐
                 ▼                                  ▼                                  ▼
      [name == "btn_prev"]               [name == "btn_next"]               [name == "btn_status"]
                 │                                  │                                  │
                 ▼                                  ▼                                  ▼
      previousEmployee()                 nextEmployee()                     changeAvailability()
                 │                                  │                                  │
                 │                                  │                     ┌────────────┴────────────┐
                 │                                  │                     ▼                         ▼
                 │                                  │              [Administrator]          [Non-Administrator]
                 │                                  │              (Block change;            emp.cycleAvailability()
                 │                                  │              log calendar notice)             │
                 └──────────────────────────────────┼───────────────────────────────────────────────┘
                                                    │
                                                    ▼
                                          NamePlate.updateDisplay()
                                                    │
                               ┌────────────────────┴────────────────────┐
                               ▼                                         ▼
                     view.showEmployee(emp)                 view.showAvailability(status)
                               │                                         │
                               ▼                                         ▼
                     LCD: Line 1 (Name)                     LightStrip: Set Color
                          Line 2 ([Status] Info)                        (Green/Amber/Red)
                               │
                               ▼
                     view.playChangeSound() (Buzzer click)
```

---

## 5. Verification & Testing Checklist

When we proceed to the coding stage, verification will validate:
1. **Model Inheritance & Display Info:**
   * Each employee type returns its distinctive string from `getDisplayInfo()`.
   * Non-administrators cycle availability through `Available` $\rightarrow$ `Away` $\rightarrow$ `Busy`.
   * `Administrator.getAvailability()` correctly reflects `Calendar.getAvailability()`.
2. **View Presentation:**
   * Line 1 and Line 2 formatting on LCD 1602 stays within the 16-character limit.
   * `showAvailability()` updates NeoPixel colors correctly.
   * `playChangeSound()` triggers buzzer tones without freezing execution.
3. **Controller Logic:**
   * `previousEmployee()` and `nextEmployee()` navigate with circular wrap-around.
   * `changeAvailability()` updates `Faculty`, `Staff`, and `StudentWorker`, but blocks manual cycling for `Administrator`.
   * Both `buttonPressed()` and `buttonReleased()` handle interrupt events cleanly.
   * `handleButtons()` attaches handlers to all 3 buttons properly.
