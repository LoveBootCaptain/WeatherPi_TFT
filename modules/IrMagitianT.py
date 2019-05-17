# pylint: disable=invalid-name, broad-except
"""irMagician-T module
"""

import logging
import serial
from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer


def read_temperature(correction_value):
    """Read tempareture from device
    """
    try:
        # send Temperature command and save reply
        with serial.Serial("/dev/ttyACM0", 9600, timeout=1) as s:
            s.write(b"T\r\n")
            value = s.readline().strip()
            s.readline().strip()  # discard the status

        # Celsius conversion and correction
        celsius = ((5.0 / 1024.0 * float(value)) - 0.4) / 0.01953
        celsius = round(celsius + correction_value, 1)
        logging.info("Celsius: %s", celsius)
        return celsius

    except Exception as e:
        logging.error(e, exc_info=True)
        return None


class IrMagitianT(WeatherModule):
    """
    irMagician-T module

    This module gets temparature from the temperature sensor (Microchip
    MCP -97001) installed in the infrared remote control system "irMagician-T"
    and displayed.

    赤外線リモコンシステムirMagician-Tに搭載された温度センサ(Microchip MCP-97001)から
    温度を取得し表示します。

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
        self.last_hash_value = None

        self.correction_value = float(config["correction_value"])
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

        celsius = result

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
