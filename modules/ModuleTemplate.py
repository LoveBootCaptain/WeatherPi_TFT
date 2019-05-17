# pylint: disable=invalid-name
""" External module template class
"""

from modules.WeatherModule import WeatherModule


class ModuleTemplate(WeatherModule):
    """Module template
    """

    # def __init__(self, fonts, location, language, units, config):
    #    super().__init__(fonts, location, language, units, config)
    #    # check config if needed

    def draw(self, screen, weather, updated):
        if weather is None or not updated:
            return

        self.clear_surface()
        # draw module to screen
        self.update_screen(screen)
