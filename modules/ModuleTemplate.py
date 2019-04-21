import gettext
import logging
from modules.WeatherModule import WeatherModule, Utils


class YourModuleClass(WeatherModule):
    def __init__(self, fonts, language, units, config):
        super().__init__(fonts, language, units, config)
        # check config if needed

    def draw(self, screen, weather, updated):
        self.clear_surface()
        # draw module to screen
        self.update_screen(screen)
