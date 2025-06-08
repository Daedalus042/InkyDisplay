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
    display.set_border(display.WHITE)
except NotImplementedError:
    pass

# Format XKCD image for display steps:
# - Open XCKD image
# - get original size
# - get display size
# ? Should the title be displayed/save space for the title
# * need to maintain original image aspect ratio
# - find the larger quotient of original/display
# - divide original (both dimensions) by quotient
# - crop
font = ImageFont.truetype(FredokaOne,12)
time.sleep(2)
sampleMethod = [Image.NEAREST, Image.BILINEAR, Image.BICUBIC, Image.LANCZOS]
img = Image.open("/home/pinky/.cache/Inky/xkcd_6-6.png")
(imgx, imgy) = img.size
quotient = max(imgx/display.resolution[0], imgy/(display.resolution[1]-15))
for i in range(3,4):
  sized = img.resize((int(imgx/quotient), int(imgy/quotient)),sampleMethod[i%4])
  cropped = sized.crop((0, -15, display.resolution[0], display.resolution[1]-15))
  draw = ImageDraw.Draw(cropped)
  draw.text((2, 2), "XKCD - Trojan Horse", display.WHITE, font=font)
  time.sleep(0.1)
  display.set_image(cropped)
  display.show()
  time.sleep(20)

# time.sleep(30)
# WeatherManager.doWeatherUpdate()
