import os
import time
import json
import urllib.request
from sys import exit

# Import dependancies
from PIL import Image, ImageDraw, ImageFont
from font_fredoka_one import FredokaOne
from inky import eeprom
from inky import phat

# Import secrets
from secrets import Secrets

# Debug boolean
DEBUG = True

# Other important values
HEADER = 15

# Get the current path
PATH = os.path.dirname(__file__)
CACHE = "/home/" + Secrets.username + "/.cache/Inky/"

class xkcd:
    TITLE = ""
    NUMBER = 0
    IMG = None
    DAY = 0
    MONTH = 0
    YEAR = 0

    def __init__(self):
        self.refresh()


    def refresh(self):
        # Try to open the cached info file
        try:
            xkcdInfoFid = open(os.path.join(CACHE, "info.0.json"), "r")
            cachedInfo = json.load(xkcdInfoFid)
            xkcdInfoFid.close()
            self.Title = cachedInfo["title"]
            self.NUMBER = cachedInfo["num"]
            self.IMG = cachedInfo["img"]
            self.DAY = cachedInfo["day"]
            self.MONTH = cachedInfo["month"]
            self.YEAR = cachedInfo["year"]
        except:
            print("ERR: Could not open cached file")

        # Try to fetch the online info file
        try:
            xkcdUrl = urllib.request.Request("https://xkcd.com/info.0.json")
            stream = urllib.request.urlopen(xkcdUrl)
            currentJson = stream.read().decode()
            stream.close()
            currentInfo = json.load(currentJson)
            if currentInfo["num"] > self.NUMBER:
                print("Info: Found a new XKCD from %i/%i/%i" % (currentInfo["month"], currentInfo["day"], currentInfo["year"]))

                # Overwrite cached image
                imgFid = open(os.path.join(CACHE, "xkcd.png"), "w")
                imgStream = urllib.request.urlopen(currentInfo["img"])
                imgFid.write(imgStream.read().decode())
                imgStream.close()
                imgFid.close()

                # Overwrite cached info
                xkcdInfoFid = open(os.path.join(CACHE, "info.0.json"), "w")
                xkcdInfoFid.print(currentJson)
                xkcdInfoFid.close()

                # Clean-up
                urllib.request.urlcleanup()

            self.TITLE = currentInfo["title"]
            self.NUMBER = currentInfo["num"]
            self.IMG = currentInfo["img"]
            self.DAY = currentInfo["day"]
            self.MONTH = currentInfo["month"]
            self.YEAR = currentInfo["year"]
        except URLError:
            print("ERR: Could not open URL")
        except:
            print("ERR: Unexpected online error")

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
  font2 = ImageFont.truetype("DejaVuSans.ttf", 12)
  sampleMethod = [Image.NEAREST, Image.BILINEAR, Image.BICUBIC, Image.LANCZOS]
  img = Image.open(os.path.join(PATH, "xkcd.png"))
  (imgx, imgy) = img.size
  quotient = max(imgx/display.resolution[0], imgy/(display.resolution[1]-HEADER))
  (width, height) = (int(imgx/quotient), int(imgy/quotient))
  # (posx, posy) = (int(display.resolution[0] - sized.size[0])
  for i in range(3,4):
    sized = img.resize((int(imgx/quotient), int(imgy/quotient)),sampleMethod[i%4])
    imgOut = Image.new("RGB", display.resolution, (255, 255, 255))
    imgOut.paste(sized, (int((display.resolution[0] - sized.size[0])/2), int(HEADER + (display.resolution[1] - sized.size[1])/2)))
    # cropped = sized.crop((0, -15, display.resolution[0], display.resolution[1]-15))
    draw = ImageDraw.Draw(imgOut)
    draw.text((2, 2), "XKCD - Trojan Horse", display.BLACK, font=font2)
    time.sleep(0.1)
    display.set_image(imgOut)
    display.show()
    time.sleep(20)
