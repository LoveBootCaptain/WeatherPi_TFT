import Adafruit_DHT
import importlib
import logging
import sys
from modules.WeatherModule import WeatherModule, Utils

# Adafruit temperature/humidity sensor module
#
# example config:
# {
#   "module": "DHT",
#   "config": {
#     "rect": [x, y, width, height],
#     "sensor": "DHT11",
#     "pin": 14
#   }
#  }
#
class DHT(WeatherModule):
    sensors = {
        "DHT11": Adafruit_DHT.DHT11,
        "DHT22": Adafruit_DHT.DHT22,
        "AM2302": Adafruit_DHT.AM2302
    }

    def __init__(self, screen, fonts, language, units, config):
        super().__init__(screen, fonts, language, units, config)
        self.pin = config["pin"]
        if config["sensor"] in DHT.sensors:
            self.sensor = DHT.sensors[config["sensor"]]
        else:
            logging.error("sensor {} not supported")
            self.sensor = None

    def draw(self, weather):
        if not self.sensors:
            return

        humidity, celsius = Adafruit_DHT.read_retry(self.sensor, self.pin)
        color = Utils.heat_color(celsius, humidity, "si")

        message = "{} {}".format(Utils.temparature_text(
            celsius, self.units), Utils.percentage_text(humidity))
        logging.debug("{} {} {}".format(__class__, message, color))

        self.draw_text(_("Indoor"), "regular", "small", "white", (5, 5))
        self.draw_text(message, "regular", "small", color, (5, 25))
