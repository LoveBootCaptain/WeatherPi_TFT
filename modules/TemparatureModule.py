# pylint: disable=invalid-name, too-many-locals, broad-except
"""Temperature and Humidity Sensor Module
"""
import datetime
import logging
import numpy as np
import pygame
from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer


class TemparatureModule(WeatherModule):
    """
    Temparature and humidity sensor module class
    """
    # minutes to keep data
    DATA_POINTS = 6 * 60

    def __init__(self, fonts, location, language, units, config):
        super().__init__(fonts, location, language, units, config)
        self.sensor_thread = None
        self.last_hash_value = None

        # histrical data
        now = datetime.datetime.now()
        self.times = [
            now - datetime.timedelta(minutes=x)
            for x in range(0, self.DATA_POINTS)
        ]
        self.times.reverse()
        self.temparatures = [np.nan] * self.DATA_POINTS
        self.humidities = [np.nan] * self.DATA_POINTS

        # glaph options
        self.graph_rect = None
        if "graph_rect" in config:
            self.graph_rect = pygame.Rect(config["graph_rect"])

    def start_sensor_thread(self, interval, function, args=None, kwargs=None):
        """start sensor thread
        """
        self.sensor_thread = RepeatedTimer(interval, function, args, kwargs)
        self.sensor_thread.start()

    def get_sensor_value(self):
        """read last sensor value
        """
        # No result yet
        result = self.sensor_thread.get_result()
        if result is None:
            logging.info("%s: No data from sensor", __class__.__name__)
            self.last_hash_value = None
            return (None, None, False)

        (celsius, humidity) = result

        # logging only once a minute
        dt = datetime.datetime.now()
        if dt.second == 0:
            self.times = self.times[1:] + [dt]
            if self.temparatures is not None:
                celsius = np.nan if celsius is None else float(
                    celsius if self.units ==
                    "si" else Utils.fahrenheit(celsius))
                self.temparatures = self.temparatures[1:] + [celsius]
            if self.humidities is not None:
                humidity = np.nan if humidity is None else float(humidity)
                self.humidities = self.humidities[1:] + [humidity]

        # Has the value changed
        hash_value = self.sensor_thread.get_hash_value()
        if self.last_hash_value == hash_value:
            return (celsius, humidity, False)

        self.last_hash_value = hash_value
        return (celsius, humidity, True)

    def plot_graph(self, screen):
        """graph plotting
        """

        if self.graph_rect is None:
            return

        # smoothing by moving average
        kernel = np.ones(4) / 4
        mode = "valid"
        times = self.times[1:-2]
        temparatures = np.convolve(self.temparatures, kernel,
                                   mode=mode) if self.temparatures else None
        humidities = np.convolve(self.humidities, kernel,
                                 mode=mode) if self.humidities else None

        # import modules only when plotting graphs
        from modules.GraphUtils import GraphUtils

        surface = pygame.Surface(
            (self.graph_rect.width, self.graph_rect.height))
        GraphUtils.plot_2axis_graph(screen, surface, self.graph_rect, times,
                                    temparatures, "Temparature", humidities,
                                    "Humidity")

    def quit(self):
        if self.sensor_thread:
            self.sensor_thread.quit()
