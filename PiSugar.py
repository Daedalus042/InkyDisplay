import smbus
import time
import os
from enum import Enum

# Import dependancies
from PIL import Image, ImageDraw, ImageFont
from font_fredoka_one import FredokaOne
from inky import eeprom
from inky import phat

class PiSugarClass:
    ADDRESS = 0x57
    Available = False
    _i2cBus = None

    def __init__(self):
        # Open I2C connection
        self._i2cBus = smbus.SMBus(1)

        try:
            SugarID = self._i2cBus.read_byte_data(self.ADDRESS, 0)
            if SugarID == 3:
                self.Available = True
        except OSError as err:
            print("Attention, no PiSugar found!")

    def __del__(self):
        # Close I2C connection
        if self._i2cBus is not None:
            self._i2cBus.close()

    def getBatteryVoltage(self):
        lowerByte = self._i2cBus.read_byte_data(self.ADDRESS, self._registerMap.BatteryLower.value)
        upperByte = self._i2cBus.read_byte_data(self.ADDRESS, self._registerMap.BatteryUpper.value)
        return (((upperByte << 8) + lowerByte) / 10000.0)

    def getBatteryPerc(self):
        return (((self.getBatteryVoltage() - 3.1) / 1.1) * 100.0)

    class _registerMap(Enum):
        Temperature  = 0x04
        BatteryLower = 0x22
        BatteryUpper = 0x23
        FW_Version_0 = 0xE2
        FW_Version_1 = 0xE3
        FW_Version_2 = 0xE4
        FW_Version_3 = 0xE5
        FW_Version_4 = 0xE6
        FW_Version_5 = 0xE7
        FW_Version_6 = 0xE8
        FW_Version_7 = 0xE9
        FW_Version_8 = 0xEA
        FW_Version_9 = 0xEB
        FW_Version_A = 0xEC
        FW_Version_B = 0xED

if __name__ == "__main__":
    # Get the current path
    PATH = os.path.dirname(__file__)


    # Connect to the Inky Display
    _eeprom = eeprom.read_eeprom()
    if _eeprom is None:
        raise RuntimeError("No EEPROM detected! You must manually initialise your Inky board.")
    elif _eeprom.display_variant != 11:
        if DEBUG:
            print("Found eeprom id " + _eeprom.display_variant)
        raise RuntimeError("Display is not the expected variant")

    display = phat.InkyPHAT_SSD1608("red")
    PiSugar = PiSugarClass()

    try:
        display.set_border(display.RED)
    except NotImplementedError:
        pass

    img = Image.open(os.path.join(PATH, "resources/Background_250x122.png")).resize(display.resolution)
    draw = ImageDraw.Draw(img)

    # Load the FredokaOne font
    font = ImageFont.truetype(FredokaOne, 22)
    draw.text((38, 14), "Battery:", display.WHITE, font=font)
    draw.text((38, 43), "%.3f V" % PiSugar.getBatteryVoltage(), display.WHITE, font=font)
    draw.text((38, 72), "%.1f %%" % PiSugar.getBatteryPerc(), display.WHITE, font=font)

    # display the battery information on Inky pHAT
    display.set_image(img)
    display.show()
