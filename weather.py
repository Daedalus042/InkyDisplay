import os
import glob
import json
import time
import netifaces

# Import dependancies
from PIL import Image, ImageDraw, ImageFont
from font_fredoka_one import FredokaOne
from inky import eeprom
from inky import phat
from PiSugar import PiSugarConnect

# Import secrets
from secrets import Secrets

# Debug boolean
DEBUG = True

# Requirements for Weather geolocation
try:
    import requests
except ImportError:
    exit("This script requires the requests module\nInstall with: sudo pip install requests")

try:
    import geocoder
except ImportError:
    exit("This script requires the geocoder module\nInstall with: sudo pip install geocoder")

# Get the current path
PATH = os.path.dirname(__file__)
CACHE = "/home/" + Secrets.username + "/.cache/Inky/"

class WeatherManagerClass:
    # Details to customise your weather display

    CITY = Secrets.city
    COUNTRYCODE = Secrets.countrycode
    WARNING_TEMP = 25.0

    def __init__(self, display):
        self.display = display


    # Convert a city name and country code to latitude and longitude
    def get_coords(self, address):
        g = geocoder.arcgis(address)
        coords = g.latlng
        return coords


    # Query OpenMeteo (https://open-meteo.com) to get current weather data
    def get_weather(self, address):
        coords = self.get_coords(address)
        weather = {}
        try:
            res = requests.get("https://api.open-meteo.com/v1/forecast?latitude=" + str(coords[0]) + "&longitude=" + str(coords[1]) + "&current_weather=true&timezone=America%2FChicago&timeformat=unixtime")
        except:
            try:
                print("ERR: Couldn't connect to wifi, trying bluetooth tethering")
                os.system("bluetoothctl connect %s" % Secrets.deviceid)
                time.sleep(1.0)
                os.system("busctl call org.bluez /org/bluez/hci0/dev_%s org.bluez.Network1 Connect s nap" % Secrets.deviceid)
                time.sleep(0.5)
                os.system("sudo dhclient -v bnep0")
                time.sleep(0.5)
                res = requests.get("https://api.open-meteo.com/v1/forecast?latitude=" + str(coords[0]) + "&longitude=" + str(coords[1]) + "&current_weather=true&timezone=America%2FChicago&timeformat=unixtime")
            except:
                res.status_code = None
                print("ERR: couldn't tether via bluetooth")
                if DEBUG:
                    print(netifaces.interfaces())

        # If able to connect successfully, load from internet
        # If new day, update forecast cache
        forecastFid = open(os.path.join(CACHE, "forecast.json"), "r")
        cachedForecast = json.load(forecastFid)
        forecastFid.close()
        if res.status_code == 200:
            rawInfo = json.loads(res.text)
            current = rawInfo["current_weather"]
            weather["current"] = True
            weather["temperature"] = current["temperature"]
            weather["windspeed"] = current["windspeed"]
            weather["weathercode"] = current["weathercode"]
            currentDay = int(time.strftime('%d', time.localtime(current["time"])))
            cachedDay = int(time.strftime('%d', time.localtime(cachedForecast["time"][0])))
            if (currentDay != cachedDay) or (int(currentDay["time"]) - int(cachedForecast["time"][0]) > 86400):
                # Present day is not the same calendar day as cached day, or interval between current and
                # cached is more than one day to account for sitting off for exactly one month.
                print("Today's forcast is out of date. Updating now")
                res = requests.get("https://api.open-meteo.com/v1/forecast?latitude=" + str(coords[0]) + "&longitude=" + str(coords[1]) + "&daily=weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min&timezone=America%2FChicago&forecast_days=1&timeformat=unixtime")
                rawInfo = json.loads(res.text)
                forecast = rawInfo["daily"]
                forecastFid = open(os.path.join(CACHE, "forecast.json"), "w")
                forecastFid.write(json.dumps(forecast))
                forecastFid.close()
        else:
            weather["current"] = False
            weather["temperature_max"] = cachedForecast["temperature_2m_max"][0]
            weather["temperature_min"] = cachedForecast["temperature_2m_min"][0]
            weather["apparent_temperature_max"] = cachedForecast["apparent_temperature_max"][0]
            weather["apparent_temperature_min"] = cachedForecast["apparent_temperature_min"][0]
            weather["weathercode"] = cachedForecast["weather_code"][0]
        return weather


    def create_mask(self, source):
        """Create a transparency mask.

        Takes a paletized source image and converts it into a mask
        permitting all the colours supported by Inky pHAT (0, 1, 2)
        or an optional list of allowed colours.

        :param mask: Optional list of Inky pHAT colours to allow.

        """
        mask=(self.display.WHITE, self.display.BLACK, self.display.RED)
        mask_image = Image.new("1", source.size)
        w, h = source.size
        for x in range(w):
            for y in range(h):
                p = source.getpixel((x, y))
                if p in mask:
                    mask_image.putpixel((x, y), 255)

        return mask_image

    def doWeatherUpdate(self):
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
        location_string = "{city}, {countrycode}".format(city=self.CITY, countrycode=self.COUNTRYCODE)
        weather = self.get_weather(location_string)

        PiSugar = PiSugarConnect()

        # Create a new canvas to draw on
        img = Image.open(os.path.join(PATH, "resources/Background_250x122.png")).resize(self.display.resolution)
        draw = ImageDraw.Draw(img)

        # Load the FredokaOne font
        font = ImageFont.truetype(FredokaOne, 22)

        # Write text with weather values to the canvas
        datetime = time.strftime('%a %b %d %H:%M')
        draw.text((38, 14), datetime, self.display.WHITE, font=font)

        if weather["current"]:
            wifiIcon = Image.open(os.path.join(PATH, "resources/icons/system/WifiGood1.png"))
            temperature = weather["temperature"]
            windspeed = weather["windspeed"]
            weathercode = weather["weathercode"]

            draw.text((83, 43), "T", self.display.WHITE, font=font)
            draw.text((103, 43), "{}°C".format(temperature), self.display.WHITE if temperature < self.WARNING_TEMP else self.display.RED, font=font)

            draw.text((80, 72), "W", self.display.WHITE, font=font)
            draw.text((103, 72), "{}kmh".format(windspeed), self.display.WHITE, font=font)

        else:
            wifiIcon = Image.open(os.path.join(PATH, "resources/icons/system/WifiBad1_thick.png"))
            print("Warning, no weather information found!")

            high = weather["temperature_max"]
            low = weather["temperature_min"]
            feelsLikeHigh = weather["apparent_temperature_max"]
            feelsLikeLow = weather["apparent_temperature_min"]
            weathercode = weather["weathercode"]

            draw.text((83, 43), "Temp", self.display.WHITE, font=font)
            draw.text((123, 43), "{} | {}°C".format(high, low), self.display.WHITE if high < self.WARNING_TEMP else self.display.RED, font=font)

            draw.text((80, 72), "Feel", self.display.WHITE, font=font)
            draw.text((123, 72), "{} | {}°C".format(feelsLikeHigh, feelsLikeLow), self.display.WHITE, font=font)

        for icon in icon_map:
            if weathercode in icon_map[icon]:
                weather_icon = icon
                break

        # Draw the current weather icon over the backdrop
        if weather_icon is not None:
            img.paste(icons[weather_icon], (30, 45), masks[weather_icon])

        else:
            draw.text((45, 55), "?", self.display.RED, font=font)

        # Add Wifi icon
        img.paste(wifiIcon, (170, 1), self.create_mask(wifiIcon))

        # Add Battery icon & number (TODO)
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
        img.paste(battIcon, (190, 1), self.create_mask(battIcon))

        # Load our icon files and generate masks
        for icon in glob.glob(os.path.join(PATH, "resources/icons/weather/icon-*.png")):
            icon_name = icon.split("icon-")[1].replace(".png", "")
            icon_image = Image.open(icon)
            icons[icon_name] = icon_image
            masks[icon_name] = self.create_mask(icon_image)

        # Draw lines to frame the weather data
        draw.line((75, 41, 75, 100))       # Vertical line
        draw.line((27, 41, 222, 41))      # Horizontal top line
        draw.line((75, 70, 222, 70))      # Horizontal middle line
        draw.line((207, 70, 207, 70), 2)  # Red seaweed pixel :D

        # display the weather data on Inky pHAT
        self.display.set_image(img)
        self.display.show()

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
    WeatherManager = WeatherManagerClass(display)

    try:
        display.set_border(display.BLACK)
    except NotImplementedError:
        pass

    WeatherManager.doWeatherUpdate()
