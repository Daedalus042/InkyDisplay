import os

# Import dependancies
from PIL import Image, ImageDraw, ImageFont
from font_fredoka_one import FredokaOne
from inky import eeprom
from inky import phat

# Import secrets
from secrets import Secrets

# Debug boolean
DEBUG = True

# Get the current path
PATH = os.path.dirname(__file__)

if __name__ == "__main__":

    # Connect to the Inky Display
    _eeprom = eeprom.read_eeprom()
    if _eeprom is None:
        raise RuntimeError("No EEPROM detected! You must manually initialise your Inky board.")
    elif _eeprom.display_variant != 11:
        if DEBUG:
            print("Found eeprom id " + _eeprom.display_variant)
        raise RuntimeError("Display is not the expected variant")

    display = phat.InkyPHAT_SSD1608("red")

    try:
        display.set_border(display.RED)
    except NotImplementedError:
        pass

    img = Image.open(os.path.join(PATH, "resources/Goldy.png"))
    draw = ImageDraw.Draw(img)
    rahFont = ImageFont.truetype(FredokaOne, 25)
    _, _, txtx, txty = draw.textbbox((0,0), "SKI-U-MAH!", font=rahFont)
    draw.text((int((display.resolution[0] - txtx)/2), int((display.resolution[1] - txty))), "SKI-U-MAH!", display.RED, font=rahFont)
    display.set_image(img)
    display.show()
