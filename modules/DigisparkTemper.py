# pylint: disable=invalid-name, broad-except, bare-except
"""DigisparkTemper (usb temperature/humidity sensor) module
"""

import json
import logging
import time

from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer
from modules.usbdevice import ArduinoUsbDevice


def read_temperature_and_humidity(correction_value):
    """Read tempareture and humidity from sensor
    """

    def read_line(device):
        line = ""
        while True:
            try:
                c = chr(device.read())
                if c == '\r':
                    return line
                line += c
            except:
                time.sleep(0.5)

    try:
        device = ArduinoUsbDevice(idVendor=0x16c0, idProduct=0x05df)
        line = read_line(device).strip()
        data = json.loads(line)

        humidity = data["Humidity"]
        celsius = round(data["Temperature"] + correction_value, 1)

        logging.info("Celsius: %s Humidity: %s", celsius, humidity)
        return humidity, celsius

    except Exception as e:
        if line:
            logging.error("DigisparkTemper: %s", line)
        logging.error(e, exc_info=True)
        return None


class DigisparkTemper(WeatherModule):
    """
    DigisparkTemper (USB temperature/humidity sensor) module

    This module gets data form DigisparkTemper and display it in
    Heat Index color.

    example config:
    {
      "module": "DigisparkTemper",
      "config": {
        "rect": [x, y, width, height],
        "correction_value": -1
      }
     }
    """

    def __init__(self, fonts, location, language, units, config):
        super().__init__(fonts, location, language, units, config)
        self.correction_value = None
        self.timer_thread = None
        self.last_hash_value = None

        self.correction_value = float(config["correction_value"])
        if self.correction_value is None:
            raise ValueError(__class__.__name__)

        # start sensor thread
        self.timer_thread = RepeatedTimer(10, read_temperature_and_humidity,
                                          [self.correction_value])
        self.timer_thread.start()

    def quit(self):
        if self.timer_thread:
            self.timer_thread.quit()

    def draw(self, screen, weather, updated):
        # No result yet
        result = self.timer_thread.get_result()
        if result is None:
            logging.info("%s: No data from sensor", __class__.__name__)
            return

        # Has the value changed
        hash_value = self.timer_thread.get_hash_value()
        if self.last_hash_value == hash_value:
            return
        self.last_hash_value = hash_value

        (humidity, celsius) = result

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
        self.draw_text(_("Indoor"), (0, 0), "small", "white")
        (w, h) = self.draw_text(message1, (0, 20), size, color, bold=True)
        if message2:
            self.draw_text(message2, (0, 20 + h), size, color, bold=True)
        self.update_screen(screen)
