import os
import time
import json
import traceback
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

class XkcdClass:
    TITLE = ""
    NUMBER = 0
    IMG = None
    DAY = 0
    MONTH = 0
    YEAR = 0
    DISPLAY = None

    def __init__(self):
        self.refresh()

    def __init__(self, display):
        self.DISPLAY = display
        self.refresh()


    def refresh(self, force=False):
        # Try to open the cached info file
        try:
            xkcdInfoFid = open(os.path.join(CACHE, "info.0.json"), "r")
            cachedInfo = json.load(xkcdInfoFid)
            xkcdInfoFid.close()
            self.TITLE = cachedInfo["title"]
            self.NUMBER = cachedInfo["num"]
            self.IMG = cachedInfo["img"]
            self.DAY = cachedInfo["day"]
            self.MONTH = cachedInfo["month"]
            self.YEAR = cachedInfo["year"]
            """if "%04i-%02i-%02i" % (self.YEAR, self.Month, self.DAY) is time.strftime("%Y-%m-%d", time.localtime()):
                 print("Most recent is already from today")
                 return"""
        except:
            print("ERR: Could not open cached file")

        # Try to fetch the online info file
        try:
            xkcdUrl = urllib.request.Request("https://xkcd.com/info.0.json")
            stream = urllib.request.urlopen(xkcdUrl)
            currentJson = stream.read().decode()
            stream.close()
            currentInfo = json.loads(currentJson)
            if currentInfo["num"] > self.NUMBER:
                print("Info: Found a new XKCD from %02i/%02i/%02i" % (int(currentInfo["month"]), int(currentInfo["day"]), int(currentInfo["year"])))

                # Overwrite cached image
                """ imgFid = open(os.path.join(CACHE, "xkcd.png"), "w")
                imgStream = urllib.request.urlopen(currentInfo["img"])
                imgFid.write(imgStream.read())
                imgStream.close()
                imgFid.close() """
                urllib.request.urlretrieve(currentInfo["img"], os.path.join(CACHE, "xkcd.png"))

                # Overwrite cached info
                xkcdInfoFid = open(os.path.join(CACHE, "info.0.json"), "w")
                xkcdInfoFid.write(currentJson)
                xkcdInfoFid.close()

                # Clean-up
                urllib.request.urlcleanup()

            self.TITLE = currentInfo["title"]
            self.NUMBER = currentInfo["num"]
            self.IMG = currentInfo["img"]
            self.DAY = currentInfo["day"]
            self.MONTH = currentInfo["month"]
            self.YEAR = currentInfo["year"]
        except urllib.error.URLError:
            print("ERR: Could not open URL")
        except Exception as err:
            # print("ERR: Unexpected online error: %s" % err)
            traceback.print_exc()

    def getImage(self):
        return open(os.path.join(CACHE, "xkcd.png"), "r")

    def getFormattedImage(self):
        titleFont = ImageFont.truetype("DejaVuSans.ttf", 12)

        # Load image and determine scaling
        img = Image.open(os.path.join(CACHE, "xkcd.png"))
        (imgx, imgy) = img.size
        quotient = max(imgx/display.resolution[0], imgy/(display.resolution[1]-HEADER))
        (width, height) = (int(imgx/quotient), int(imgy/quotient))

        # Scale and center image in display
        scaledImg = img.resize((int(imgx/quotient), int(imgy/quotient)), Image.LANCZOS)
        imgOut = Image.new("RGB", display.resolution, (255, 255, 255))
        imgOut.paste(scaledImg, (int((display.resolution[0] - scaledImg.size[0])/2), int(HEADER + (display.resolution[1] - scaledImg.size[1])/2)))
        draw = ImageDraw.Draw(imgOut)
        title = "XKCD - %s" % self.TITLE
        _, _, txtx, _ = draw.textbbox((0,0), title, font=titleFont)
        draw.text((int((display.resolution[0] - txtx)/2), 0), title, display.BLACK, font=titleFont)

        # Clean-up & return
        img.close()
        return imgOut

    def displayImage(self):
        if self.DISPLAY is None:
            return

        # Update display with image
        display.set_image(self.getFormattedImage())
        display.show()

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


  XkcdComic = XkcdClass(display)
  XkcdComic.displayImage()

"""
  # Format XKCD image for display steps:
  # - Open XCKD image
  # - get original size
  # - get display size
  # ? Should the title be displayed/save space for the title
  # * need to maintain original image aspect ratio
  # - find the larger quotient of original/display
  # - divide original (both dimensions) by quotient
  # - crop
"""
