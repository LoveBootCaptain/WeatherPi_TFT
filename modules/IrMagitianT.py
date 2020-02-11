# pylint: disable=invalid-name, broad-except
"""irMagician-T module
"""

import logging
import serial
from modules.TemparatureModule import TemparatureModule
from modules.WeatherModule import Utils


def read_temperature(correction_value):
    """Read tempareture from device
    """
    try:
        # send Temperature command and save reply
        with serial.Serial("/dev/ttyACM0", 9600, timeout=1) as s:
            s.write(b"T\r\n")
            value = s.readline().strip()
            s.readline()  # discard the status

        # Celsius conversion and correction
        celsius = ((5.0 / 1024.0 * float(value)) - 0.4) / 0.01953
        celsius = round(celsius + correction_value, 1)
        logging.info("Celsius: %s", celsius)
        return celsius, None

    except Exception as e:
        logging.error(e, exc_info=True)
        return None


class IrMagitianT(TemparatureModule):
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
        "correction_value": -10,
        "graph_rect": [x, y, width, height]
      }
     }
    """

    def __init__(self, fonts, location, language, units, config):
        super().__init__(fonts, location, language, units, config)
        self.correction_value = float(config["correction_value"])
        if self.correction_value is None:
            raise ValueError(__class__.__name__)
        self.humidities = None

        # start sensor thread
        self.start_sensor_thread(20, read_temperature, [self.correction_value])

    def draw(self, screen, weather, updated):
        (celsius, _humidity, data_changed) = self.get_sensor_value()
        if not data_changed:
            return

        temparature = Utils.temperature_text(
            celsius if self.units == "si" else Utils.fahrenheit(celsius),
            self.units)

        message = temparature
        for size in ("large", "medium", "small"):
            w, h = self.text_size(message, size, bold=True)
            if w <= self.rect.width and 20 + h <= self.rect.height:
                break

        self.clear_surface()
        self.draw_text(_("Indoor"), (0, 0), "small", "gray")
        self.draw_text(message, (0, 20), size, "white", bold=True)
        self.update_screen(screen)

        # plot the graph if necessary
        self.plot_graph(screen)
