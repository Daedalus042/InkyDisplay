import argparse
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
import PiSugar

# Import secrets
from secrets import Secrets

# Debug boolean
DEBUG = True

# Get the current path
PATH = os.path.dirname(__file__)

parser = argparse.ArgumentParser()
parser.add_argument(
    "--display",
    default=False,
    action='store_true',
    help="Display Battery information to the phat",
)
args = parser.parse_args()

if __name__ == "__main__":
    if args.display:
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

        PiSugar = PiSugar.PiSugarConnect()
        display = phat.InkyPHAT_SSD1608("red")
        try:
            display.set_border(display.BLACK)
        except NotImplementedError:
            pass

        if DEBUG:
            fid = open(os.path.join(PATH, "../LiveLogVoltage.csv"), "w")

        while True:
            # Blank canvas
            img = Image.new("P", (250, 122), 0)
            draw = ImageDraw.Draw(img)

            # Load the FredokaOne font
            font = ImageFont.truetype(FredokaOne, 11)
            draw.text((5, 10), "Battery: %.3f V | %.1f %%" % (PiSugar.getBatteryVoltage(), PiSugar.getBatteryPerc()), display.BLACK, font=font)
            bd = PiSugar.buffDump()
            bufferString = ""
            for byte in bd:
                bufferString += "0x%02X " % byte
            draw.text((5, 30), bufferString[0:40], display.BLACK, font=font)
            draw.text((5, 45), bufferString[40:80], display.BLACK, font=font)
            draw.text((5, 60), bufferString[80:110], display.BLACK, font=font)
            draw.text((185, 60), bufferString[110:120], display.RED, font=font)
            draw.text((5, 75), bufferString[120:160], display.BLACK, font=font)
            draw.text((5, 90), bufferString[160:200], display.BLACK, font=font)
            draw.text((5, 105), bufferString[200:], display.BLACK, font=font)
            if DEBUG:
                fid.write(time.strftime('%H:%M,') + bufferString.replace(" ", ","))

            # Update Display
            display.set_image(img)
            display.show()

            for i in range(0, 150):
                time.sleep(2.0)
    else:
        fid = open(os.path.join(PATH, "../LogVoltage10m.csv"), "a")
        PiSugar = PiSugar.PiSugarConnect()
        fid.write(time.strftime('%d %H:%M, ') + "%.3f V  --  %.3f %%  --  Energy: %i  --  Is Charging? " % (PiSugar.getBatteryVoltage(), PiSugar.getBatteryPerc(), PiSugar.getBatteryEnergy()) + str(PiSugar.isSuppliedPower()) + "\n")
        fid.close()
