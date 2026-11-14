"""
PioLightStrip.py
Hardware PIO-based WS2812 (NeoPixel) driver for Raspberry Pi Pico and Pico 2 / Pico 2 W (RP2350).
Uses the official Raspberry Pi MicroPython PIO state machine to guarantee exact 800 kHz signal
timings on RP2040 and RP2350 microcontrollers regardless of CPU clock frequency.
Author: buonma98
"""

import time
import array
from Log import Log

# Color constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 200, 0)

# Check if running under MicroPython with rp2 support
try:
    import rp2
    from machine import Pin

    # Official Raspberry Pi MicroPython PIO WS2812 program
    @rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
    def _ws2812_pio():
        T1 = 2
        T2 = 5
        T3 = 3
        wrap_target()
        label("bitloop")
        out(x, 1)               .side(0)    [T3 - 1]
        jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
        jmp("bitloop")          .side(1)    [T2 - 1]
        label("do_zero")
        nop()                   .side(0)    [T2 - 1]
        wrap()

    _PIO_AVAILABLE = True
except (ImportError, AttributeError):
    _PIO_AVAILABLE = False


class PioLightStrip:
    """
    PIO-based WS2812 / NeoPixel LED driver.
    Drop-in replacement for LightStrip compatible with KioskView and PicoLibrary.
    Resolves the RP2350 (Pico 2 / Pico 2 W) timing corruption with the built-in neopixel driver.
    """

    # Standard LightStrip animation modes for interface compatibility
    FILLS = 0
    CHASES = 1
    RAINBOW = 2

    def __init__(self, pin: int = 16, numleds: int = 8, brightness: float = 0.2,
                 sm_id: int = 0, rgb_order: str = "GRB", name: str = "PioLightStrip"):
        """
        Initialize the PIO WS2812 driver.

        Parameters:
        -----------
        pin : int
            GPIO pin connected to the DIN of the LED ring (default GP16).
        numleds : int
            Number of LEDs in the ring (default 8).
        brightness : float
            Brightness scale factor between 0.0 and 1.0 (default 0.2 for low power).
        sm_id : int
            PIO StateMachine ID to use (0-7, default 0).
        rgb_order : str
            Color channel ordering: "GRB" (standard WS2812/NeoPixel) or "RGB".
        name : str
            Identifier name for logging.
        """
        self._pin_num = pin
        self._numleds = numleds
        self._brightness = max(0.0, min(1.0, brightness))
        self._rgb_order = rgb_order.upper()
        self._name = name

        # Internal raw color buffer [(R, G, B), ...]
        self._pixels = [(0, 0, 0)] * self._numleds

        # 32-bit DMA/FIFO word array for the PIO state machine
        self._sm_buffer = array.array("I", [0] * self._numleds)

        if _PIO_AVAILABLE:
            # 8 MHz frequency gives 125ns clock cycles (exact WS2812 timing on RP2040 and RP2350)
            self._sm = rp2.StateMachine(sm_id, _ws2812_pio, freq=8_000_000, sideset_base=Pin(pin))
            self._sm.active(1)
            Log.i(f"PioLightStrip: Initialized on GP{pin} with {numleds} LEDs (PIO SM {sm_id}, brightness {self._brightness})")
        else:
            self._sm = None
            Log.w("PioLightStrip: rp2/machine not available. Running in simulation/mock mode.")

        # Ensure all LEDs start OFF
        self.off()

    def setBrightness(self, brightness: float) -> None:
        """Set the global brightness multiplier (0.0 to 1.0)."""
        self._brightness = max(0.0, min(1.0, brightness))

    def getBrightness(self) -> float:
        """Return the current brightness multiplier."""
        return self._brightness

    def setPixel(self, index: int, color: tuple, show: bool = True) -> None:
        """
        Set a single pixel color (R, G, B).
        
        Parameters:
        -----------
        index : int
            0-based index of the pixel (0 to numleds - 1).
        color : tuple
            (R, G, B) tuple with values 0-255.
        show : bool
            Whether to transmit the update immediately to the LEDs.
        """
        if 0 <= index < self._numleds:
            self._pixels[index] = color
            if show:
                self.show()

    def setColor(self, color: tuple, numPixels: int = None) -> None:
        """
        Set LEDs to a specific color up to numPixels.
        Remaining LEDs beyond numPixels are turned OFF (BLACK).
        Matches the LightStrip.setColor(color, numPixels) interface.

        Parameters:
        -----------
        color : tuple
            (R, G, B) tuple, e.g. (0, 255, 0) for green.
        numPixels : int, optional
            Number of LEDs to turn on (0 to numleds). If None, all LEDs are lit.
        """
        if numPixels is None or numPixels > self._numleds:
            count = self._numleds
        else:
            count = max(0, int(numPixels))

        # First 'count' LEDs receive the color
        for i in range(count):
            self._pixels[i] = color

        # Remaining LEDs are turned off
        for i in range(count, self._numleds):
            self._pixels[i] = BLACK

        self.show()

    def show(self) -> None:
        """Transmit current pixel buffer out through the PIO state machine."""
        b = self._brightness
        order = self._rgb_order

        for i in range(self._numleds):
            r, g, b_val = self._pixels[i]
            # Apply brightness scaling
            adj_r = int(r * b)
            adj_g = int(g * b)
            adj_b = int(b_val * b)

            # WS2812 typically expects GRB byte order
            if order == "RGB":
                word = (adj_r << 16) | (adj_g << 8) | adj_b
            else: # Standard GRB
                word = (adj_g << 16) | (adj_r << 8) | adj_b

            self._sm_buffer[i] = word

        if self._sm:
            # Shift left by 8 so the 24 bits occupy the upper bits of the 32-bit word
            self._sm.put(self._sm_buffer, 8)
            # Short sleep to allow the WS2812 reset latch (>50us)
            if hasattr(time, "sleep_us"):
                time.sleep_us(100)
            elif hasattr(time, "sleep_ms"):
                time.sleep_ms(1)
            else:
                time.sleep(0.001)

    def off(self) -> None:
        """Turn off all LEDs immediately."""
        self._pixels = [BLACK] * self._numleds
        self.show()

    def on(self) -> None:
        """Turn all LEDs on white."""
        self._pixels = [WHITE] * self._numleds
        self.show()

    def clear(self) -> None:
        """Alias for off()."""
        self.off()

    def animate(self, color=None) -> None:
        """UML stub method for animation compatibility."""
        pass

    def run(self, runtype: int = 0) -> None:
        """PicoLibrary LightStrip stub method for animation compatibility."""
        pass
