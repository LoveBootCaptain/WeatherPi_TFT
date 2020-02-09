# pylint: disable=invalid-name, too-many-locals, broad-except
"""Adafruit temperature/humidity sensor module
"""

import logging
import Adafruit_DHT
from modules.TemparatureModule import TemparatureModule
from modules.WeatherModule import Utils


def read_temperature_and_humidity(sensor, pin, correction_value):
    """Read tempareture and humidity from sensor
    """
    try:
        humidity, celsius = Adafruit_DHT.read_retry(sensor, pin)
        celsius = round(celsius + correction_value, 1)
        logging.info("Celsius: %s Humidity: %s", celsius, humidity)
        return celsius, humidity

    except Exception as e:
        logging.error(e, exc_info=True)
        return None


class DHT(TemparatureModule):
    """
    Adafruit temperature/humidity sensor module

    This module gets data form DHT11, DHT22 and AM2302 sensors and display it
    in Heat Index color.

    example config:
    {
      "module": "DHT",
      "config": {
        "rect": [x, y, width, height],
        "sensor": "DHT11",
        "pin": 14,
        "correction_value": -8,
        "graph_rect": [x, y, width, height]
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

        if config["sensor"] in DHT.sensors:
            self.sensor = DHT.sensors[config["sensor"]]
        if isinstance(config["pin"], int):
            self.pin = config["pin"]
        self.correction_value = float(config["correction_value"])
        if not (self.sensor and self.pin and self.correction_value):
            raise ValueError(__class__.__name__)

        # start sensor thread
        self.start_sensor_thread(
            20, read_temperature_and_humidity,
            [self.sensor, self.pin, self.correction_value])

    def draw(self, screen, weather, updated):
        (celsius, humidity, data_changed) = self.get_sensor_value()
        if not data_changed:
            return

        if self.graph_rect is not None:
            self.plotting(screen)

        color = Utils.heat_color(celsius, humidity, "si")
        temperature = Utils.temperature_text(
            celsius if self.units == "si" else Utils.fahrenheit(celsius),
            self.units)
        humidity = Utils.percentage_text(humidity)

        for size in ("large", "medium", "small"):
            # Horizontal
            message1 = "{}  {}".format(temperature, humidity)
            message2 = None
            w, h = self.text_size(message1, size, bold=True)
            if w <= self.rect.width and 20 + h <= self.rect.height:
                break

            # Vertical
            message1 = temperature
            message2 = humidity if humidity else None
            w1, h1 = self.text_size(message1, size, bold=True)
            w2, h2 = self.text_size(message2, size, bold=True)
            if max(w1,
                   w2) <= self.rect.width and 20 + h1 + h2 <= self.rect.height:
                break

        self.clear_surface()
        self.draw_text(_("Indoor"), (0, 0), "small", "gray")
        (w, h) = self.draw_text(message1, (0, 20), size, color, bold=True)
        if message2:
            self.draw_text(message2, (0, 20 + h), size, color, bold=True)
        self.update_screen(screen)
