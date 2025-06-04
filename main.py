import os
import time
from sys import exit

# Import dependancies
from PIL import Image, ImageDraw, ImageFont
from font_fredoka_one import FredokaOne
from inky import eeprom
from inky import phat
from weather import WeatherManagerClass

# Import secrets
from secrets import Secrets

# Debug boolean
DEBUG = True

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
WeatherManager = WeatherManagerClass(display)

# Initial boot, print the InkyPhat Logo
try:
    display.set_border(display.BLACK)
except NotImplementedError:
    pass

img = Image.open(os.path.join(PATH, "resources/InkypHAT-250x122.png")).resize(display.resolution)
display.set_image(img)
display.show()

time.sleep(30)
WeatherManager.doWeatherUpdate()
