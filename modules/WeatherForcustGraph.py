# pylint: disable=invalid-name
""" Weather forcust graph class
"""

import datetime
import logging
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
    if condition:
        if block == "hourly":
            if condition not in hourly:
                raise ValueError("{} {} not in {}".format(
                    block, condition, " ,".join(hourly)))
        elif block == "daily":
            if condition not in daily:
                raise ValueError("{} {} must be one of {}".format(
                    block, condition, ", ".join(daily)))
        else:
            raise ValueError("{} must be hourly or daily".format(block))


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

        self.block = None
        if "block" in config:
            self.block = config["block"]

        self.conditions = []
        for condition in config["conditions"]:
            check_condition(self.block, condition)
            self.conditions.append(condition)
        if len(self.conditions) < 2:
            self.conditions.append(None)

        logging.info("weather forcust graph (%s. %s)", self.block,
                     ",".join(self.conditions))

    def draw(self, screen, weather, updated):
        if weather is None or not updated:
            return

        data = weather[self.block]["data"]
        times = list(map(lambda x: adjust_unit(x, "time", self.units), data))
        if self.conditions[0]:
            y1 = list(
                map(lambda x: adjust_unit(x, self.conditions[0], self.units),
                    data))
            ylabel1 = "".join(
                map(lambda x: x if x.islower() else " " + x,
                    self.conditions[0])).capitalize()
        else:
            y1 = ylabel1 = None
        if self.conditions[1]:
            y2 = list(
                map(lambda x: adjust_unit(x, self.conditions[1], self.units),
                    data))
            ylabel2 = "".join(
                map(lambda x: x if x.islower() else " " + x,
                    self.conditions[1])).capitalize()
        else:
            y2 = ylabel2 = None

        self.clear_surface()
        GraphUtils.set_font(self.fonts["name"])
        GraphUtils.draw_2axis_graph(screen, self.surface, self.rect, times, y1,
                                    _(ylabel1), y2, _(ylabel2))
