# pylint: disable=invalid-name
""" Weather forcust graph class
"""

import datetime
from modules.WeatherModule import WeatherModule, Utils
from modules.GraphUtils import GraphUtils


def check_condition(block, condition):
    """check block and condition
    """
    hourly = [
        "precipIntensity", "precipProbability", "temperature",
        "apparentTemperature", "dewPoint", "humidity", "pressure", "windSpeed",
        "windGust", "cloudCover", "uvIndex", "visibility", "ozone"
    ]
    daily = [
        "precipIntensity", "precipIntensityMax", "precipProbability",
        "temperatureHigh", "temperatureLow", "apparentTemperatureHigh",
        "apparentTemperatureLow", "dewPoint", "humidity", "pressure",
        "windSpeed", "windGust", "cloudCover", "uvIndex", "uvIndexTime",
        "visibility", "ozone", "temperatureMin", "temperatureMax",
        "apparentTemperatureMin", "apparentTemperatureMax"
    ]
    if condition is not None:
        if block == "hourly":
            if condition not in hourly:
                return False
        elif block == "daily":
            if condition not in daily:
                return False
        else:
            return False
    return True


def adjust_unit(values, condition, units):
    """adjust values units
    """
    value = values[condition]
    if condition == "time":
        return datetime.datetime.fromtimestamp(value)
    value = float(value)
    if "temperature" in condition.lower() or condition == "dewPoint":
        return value if units == "si" else Utils.fahrenheit(value)
    if condition == "humidity":
        return value * 100
    if condition in ("windSpeed", "windGust"):
        return round(Utils.kilometer(value) if units == "si" else value, 1)
    return value


class WeatherForcustGraph(WeatherModule):
    """
    Weather forcust graph Module

    This module plots weather condition data for the next 48 hours or 7 days.
    When two weather conditions are specified, a two-axis graph is plotted.

    example config:
    {
      "module": "WeatherForcustGraph",
      "config": {
        "rect": [x, y, width, height],
        "block": "hourly",
        "conditions": ["temperature", "humidity"]
      }
     }

    Available weather conditions is following:
        hourly:
            temperature, apparentTemperature, dewPoint, humidity,
            pressure, windSpeed, uvIndex, ozone
        daily:
            precipIntensity, precipIntensityMax, precipProbability,
            temperatureHigh, temperatureLow, apparentTemperatureHigh,
            apparentTemperatureLow, dewPoint, humidity, pressure,
            windSpeed, windGust, cloudCover, uvIndex, uvIndexTime,
            visibility, ozone, temperatureMin, temperatureMax,
            apparentTemperatureMin, apparentTemperatureMax

        https://darksky.net/dev/docs
    """

    def __init__(self, fonts, location, language, units, config):
        super().__init__(fonts, location, language, units, config)

        block = condition1 = condition2 = None
        if "block" in config:
            block = config["block"]
        if "conditions" in config:
            conditions = config["conditions"]
            length = len(conditions)
            if length > 0:
                condition1 = conditions[0]
            if length > 1:
                condition2 = conditions[1]
        if not check_condition(block, condition1) or not check_condition(
                block, condition2):
            raise ValueError(__class__.__name__)

        self.block = block
        self.condition1 = condition1
        self.condition2 = condition2
        logging.info("weather forcust graph (%s. %s, %s)", block, condition1,
                     condition2)

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
                                    _(ylabel1), y2, _(ylabel2))
