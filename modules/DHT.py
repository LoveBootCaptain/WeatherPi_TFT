import Adafruit_DHT
import gettext
import logging
import sys
from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer


# Adafruit temperature/humidity sensor module
#
# example config:
# {
#   "module": "DHT",
#   "config": {
#     "rect": [x, y, width, height],
#     "sensor": "DHT11",
#     "pin": 14,
#     "correction_value": -8
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
        self.sensor = None
        self.pin = None
        self.correction_value = None
        self.timer_thread = None

        if config["sensor"] in DHT.sensors:
            self.sensor = DHT.sensors[config["sensor"]]
        if isinstance(config["pin"], int):
            self.pin = config["pin"]
        if isinstance(config["correction_value"], int):
            self.correction_value = config["correction_value"]
        if self.sensor is None or self.pin is None or self.correction_value is None:
            raise ValueError(__class__.__name__)

        # start sensor thread
        self.timer_thread = RepeatedTimer(
            10, Adafruit_DHT.read_retry, [self.sensor, self.pin])
        self.timer_thread.start()
        logging.info("{}: sensor thread started".format(__class__.__name__))

    def quit(self):
        if self.timer_thread:
            logging.info("{}: sensor thread stopped".format(
                __class__.__name__))
            self.timer_thread.quit()

    def draw(self, weather):
        if self.timer_thread is None:
            return
        result = self.timer_thread.result()
        if result is None:
            return

        (humidity, celsius) = result
        if humidity is None or celsius is None:
            logging.info("{}: No data from sensor".format(__class__.__name__))
            return

        # workaround:
        #　Adjusted because the temperature to be measured is too high
        celsius = celsius + self.correction_value
        color = Utils.heat_color(celsius, humidity, "si")

        message = "{} {}".format(Utils.temparature_text(
            celsius, self.units), Utils.percentage_text(humidity))
        logging.debug("{} {} {}".format(__class__.__name__, message, color))

        self.draw_text(_("Indoor"), "regular", "small", "white", (5, 5))
        self.draw_text(message, "regular", "small", color, (5, 25))
