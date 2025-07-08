import smbus
import time
import os
import math
from enum import Enum

# Import dependancies
from PIL import Image, ImageDraw, ImageFont
from font_fredoka_one import FredokaOne
from inky import eeprom
from inky import phat

# Debug boolean
DEBUG = True

def PiSugarConnect():
    # Open I2C connection
    _i2cBus = smbus.SMBus(1)

    try:
        SugarID = _i2cBus.read_byte_data(0x57, 0)
        if SugarID == 3:
            return PiSugarClass(_i2cBus)
    except OSError as err:
        print("Attention, no PiSugar found!")
        _i2cBus.close()
        return PiDummy()

class PiSugarClass:
    ADDRESS = 0x57
    Available = False
    _i2cBus = None

    def __init__(self, bus):
        self._i2cBus = bus
        self.Available = True

    def __del__(self):
        # Close I2C connection
        if self._i2cBus is not None:
            self._i2cBus.close()

    def isAvailable(self):
        return self.Available

    def getBatteryInfo(self):
        samples = []
        for i in range(0,10):
            lowerByte = self._i2cBus.read_byte_data(self.ADDRESS, self._registerMap.BatteryLower.value)
            upperByte = self._i2cBus.read_byte_data(self.ADDRESS, self._registerMap.BatteryUpper.value)
            energyLevel = self._i2cBus.read_byte_data(self.ADDRESS, self._registerMap.EnergyLevel.value)
            samples.append([upperByte, lowerByte, energyLevel])
            time.sleep(0.05)
        print(samples)

    def getBatteryBytes(self):
        lowerByte = self._i2cBus.read_byte_data(self.ADDRESS, self._registerMap.BatteryLower.value)
        upperByte = self._i2cBus.read_byte_data(self.ADDRESS, self._registerMap.BatteryUpper.value)
        return (upperByte << 8) + lowerByte

    def getBatteryVoltage(self):
        samples = []
        for i in range(0,10):
            lowerByte = self._i2cBus.read_byte_data(self.ADDRESS, self._registerMap.BatteryLower.value)
            upperByte = self._i2cBus.read_byte_data(self.ADDRESS, self._registerMap.BatteryUpper.value)
            samples.append(((upperByte << 8) + lowerByte) / 1000.0)
            time.sleep(0.05)
        avg = sum(samples) / len(samples)
        return avg

    def getBatteryEnergy(self):
        samples = []
        for i in range(0,10):
           samples.append(self._i2cBus.read_byte_data(self.ADDRESS, self._registerMap.EnergyLevel.value))
           time.sleep(0.1)
        return sum(samples) / len(samples)

    def getBatteryPerc(self):
        """
        Returns percent of battery charge available

        Shutdown voltage: ~ 3.0 V
        Max Voltage:      ~ 4.2? V
        ergo Battery range ~ 1.2 V from min to max

        Current way to determine the battery percentage uses the following peacewise functions
        for x <= 3.7: f(x)=150^(x-4.07)
        for 3.7 < x <= 3.775: f(x)=20^(14x-53.3)+0.15
        for 3.775 < x: -20^(-x+3.7)+1.2
        """
        voltage = self.getBatteryVoltage()
        if voltage <= 3.7:
            return 150^(voltage-4.07)
        elif voltage <= 3.775:
            return 20^(14*voltage-53.3)+0.15
        else:
            return -(20^(-voltage+3.7))+1.2

    def isSuppliedPower(self):
        PowerCtrlReg = self._i2cBus.read_byte_data(self.ADDRESS, self._registerMap.PowerCtrl.value)
        extPower = (PowerCtrlReg & (1 << 7)) > 0
        return extPower

    def create_mask(self, source):
        """Create a transparency mask.

        Takes a paletized source image and converts it into a mask
        permitting all the colours supported by Inky pHAT (0, 1, 2)
        or an optional list of allowed colours.

        :param mask: Optional list of Inky pHAT colours to allow.

        """

    def buffDump(self):
        buffer = []
        for i in range(0, 256, 32):
            word = self._i2cBus.read_i2c_block_data(0x57, i, 32)
            buffer.extend(word)
            time.sleep(0.1)
        return buffer

    class _registerMap(Enum):
        PowerCtrl    = 0x02
        Temperature  = 0x04
        BatteryUpper = 0x22
        BatteryLower = 0x23
        EnergyLevel  = 0x2A
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

    """ --- Register Map --- | Source: https://github.com/PiSugar/PiSugar/wiki/PiSugar-3-I2C-Datasheet
    Address |     7      |       6        |        5       |       4       |         3        |    2    |   1  |      0
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x02 |  External  |  Charge when   | Delayed System |  Auto Power   | Accidental Touch |  Power  | RSVD | Power Button
            | Power (RO) |  powered (rw)  | Shutdown (rw)  |    On (rw)    |   Control (rw)   | On (rw) |      |  State (RO)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x03 |    RSVD    |    Automatic   |      RSVD      |      Soft     |  Soft Shutdown   |         Reserved
            |            | Hibernate (rw) |                | Shutdown (rw) |   Status (RO)    |
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x04 |                                             Chip Temperature (RO)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x05 |                                                   Reserved
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x06 |            |                |                |               |                  |         Reserved
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x07 |                                              Watchdog Timeout
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x06 |                                   Reserved                                      |       Custom Button?
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x09 |                                         Delayed System Shutdown Time
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x0A |                                           Boot Watchdog Retry Limit
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x0B |                         Write Protection (rw):   Off = 0x29,   On = Any other value
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x0C |
        ... |                                                   Reserved
       0x1F |
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x20 | Charge (rw)|                    Reserved                     | SCL Awakening    |         Reserved
            | Protection |                                                 | (rw)             |
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x21 |                                                   Reserved
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x22 |                                          Upper Battery Voltage (rw)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x23 |                                          Lower Battery Voltage (rw)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x24 |
        ... |                                                   Reserved
       0x29 |
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x2A |                                             Percent Battery (RO)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x2B |
        ... |                                                   Reserved
       0x2F |
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x30 | ???????????????????????????????????????????????????????????????????????????????????????????????????????????????
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x31 |                                                RTC Year (rw)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x32 |                                               RTC Month (rw)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x33 |                                                RTC Day (rw)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x34 |                                              RTC Weekday (rw)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x35 |                                                RTC Hour (rw)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x36 |                                               RTC Minute (rw)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x37 |                                               RTC Second (rw)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x38 |
        ... |                                                   Reserved
       0x3F |
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x40 | Timed (rw) |                                             Reserved
            | Bootup     |
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x41 |
       0x42 |                                                   Reserved
       0x43 |
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x44 |  Reserved  |                                    Timed Bootup Weekday (rw)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x45 |                                           Timed Bootup Hour (rw)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x46 |                                          Timed Bootup Minute (rw)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x47 |                                          Timed Bootup Second (rw)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0x48 |
        ... |                                                   Reserved
       0xE1 |
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0xE2 |                                         Firmware Version char 0 (RO)
        ... |                                                     ...
       0xED |                                         Firmware Version char 11 (RO)
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
       0xEE |
        ... |                                                   Reserved
       0xFF |
    --------+------------+----------------+----------------+---------------+------------------+---------+------+--------------
        """

class PiDummy:
    def isAvailable(self):
        return False

    def getBatteryVoltage(self):
        return 0.0

    def getBatteryPerc(self):
        return 0

    def buffDump(self):
        return range(0, 256*32)

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
    PiSugar = PiSugarConnect()

    try:
        display.set_border(display.RED)
    except NotImplementedError:
        pass

    img = Image.open(os.path.join(PATH, "resources/Background_250x122.png")).resize(display.resolution)
    draw = ImageDraw.Draw(img)

    # Add Battery icon & number
    battPerc = PiSugar.getBatteryPerc()
    if battPerc > 80.0:
        battIcon = Image.open(os.path.join(PATH, "resources/icons/system/Battery4.png"))
    elif battPerc > 60.0:
        battIcon = Image.open(os.path.join(PATH, "resources/icons/system/Battery3.png"))
    elif battPerc > 40.0:
        battIcon = Image.open(os.path.join(PATH, "resources/icons/system/Battery2.png"))
    elif battPerc > 20.0:
        battIcon = Image.open(os.path.join(PATH, "resources/icons/system/Battery1.png"))
    else:
        battIcon = Image.open(os.path.join(PATH, "resources/icons/system/BatteryEmpty.png"))

    # Create Mask
    mask=(display.WHITE, display.BLACK, display.RED)
    mask_image = Image.new("1", battIcon.size)
    w, h = battIcon.size
    for x in range(w):
        for y in range(h):
            p = battIcon.getpixel((x, y))
            if p in mask:
                mask_image.putpixel((x, y), 255)
    img.paste(battIcon, (190, 1), mask_image)


    # Load the FredokaOne font
    font = ImageFont.truetype(FredokaOne, 22)
    draw.text((38, 14), "Battery:", display.WHITE, font=font)
    draw.text((38, 43), "%.3f V" % PiSugar.getBatteryVoltage(), display.WHITE, font=font)
    draw.text((38, 72), "%.1f %%" % PiSugar.getBatteryPerc(), display.WHITE, font=font)

    # display the battery information on Inky pHAT
    display.set_image(img)
    display.show()
