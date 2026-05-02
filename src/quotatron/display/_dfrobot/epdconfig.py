"""DFRobot DFR0591 v3.0 GPIO / SPI configuration.

BCM pin map:
  RST  = 26  (v3.0 added explicit RST; v1/v2 had onboard RC reset)
  DC   = 17
  CS   = 27  (software CS — the HAT does not use hardware CE0)
  BUSY = 4

On non-Pi machines (Windows dev), all functions fall back to stubs that
raise RuntimeError on call so the module imports cleanly without hardware.
"""
import sys
import time

RST_PIN  = 26
DC_PIN   = 17
CS_PIN   = 27
BUSY_PIN = 4


def _unavailable(*_a, **_kw):
    raise RuntimeError(
        "DFRobot GPIO/SPI unavailable — run on Pi with gpiozero + spidev installed."
    )


try:
    import spidev as _spidev
    import gpiozero as _gpiozero

    _spi  = _spidev.SpiDev()
    _rst  = _gpiozero.LED(RST_PIN)
    _dc   = _gpiozero.LED(DC_PIN)
    _cs   = _gpiozero.LED(CS_PIN)
    _busy = _gpiozero.Button(BUSY_PIN, pull_up=False)

    def digital_write(pin: int, value: int) -> None:
        if   pin == RST_PIN:  (_rst.on()  if value else _rst.off())
        elif pin == DC_PIN:   (_dc.on()   if value else _dc.off())
        elif pin == CS_PIN:   (_cs.on()   if value else _cs.off())

    def digital_read(pin: int) -> int:
        if pin == BUSY_PIN:
            return int(_busy.value)
        return 0

    def delay_ms(ms: float) -> None:
        time.sleep(ms / 1000.0)

    def spi_writebyte(data) -> None:
        _spi.writebytes(data)

    def spi_writebyte2(data) -> None:
        _spi.writebytes2(data)

    def module_init() -> int:
        _cs.on()                        # CS inactive (high) before opening SPI
        _spi.open(0, 0)
        _spi.max_speed_hz = 4_000_000
        _spi.mode = 0b00
        return 0

    def module_exit(cleanup: bool = False) -> None:
        try:
            _spi.close()
        except Exception:
            pass
        _rst.off()
        _dc.off()
        _cs.off()
        if cleanup:
            for _dev in (_rst, _dc, _cs, _busy):
                try:
                    _dev.close()
                except Exception:
                    pass

except Exception:
    digital_write  = _unavailable
    digital_read   = _unavailable
    delay_ms       = _unavailable
    spi_writebyte  = _unavailable
    spi_writebyte2 = _unavailable
    module_init    = _unavailable
    module_exit    = _unavailable
