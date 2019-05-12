import gettext
import json
import logging
import requests
import sys
from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer


def read_temperature_and_humidity(token, name):
    try:
        response = requests.get("https://api.nature.global/1/devices",
                                headers={
                                    "Authorization": "Bearer {}".format(token),
                                    "accept": "application/json"
                                })
        response.raise_for_status()

        temperature = humidity = None
        for device in response.json():
            if device["name"] == name:
                events = device["newest_events"]
                if "te" in events:
                    temperature = round(float(events["te"]["val"]), 1)
                if "hu" in events:
                    humidity = events["hu"]["val"]

        logging.debug("Temperature: {} Humidity: {}".format(
            temperature, humidity))
        return temperature, humidity

    except Exception as e:
        logging.error(e, exc_info=True)
        return None


class NatureRemo(WeatherModule):
    """
    Nature Remo module

    This module gets temparature and humidity from Nature Remo/Remo mini and displayed.
    Nature Remo/Remo miniに搭載された温湿度センサ()から温湿度を取得し表示します。
    （湿度が計測できるのはRemoのみ）

    example config:
    {
      "module": "IRM",
      "config": {
        "rect": [x, y, width, height],
        "token": "<access tokens to access Nature API>"
        "name": "<device name>"
      }
     }
    """

    def __init__(self, fonts, location, language, units, config):
        super().__init__(fonts, location, language, units, config)
        self.token = config["token"]
        self.name = config["name"]

        # start sensor thread
        self.timer_thread = RepeatedTimer(20, read_temperature_and_humidity,
                                          [self.token, self.name])
        self.timer_thread.start()

    def quit(self):
        if self.timer_thread:
            self.timer_thread.quit()

    def draw(self, screen, weather, updated):
        if self.timer_thread is None:
            return

        result = self.timer_thread.result()
        if result is None:
            logging.info("{}: No data from sensor".format(__class__.__name__))
            return
        temperature, humidity = result

        if self.units != "si":
            temperature = Utils.fahrenheit(temperature)

        message1 = Utils.temparature_text(temperature, self.units)
        message2 = Utils.pressure_text(humidity) if humidity else None
        color = Utils.heat_color(temperature, humidity,
                                 self.units) if humidity else "white"
        for size in ("large", "medium", "small"):
            w1, h1 = self.text_size(message1, size, bold=True)
            w2, h2 = self.text_size(message2, size, bold=True)
            if max(w1,
                   w2) <= self.rect.width and 20 + h1 + h2 <= self.rect.height:
                break

        self.clear_surface()
        self.draw_text(_("Indoor"), (0, 0), "small", "white")
        (w, h) = self.draw_text(message1, (0, 20), size, color, bold=True)
        if message2:
            self.draw_text(message2, (0, 20 + h), size, color, bold=True)
        self.update_screen(screen)
