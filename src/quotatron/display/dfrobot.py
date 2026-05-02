"""DFRobot DFR0591 v3.0 e-paper backend.

Conforms to ``quotatron.display._interface.Display``. The EPD driver import
is deferred to ``__init__`` so this module loads cleanly on dev machines
without ``spidev``/``gpiozero``; only instantiating ``DFRobotDisplay``
triggers the hardware path.
"""
from __future__ import annotations

from PIL import Image


class DFRobotDisplay:
    """Production e-paper backend for the DFRobot DFR0591 v3.0 2.13" HAT.

    Landscape canvas (250 × 122) matching the rest of the codebase.
    The underlying EPD driver is portrait-native (122 × 250); getbuffer
    handles rotation.

    BCM pins: RST=26, DC=17, CS=27 (soft-CS), BUSY=4.
    """

    width  = 250
    height = 122

    def __init__(self) -> None:
        from quotatron.display._dfrobot.epd2in13 import EPD
        self._epd = EPD()
        self._epd.init()
        self._epd.Clear(0xFF)
        self._partial = False

    def display_full(self, img: Image.Image) -> None:
        if self._partial:
            self._epd.init()
            self._partial = False
        self._epd.display(self._epd.getbuffer(img))

    def enter_partial_mode(self) -> None:
        if self._partial:
            return
        # displayPartial() reloads the partial waveform LUT itself each
        # frame — SSD1675 requires the per-frame re-activation, so no
        # one-shot setup is needed here.
        self._partial = True

    def display_partial(self, img: Image.Image) -> None:
        if not self._partial:
            self.enter_partial_mode()
        self._epd.displayPartial(self._epd.getbuffer(img))

    def exit_partial_mode(self) -> None:
        self._partial = False

    def deep_clean(self) -> None:
        """Three-pass white/black/white flush to clear ghosting."""
        for fill in (0xFF, 0x00, 0xFF):
            blank = Image.new(
                "1", (self.width, self.height), 1 if fill == 0xFF else 0
            )
            self._epd.display(self._epd.getbuffer(blank))

    def shutdown(self, farewell: Image.Image | None = None) -> None:
        if farewell is not None:
            self.display_full(farewell)
        self._epd.sleep()
