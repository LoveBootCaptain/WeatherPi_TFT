import gettext
import RPi.GPIO as GPIO
import logging
import sys
from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer

# PIR motion sensor module
#
# example config:
# {
#   "module": "PIR",
#   "config": {
#     "pin": 26,
#     "power_save_delay": 300
#   }
# }
#


class PIR(WeatherModule):
    def __init__(self, fonts, location, language, units, config):
        self.pin = None
        self.power_save_delay = None
        self.power_save_timer = 0

        if isinstance(config["pin"], int):
            self.pin = config["pin"]
        if isinstance(config["power_save_delay"], int):
            self.power_save_delay = config["power_save_delay"]
        if self.pin is None or self.power_save_delay is None:
            raise ValueError(__class__.__name__)

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)

    def draw(self, screen, weather, updated):
        if GPIO.input(self.pin):
            Utils.display_wakeup()
            self.power_save_timer = 0
        else:
            self.power_save_timer += 1
            if self.power_save_timer > self.power_save_delay:
                logging.info("{}: screen sleep.".format(__class__.__name__))
                Utils.display_sleep()
