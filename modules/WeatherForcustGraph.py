# pylint: disable=invalid-name
""" Weather forcust graph class
"""

import datetime
from modules.WeatherModule import WeatherModule, Utils
from modules.GraphUtils import GraphUtils


def adjust_unit(values, condition, units):
    """adjust values units
    """
    value = values[condition]
    if condition == "time":
        return datetime.datetime.fromtimestamp(value)
    value = float(value)
    if condition in ("temparature", "apparentTemperature"):
        return value if units == "si" else Utils.fahrenheit(value)
    if condition == "humidity":
        return value * 100
    if condition == "windSpeed":
        return round(Utils.kilometer(value) if units == "si" else value, 1)
    return value


class WeatherForcustGraph(WeatherModule):
    """
    Weather forcust graph Module

    This module plots weather condition data for the next 48 hours.
    When two weather conditions are specified, a two-axis graph is plotted.

    example config:
    {
      "module": "WeatherForcustGraph",
      "config": {
        "rect": [x, y, width, height],
        "conditions": ["temperature", "humidity"]
      }
     }

    Available weather conditions is following:
        temperature, apparentTemperature, dewPoint, humidity,
        pressure, windSpeed, uvIndex, ozone

        https://darksky.net/dev/docs
    """
    CONDITIONS = [
        "temperature", "apparentTemperature", "dewPoint", "humidity",
        "pressure", "windSpeed", "uvIndex", "ozone"
    ]

    def __init__(self, fonts, location, language, units, config):
        super().__init__(fonts, location, language, units, config)
        self.block = "hourly"
        self.condition1 = None
        self.condition2 = None
        if "conditions" in config:
            conditions = config["conditions"]
            length = len(conditions)
            if length > 0:
                if conditions[0] not in self.CONDITIONS:
                    raise ValueError(__class__.__name__)
                self.condition1 = conditions[0]
            if length > 1:
                if conditions[1] not in self.CONDITIONS:
                    raise ValueError(__class__.__name__)
                self.condition2 = conditions[1]

    def draw(self, screen, weather, updated):
        if weather is None or not updated:
            return

        data = weather[self.block]["data"]
        times = list(map(lambda x: adjust_unit(x, "time", self.units), data))
        if self.condition1:
            y1 = list(
                map(lambda x: adjust_unit(x, self.condition1, self.units),
                    data))
            ylabel1 = "".join(
                map(lambda x: x if x.islower() else " " + x,
                    self.condition1)).capitalize()
        else:
            y1 = ylabel1 = None
        if self.condition2:
            y2 = list(
                map(lambda x: adjust_unit(x, self.condition2, self.units),
                    data))
            ylabel2 = "".join(
                map(lambda x: x if x.islower() else " " + x,
                    self.condition2)).capitalize()
        else:
            y2 = ylabel2 = None

        self.clear_surface()
        GraphUtils.set_font(self.fonts["name"])
        GraphUtils.plot_2axis_graph(screen, self.surface, self.rect, times, y1,
                                    ylabel1, y2, ylabel2)
