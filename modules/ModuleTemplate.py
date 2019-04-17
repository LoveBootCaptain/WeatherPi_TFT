import gettext
import logging
from modules.WeatherModule import WeatherModule, Utils


class YourModuleClass(WeatherModule):
    def __init__(self, screen, fonts, language, units, config):
        super().__init__(screen, fonts, language, units, config)
        # check config if needed

    def draw(self, weather):
        # draw module to screen
        pass
