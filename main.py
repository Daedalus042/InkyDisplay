import os
import glob
import json
import time
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

# Get the current path
PATH = os.path.dirname(__file__)

# Requirements for Weather geolocation
try:
    import requests
except ImportError:
    exit("This script requires the requests module\nInstall with: sudo pip install requests")

try:
    import geocoder
except ImportError:
    exit("This script requires the geocoder module\nInstall with: sudo pip install geocoder")

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
    display.set_border(display.BLACK)
except NotImplementedError:
    pass

img = Image.open(os.path.join("/home/", Secrets.username, "repos/inky/examples/phat/resources/InkypHAT-250x122.png"))
display.set_image(img)
display.show()

# Details to customise your weather display

CITY = Secrets.city
COUNTRYCODE = Secrets.countrycode
WARNING_TEMP = 25.0

# Convert a city name and country code to latitude and longitude
def get_coords(address):
    g = geocoder.arcgis(address)
    coords = g.latlng
    return coords


# Query OpenMeteo (https://open-meteo.com) to get current weather data
def get_weather(address):
    coords = get_coords(address)
    weather = {}
    res = requests.get("https://api.open-meteo.com/v1/forecast?latitude=" + str(coords[0]) + "&longitude=" + str(coords[1]) + "&current_weather=true")
    if res.status_code == 200:
        j = json.loads(res.text)
        current = j["current_weather"]
        weather["temperature"] = current["temperature"]
        weather["windspeed"] = current["windspeed"]
        weather["weathercode"] = current["weathercode"]
        return weather
    else:
        return weather


def create_mask(source, mask=(display.WHITE, display.BLACK, display.RED)):
    """Create a transparency mask.

    Takes a paletized source image and converts it into a mask
    permitting all the colours supported by Inky pHAT (0, 1, 2)
    or an optional list of allowed colours.

    :param mask: Optional list of Inky pHAT colours to allow.

    """
    mask_image = Image.new("1", source.size)
    w, h = source.size
    for x in range(w):
        for y in range(h):
            p = source.getpixel((x, y))
            if p in mask:
                mask_image.putpixel((x, y), 255)

    return mask_image

def doWeatherUpdate():
    # Dictionaries to store our icons and icon masks in
    icons = {}
    masks = {}

    # This maps the weather code from Open Meteo
    # to the appropriate weather icons
    # Weather codes from https://open-meteo.com/en/docs
    icon_map = {
        "snow": [71, 73, 75, 77, 85, 86],
        "rain": [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82],
        "cloud": [1, 2, 3, 45, 48],
        "sun": [0],
        "storm": [95, 96, 99],
        "wind": []
    }

    # Placeholder variables
    windspeed = 0.0
    temperature = 0.0
    weather_icon = None

    # Get the weather data for the given location
    location_string = "{city}, {countrycode}".format(city=CITY, countrycode=COUNTRYCODE)
    weather = get_weather(location_string)

    if weather:
        temperature = weather["temperature"]
        windspeed = weather["windspeed"]
        weathercode = weather["weathercode"]

        for icon in icon_map:
            if weathercode in icon_map[icon]:
                weather_icon = icon
                break

    else:
        print("Warning, no weather information found!")

    # Create a new canvas to draw on
    img = Image.open(os.path.join(PATH, "resources/Background_250x122.png")).resize(display.resolution)
    draw = ImageDraw.Draw(img)

    # Load our icon files and generate masks
    for icon in glob.glob(os.path.join(PATH, "resources/icon-*.png")):
        icon_name = icon.split("icon-")[1].replace(".png", "")
        icon_image = Image.open(icon)
        icons[icon_name] = icon_image
        masks[icon_name] = create_mask(icon_image)

    # Load the FredokaOne font
    font = ImageFont.truetype(FredokaOne, 22)

    # Draw lines to frame the weather data
    draw.line((75, 41, 75, 100))       # Vertical line
    draw.line((27, 41, 222, 41))      # Horizontal top line
    draw.line((75, 70, 222, 70))      # Horizontal middle line
    draw.line((207, 70, 207, 70), 2)  # Red seaweed pixel :D

    # Write text with weather values to the canvas
    datetime = time.strftime("%d/%m %H:%M")

    draw.text((41, 14), datetime, display.WHITE, font=font)

    draw.text((80, 40), "T", display.WHITE, font=font)
    draw.text((100, 40), "{}°C".format(temperature), display.WHITE if temperature < WARNING_TEMP else display.RED, font=font)

    draw.text((80, 69), "W", display.WHITE, font=font)
    draw.text((100, 69), "{}kmh".format(windspeed), display.WHITE, font=font)

    # Draw the current weather icon over the backdrop
    if weather_icon is not None:
        img.paste(icons[weather_icon], (30, 50), masks[weather_icon])

    else:
        draw.text((30, 50), "?", display.RED, font=font)

    # Display the weather data on Inky pHAT
    display.set_image(img)
    display.show()


time.sleep(30)
doWeatherUpdate()
