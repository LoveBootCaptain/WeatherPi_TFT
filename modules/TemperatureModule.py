# pylint: disable=invalid-name, too-many-locals, broad-except
"""Temperature and Humidity Sensor Module
"""
import datetime
import logging
import numpy as np
from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer


class TemperatureGraph(WeatherModule):
    """
    Temperature and humidity graph module class
    """

    def draw_graph(self, screen, times, temperatures, humidities):
        """draw temperature and humidity graph
        """
        from modules.GraphUtils import GraphUtils

        # smoothing by moving average
        kernel = np.ones(4) / 4
        mode = "valid"
        times = times[1:-2]
        temperatures = np.convolve(temperatures, kernel,
                                   mode=mode) if temperatures else None
        humidities = np.convolve(humidities, kernel,
                                 mode=mode) if humidities else None

        self.clear_surface()
        GraphUtils.set_font(self.fonts["name"])
        GraphUtils.plot_2axis_graph(screen, self.surface, self.rect, times,
                                    temperatures, _("Temperature"), humidities,
                                    _("Humidity"))


class TemperatureModule(WeatherModule):
    """
    Temperature and humidity sensor module class
    """

    def __init__(self, fonts, location, language, units, config):
        super().__init__(fonts, location, language, units, config)
        self.sensor_thread = None
        self.last_hash_value = None

        # histrical data
        self.window_size = 6 * 60
        now = datetime.datetime.now()
        self.times = [
            now - datetime.timedelta(minutes=x)
            for x in range(0, self.window_size)
        ]
        self.times.reverse()
        self.temperatures = [np.nan] * self.window_size
        self.humidities = [np.nan] * self.window_size

        # glaph module setup
        self.graph_module = None
        if "graph_rect" in config:
            config["rect"] = config["graph_rect"]
            self.graph_module = TemperatureGraph(fonts, location, language,
                                                 units, config)

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
            if self.temperatures is not None:
                celsius = np.nan if celsius is None else float(
                    celsius if self.units ==
                    "si" else Utils.fahrenheit(celsius))
                self.temperatures = self.temperatures[1:] + [celsius]
            if self.humidities is not None:
                humidity = np.nan if humidity is None else float(humidity)
                self.humidities = self.humidities[1:] + [humidity]

        # Has the value changed
        hash_value = self.sensor_thread.get_hash_value()
        if self.last_hash_value == hash_value:
            return (celsius, humidity, False)

        self.last_hash_value = hash_value
        return (celsius, humidity, True)

    def draw_graph(self, screen, _weather, _updated):
        """draw temperature and humidity graph
        """
        if self.graph_module:
            self.graph_module.draw_graph(screen, self.times, self.temperatures,
                                         self.humidities)

    def quit(self):
        if self.sensor_thread:
            self.sensor_thread.quit()
