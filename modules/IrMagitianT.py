import gettext
import hashlib
import logging
import serial
import sys
from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer


def read_temperature(correction_value):
    try:
        # send Temperature command and save reply
        with serial.Serial("/dev/ttyACM0", 9600, timeout=1) as s:
            s.write(b"T\r\n")
            value = s.readline().strip()
            status = s.readline().strip()

        # Celsius conversion and correction
        celsius = ((5.0 / 1024.0 * float(value)) - 0.4) / 0.01953
        celsius = round(celsius + correction_value, 1)
        hash = hashlib.md5(str(celsius).encode()).hexdigest()
        logging.info("Celsius: {}".format(celsius))
        return celsius, hash

    except Exception as e:
        logging.error(e, exc_info=True)
        return None


class IrMagitianT(WeatherModule):
    """
    irMagician-T module

    This module gets temparature from the temperature sensor (Microchip MCP -97001)
    installed in the infrared remote control system "irMagician-T" and displayed.

    赤外線リモコンシステムirMagician-Tに搭載された温度センサ(Microchip MCP-97001)から温度を取得し表示します。

    example config:
    {
      "module": "IRM",
      "config": {
        "rect": [x, y, width, height],
        "correction_value": -10
      }
     }
    """

    def __init__(self, fonts, location, language, units, config):
        super().__init__(fonts, location, language, units, config)
        self.correction_value = None
        self.timer_thread = None
        self.hash = None

        if isinstance(config["correction_value"], int):
            self.correction_value = config["correction_value"]
        if self.correction_value is None:
            raise ValueError(__class__.__name__)

        # start sensor thread
        self.timer_thread = RepeatedTimer(20, read_temperature,
                                          [self.correction_value])
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

        (celsius, hash) = result
        if self.hash == hash:
            return
        self.hash = hash

        temparature = Utils.temperature_text(
            celsius if self.units == "si" else Utils.fahrenheit(celsius),
            self.units)

        message = temparature
        for size in ("large", "medium", "small"):
            w, h = self.text_size(message, size, bold=True)
            if w <= self.rect.width and 20 + h <= self.rect.height:
                break

        self.clear_surface()
        self.draw_text(_("Indoor"), (0, 0), "small", "white")
        self.draw_text(message, (0, 20), size, "white", bold=True)
        self.update_screen(screen)
