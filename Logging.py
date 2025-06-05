import smbus
import time
import os
import sys
import signal
from enum import Enum

# Import dependancies
from PIL import Image, ImageDraw, ImageFont
from font_fredoka_one import FredokaOne
from inky import eeprom
from inky import phat
from PiSugar import PiSugarClass

# Debug boolean
DEBUG = True

def signalHandler(sig, frame):
    print("Process ended")
    del PiSugar
    if DEBUG:
        fid.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signalHandler)

def create_mask(self, source):
    """Create a transparency mask.

    Takes a paletized source image and converts it into a mask
    permitting all the colours supported by Inky pHAT (0, 1, 2)
    or an optional list of allowed colours.

    :param mask: Optional list of Inky pHAT colours to allow.

    """
    mask=(display.WHITE, display.BLACK, display.RED)
    mask_image = Image.new("1", source.size)
    w, h = source.size
    for x in range(w):
        for y in range(h):
            p = source.getpixel((x, y))
            if p in mask:
                mask_image.putpixel((x, y), 255)

    return mask_image

# Connect to the Inky Display
_eeprom = eeprom.read_eeprom()
if _eeprom is None:
    raise RuntimeError("No EEPROM detected! You must manually initialise your Inky board.")
elif _eeprom.display_variant != 11:
    if DEBUG:
        print("Found eeprom id " + _eeprom.display_variant)
    raise RuntimeError("Display is not the expected variant")

PiSugar = PiSugarClass()
display = phat.InkyPHAT_SSD1608("red")
try:
    display.set_border(display.BLACK)
except NotImplementedError:
    pass

if DEBUG:
    fid = open("~/LogVoltage.csv", "x")

while True:
    # Blank canvas
    img = Image.new("P", (250, 122), 0)
    draw = ImageDraw.Draw(img)

    # Load the FredokaOne font
    font = ImageFont.truetype(FredokaOne, 12)
    draw.text((38, 14), "Battery: %.3f V | %.1f %%" % PiSugar.getBatteryVoltage() % PiSugar.getBatteryPerc(), display.Black, font=font)
    draw.text((38, 44), PiSugar.buffDump(), display.Black, font=font)
    if DEBUG:
        fid.write()

    # Update Display
    display.set_image(img)
    display.show()

    time.sleep(300.0)

