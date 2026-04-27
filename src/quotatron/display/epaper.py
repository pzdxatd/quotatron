"""Hardware Waveshare 2.13" e-paper backend.

Conforms to ``quotatron.display._interface.Display``. The Waveshare driver
import is deferred to ``__init__`` so this module loads cleanly on dev
machines without ``spidev``/``RPi.GPIO``; only instantiating
``WaveshareDisplay`` triggers the hardware path.
"""
from __future__ import annotations

import importlib

from PIL import Image


class WaveshareDisplay:
    """Production e-paper backend driving the Waveshare 2.13" HAT.

    The wrapper exposes a landscape canvas (``250 x 122``) matching the
    rest of the codebase. The underlying Waveshare driver is portrait-native
    (``122 x 250``) and its ``getbuffer`` handles the rotation.
    """

    width = 250
    height = 122

    _DRIVER_MODULES = {
        "waveshare_2in13_v2": "epd2in13_V2",
        "waveshare_2in13_v3": "epd2in13_V3",
        "waveshare_2in13_v4": "epd2in13_V4",
    }

    def __init__(self, driver: str = "waveshare_2in13_v3") -> None:
        try:
            suffix = self._DRIVER_MODULES[driver]
        except KeyError as exc:
            raise ValueError(
                f"unknown driver {driver!r}; "
                f"expected one of {sorted(self._DRIVER_MODULES)}"
            ) from exc
        mod = importlib.import_module(f"quotatron.display._waveshare.{suffix}")
        self._epd = mod.EPD()
        self._epd.init()
        self._epd.Clear(0xFF)
        self._partial = False

    def display_full(self, img: Image.Image) -> None:
        if self._partial:
            # Exit partial mode by re-initing the panel in full-update mode.
            self._epd.init()
            self._partial = False
        self._epd.display(self._epd.getbuffer(img))

    def enter_partial_mode(self) -> None:
        if self._partial:
            return
        if hasattr(self._epd, "init_Partial"):
            self._epd.init_Partial()
        else:
            self._epd.init()
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
