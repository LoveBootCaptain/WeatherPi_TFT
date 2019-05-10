import gettext
import logging
import serial
import sys
from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer


def read_temperature(units, correction_value):
    try:
        # send Temperature command and save reply
        s = serial.Serial("/dev/ttyACM0", 9600, timeout=1)
        s.write(b"T\r\n")
        value = str(s.readline()).strip()
        status = str(s.readline()).strip()
        s.close()

        # Celsius conversion and correction
        celsius = ((5.0 / 1024.0 * float(value)) - 0.4) / 0.01953
        celsius = round(celsius + correction_value, 1)

        temperature = celsius if units == "si" else Utils.fahrenheit(celsius)
        logging.debug("Temperature: {}".format(temparature))
        return temperature

    except Exception as e:
        logging.error("read_temperature failed: {}".format(e))
        return None


class IrMagitianT(WeatherModule):
    """
    irMagician-T module

    This module gets temparature from irMagician-T and display it.

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

        if isinstance(config["correction_value"], int):
            self.correction_value = config["correction_value"]
        if self.correction_value is None:
            raise ValueError(__class__.__name__)

        # start sensor thread
        self.timer_thread = RepeatedTimer(20, read_temperature,
                                          [self.units, self.correction_value])
        self.timer_thread.start()
        logging.info("{}: sensor thread started".format(__class__.__name__))

    def quit(self):
        if self.timer_thread:
            logging.info("{}: sensor thread stopped".format(
                __class__.__name__))
            self.timer_thread.quit()

    def draw(self, screen, weather, updated):
        if self.timer_thread is None:
            return

        temperature = self.timer_thread.result()
        if temperature is None:
            logging.info("{}: No data from sensor".format(__class__.__name__))
            return

        message = Utils.temparature_text(temperature, self.units)
        for size in ("large", "medium", "small"):
            w, h = self.text_size(message, size, bold=True)
            if w <= self.rect.width and 20 + h <= self.rect.height:
                break

        self.clear_surface()
        self.draw_text(_("Indoor"), (0, 0), "small", "white")
        self.draw_text(message, (0, 20), size, "white", bold=True)
        self.update_screen(screen)
