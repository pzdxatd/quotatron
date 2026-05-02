"""E-paper driver for DFRobot DFR0591 v3.0 (2.13" 250×122 px).

Uses the SSD1675-compatible command set (same as Waveshare 2.13" V3).
The only difference from the Waveshare driver is the pin map, which comes
from this package's epdconfig (RST=26, DC=17, CS=27, BUSY=4).
"""
import logging
from . import epdconfig

EPD_WIDTH  = 122
EPD_HEIGHT = 250

logger = logging.getLogger(__name__)


class EPD:
    width  = EPD_WIDTH
    height = EPD_HEIGHT

    def __init__(self):
        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin    = epdconfig.DC_PIN
        self.busy_pin  = epdconfig.BUSY_PIN
        self.cs_pin    = epdconfig.CS_PIN

    # ------------------------------------------------------------------
    # Waveform LUTs
    # ------------------------------------------------------------------

    lut_partial_update = [
        0x0,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x80,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x40,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x14,0x0,0x0,0x0,0x0,0x0,0x0,
        0x1,0x0,0x0,0x0,0x0,0x0,0x0,
        0x1,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x22,0x22,0x22,0x22,0x22,0x22,0x0,0x0,0x0,
        0x22,0x17,0x41,0x00,0x32,0x36,
    ]

    lut_full_update = [
        0x80,0x4A,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x40,0x4A,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x80,0x4A,0x40,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x40,0x4A,0x80,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0xF,0x0,0x0,0x0,0x0,0x0,0x0,
        0xF,0x0,0x0,0xF,0x0,0x0,0x2,
        0xF,0x0,0x0,0x0,0x0,0x0,0x0,
        0x1,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x0,0x0,0x0,0x0,0x0,0x0,0x0,
        0x22,0x22,0x22,0x22,0x22,0x22,0x0,0x0,0x0,
        0x22,0x17,0x41,0x0,0x32,0x36,
    ]

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    def reset(self):
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(20)
        epdconfig.digital_write(self.reset_pin, 0)
        epdconfig.delay_ms(2)
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(20)

    def send_command(self, command):
        epdconfig.digital_write(self.dc_pin, 0)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([command])
        epdconfig.digital_write(self.cs_pin, 1)

    def send_data(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([data])
        epdconfig.digital_write(self.cs_pin, 1)

    def send_data2(self, data):
        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte2(data)
        epdconfig.digital_write(self.cs_pin, 1)

    def ReadBusy(self):
        logger.debug("e-Paper busy")
        while epdconfig.digital_read(self.busy_pin) == 1:
            epdconfig.delay_ms(10)
        logger.debug("e-Paper busy release")

    def TurnOnDisplay(self):
        self.send_command(0x22)
        self.send_data(0xC7)
        self.send_command(0x20)
        self.ReadBusy()

    def TurnOnDisplayPart(self):
        self.send_command(0x22)
        self.send_data(0x0F)
        self.send_command(0x20)
        self.ReadBusy()

    def Lut(self, lut):
        self.send_command(0x32)
        # SSD1675 wants per-byte CS toggling for LUT writes — bulk SPI here
        # left the chip in a state where TurnOnDisplayPart never released
        # BUSY. Image data (cmd 0x24) accepts bulk fine; LUT (cmd 0x32) does
        # not.
        for i in range(153):
            self.send_data(lut[i])
        self.ReadBusy()

    def SetLut(self, lut):
        self.Lut(lut)
        self.send_command(0x3F)
        self.send_data(lut[153])
        self.send_command(0x03)
        self.send_data(lut[154])
        self.send_command(0x04)
        self.send_data(lut[155])
        self.send_data(lut[156])
        self.send_data(lut[157])
        self.send_command(0x2C)
        self.send_data(lut[158])

    def SetWindow(self, x_start, y_start, x_end, y_end):
        self.send_command(0x44)
        self.send_data((x_start >> 3) & 0xFF)
        self.send_data((x_end   >> 3) & 0xFF)
        self.send_command(0x45)
        self.send_data(y_start & 0xFF)
        self.send_data((y_start >> 8) & 0xFF)
        self.send_data(y_end & 0xFF)
        self.send_data((y_end   >> 8) & 0xFF)

    def SetCursor(self, x, y):
        self.send_command(0x4E)
        self.send_data(x & 0xFF)
        self.send_command(0x4F)
        self.send_data(y & 0xFF)
        self.send_data((y >> 8) & 0xFF)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def init(self):
        if epdconfig.module_init() != 0:
            return -1
        self.reset()
        self.ReadBusy()
        self.send_command(0x12)   # SWRESET
        self.ReadBusy()

        self.send_command(0x01)   # Driver output control
        self.send_data(0xF9)
        self.send_data(0x00)
        self.send_data(0x00)

        self.send_command(0x11)   # Data entry mode
        self.send_data(0x03)

        self.SetWindow(0, 0, self.width - 1, self.height - 1)
        self.SetCursor(0, 0)

        self.send_command(0x3C)
        self.send_data(0x05)

        self.send_command(0x21)   # Display update control
        self.send_data(0x00)
        self.send_data(0x80)

        self.send_command(0x18)
        self.send_data(0x80)

        self.ReadBusy()
        self.SetLut(self.lut_full_update)
        return 0

    def getbuffer(self, image):
        from PIL import Image as _Image
        img = image
        iw, ih = img.size
        if iw == self.width and ih == self.height:
            img = img.convert("1")
        elif iw == self.height and ih == self.width:
            img = img.rotate(90, expand=True).convert("1")
        else:
            logger.warning(
                "Wrong image dimensions %s; expected %dx%d",
                img.size, self.width, self.height,
            )
            return bytearray(int(self.width / 8) * self.height)
        return bytearray(img.tobytes("raw"))

    def display(self, image):
        # Bulk SPI write — old byte-by-byte loop did ~3800 single-byte
        # send_data() calls, each toggling DC/CS pins. send_data2 ships the
        # whole framebuffer in one transaction.
        self.send_command(0x24)
        self.send_data2(list(image))
        self.TurnOnDisplay()

    def displayPartial(self, image):
        # The soft-RST + LUT reload is mandatory per-frame on SSD1675: the
        # panel's update state machine requires the partial waveform to be
        # re-activated each refresh. Removing it caused TurnOnDisplayPart to
        # never release BUSY (verified — main thread spun in ReadBusy).
        # The per-frame LUT cost is amortised by the bulk SPI write in Lut().
        epdconfig.digital_write(self.reset_pin, 0)
        epdconfig.delay_ms(1)
        epdconfig.digital_write(self.reset_pin, 1)

        self.SetLut(self.lut_partial_update)
        self.send_command(0x37)
        for b in [0x00, 0x00, 0x00, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00]:
            self.send_data(b)

        self.send_command(0x3C)
        self.send_data(0x80)

        self.send_command(0x22)
        self.send_data(0xC0)
        self.send_command(0x20)
        self.ReadBusy()

        self.SetWindow(0, 0, self.width - 1, self.height - 1)
        self.SetCursor(0, 0)

        self.send_command(0x24)
        self.send_data2(image)
        self.TurnOnDisplayPart()

    def Clear(self, color=0xFF):
        linewidth = self.width // 8 if self.width % 8 == 0 else self.width // 8 + 1
        self.send_command(0x24)
        self.send_data2([color] * (self.height * linewidth))
        self.TurnOnDisplay()

    def sleep(self):
        self.send_command(0x10)
        self.send_data(0x01)
        epdconfig.delay_ms(2000)
        epdconfig.module_exit()
