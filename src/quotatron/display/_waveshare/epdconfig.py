"""Waveshare epdconfig SPI/GPIO bindings - STUB.

The real driver is fetched at install time on the Pi (see scripts/install.sh).
On dev machines, importing this module is fine; using any of the SPI/GPIO
helpers raises RuntimeError so misuse is caught early.

License: BSD-3 - Waveshare reference code.
URL: https://github.com/waveshare/e-Paper
"""
from __future__ import annotations


def _unavailable(*_args, **_kwargs):
    raise RuntimeError(
        "Waveshare epdconfig not vendored on this machine. "
        "Run scripts/install.sh on the Pi (or vendor manually from "
        "https://github.com/waveshare/e-Paper)."
    )


# Public surface mirroring the upstream epdconfig module so accidental imports
# don't AttributeError - they raise RuntimeError on call instead.
module_init = _unavailable
module_exit = _unavailable
digital_write = _unavailable
digital_read = _unavailable
delay_ms = _unavailable
spi_writebyte = _unavailable
spi_writebyte2 = _unavailable
