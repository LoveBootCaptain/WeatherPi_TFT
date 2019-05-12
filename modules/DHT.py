import Adafruit_DHT
import gettext
import logging
import sys
from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer


class DHT(WeatherModule):
    """
    Adafruit temperature/humidity sensor module

    This module gets data form DHT11, DHT22 and AM2302 sensors and display it in
    Color Index color.

    example config:
    {
      "module": "DHT",
      "config": {
        "rect": [x, y, width, height],
        "sensor": "DHT11",
        "pin": 14,
        "correction_value": -8
      }
     }
    """
    sensors = {
        "DHT11": Adafruit_DHT.DHT11,
        "DHT22": Adafruit_DHT.DHT22,
        "AM2302": Adafruit_DHT.AM2302
    }

    def __init__(self, fonts, location, language, units, config):
        super().__init__(fonts, location, language, units, config)
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
        self.timer_thread = RepeatedTimer(20, Adafruit_DHT.read_retry,
                                          [self.sensor, self.pin])
        self.timer_thread.start()

    def quit(self):
        if self.timer_thread:
            self.timer_thread.quit()

    def draw(self, screen, weather, updated):
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
        # Adjusted because the temperature to be measured is too high
        celsius = celsius + self.correction_value

        color = Utils.heat_color(celsius, humidity, "si")
        temparature = Utils.temparature_text(
            celsius if self.units == "si" else Utils.fahrenheit(celsius)
            self.units)
        humidity = Utils.percentage_text(humidity)

        logging.debug("{} {} {} {}".format(__class__.__name__, temparature,
                                           humidity, color))

        message = "{}  {}".format(temparature, humidity)
        for size in ("large", "medium", "small"):
            w, h = self.text_size(message, size, bold=True)
            if w <= self.rect.width and 20 + h <= self.rect.height:
                break

        self.clear_surface()
        self.draw_text(_("Indoor"), (0, 0), "small", "white")
        self.draw_text(message, (0, 20), size, color, bold=True)
        self.update_screen(screen)
