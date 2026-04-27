"""Waveshare 2.13in V3 e-paper driver - STUB.

The real driver is fetched at install time on the Pi (see scripts/install.sh).
On dev machines, importing this module is fine; instantiating EPD raises
RuntimeError so misuse is caught early.

License: BSD-3 - Waveshare reference code.
URL: https://github.com/waveshare/e-Paper
"""
from __future__ import annotations


class EPD:
    """Stub - replace with vendored Waveshare driver on the Pi."""

    width = 122
    height = 250

    def __init__(self) -> None:
        raise RuntimeError(
            "Waveshare driver not vendored on this machine. "
            "Run scripts/install.sh on the Pi (or vendor manually from "
            "https://github.com/waveshare/e-Paper)."
        )

    def init(self) -> None: ...
    def init_Partial(self) -> None: ...
    def Clear(self, color: int) -> None: ...
    def display(self, image_buf: bytes) -> None: ...
    def displayPartial(self, image_buf: bytes) -> None: ...
    def getbuffer(self, image) -> bytes: ...
    def sleep(self) -> None: ...
