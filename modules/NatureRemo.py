# pylint: disable=invalid-name, too-many-locals, broad-except
"""NatureRemo module
"""

import logging
import requests
from modules.TemparatureModule import TemparatureModule
from modules.WeatherModule import Utils


def read_temperature_and_humidity(token, name, correction_value):
    """Read tempareture and humidity from device
    """
    try:
        response = requests.get("https://api.nature.global/1/devices",
                                headers={
                                    "Authorization": "Bearer {}".format(token),
                                    "accept": "application/json"
                                })
        response.raise_for_status()

        celsius = humidity = None
        for device in response.json():
            if device["name"] == name:
                events = device["newest_events"]
                if "te" in events:
                    celsius = round(float(events["te"]["val"]), 1)
                    celsius = round(celsius + correction_value, 1)
                if "hu" in events:
                    humidity = events["hu"]["val"]
                break
        logging.info("Celsius: %s Humidity: %s", celsius, humidity)
        return celsius, humidity

    except Exception as e:
        logging.error(e, exc_info=True)
        return None


class NatureRemo(TemparatureModule):
    """
    Nature Remo module

    This module gets temperature and humidity from Nature Remo/Remo mini and
    displayed.
    Nature Remo/Remo miniに搭載された温湿度センサ()から温湿度を取得し表示します。
    （湿度が計測できるのはRemoのみ）

    example config:
    {
      "module": "NatureRemo",
      "config": {
        "rect": [x, y, width, height],
        "token": "<access tokens to access Nature API>"
        "name": "<device name>",
        "correction_value": 0.2,
        "graph_rect": [x, y, width, height]
      }
     }
    """

    def __init__(self, fonts, location, language, units, config):
        super().__init__(fonts, location, language, units, config)
        self.token = config["token"]
        self.name = config["name"]
        self.correction_value = float(config["correction_value"])
        if self.correction_value is None:
            raise ValueError(__class__.__name__)
        self.humidities = None

        # start sensor thread
        self.start_sensor_thread(
            20, read_temperature_and_humidity,
            [self.token, self.name, self.correction_value])

    def draw(self, screen, weather, updated):
        (celsius, humidity, data_changed) = self.get_sensor_value()
        if not data_changed:
            return

        if self.graph_rect is not None:
            self.plotting(screen)

        color = Utils.heat_color(celsius, humidity,
                                 "si") if humidity else "white"
        temperature = Utils.temperature_text(
            celsius if self.units == "si" else Utils.fahrenheit(celsius),
            self.units)
        humidity = Utils.pressure_text(humidity) if humidity else None

        for size in ("large", "medium", "small"):
            # Horizontal
            message1 = "{} {}".format(temperature, humidity)
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
