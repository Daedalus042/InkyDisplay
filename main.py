import os

# Import dependancies
from PIL import Image
from inky.inky import eeprom
from inky.inky import phat

# Import secrets
from .secrets import Secrets

# Connect to the Inky Display
_eeprom = eeprom.read_eeprom()
if _eeprom is None:
    raise RuntimeError("No EEPROM detected! You must manually initialise your Inky board.")
elif _eeprom is not 11:
    raise RuntimeError("Display is not the expected variant")

display = phat.InkyPHAT_SSD1608("red")

# Initial boot, print the InkyPhat Logo
try:
    display.set_border(display.BLACK)
except NotImplementedError:
    pass

img = Image.open(os.path.join("/home/", Secrets.username, "inky/examples/phat/resources/InkypHAT-250x122.png"))
display.set_image(img)
display.show()
