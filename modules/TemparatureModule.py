# pylint: disable=invalid-name, too-many-locals, broad-except
"""Temperature and Humidity Sensor Module
"""
import datetime
import io
import logging
import threading
import time
import pygame
from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer


def plotting(screen, rect, units, times, temparatures, humidities):
    """graph plotting
    """
    start = time.perf_counter()

    # import modules
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.dates import DateFormatter, HourLocator

    # plot graph
    plt.style.use("dark_background")
    fig, ax1 = plt.subplots(figsize=(rect.width / 100, rect.height / 100))
    if temparatures is not None:
        c = plt.get_cmap("Dark2")(0)
        ax1.yaxis.label.set_color(c)
        ax1.set_ylabel(Utils.temperature_text("Temparature ", units))
        ax1.plot(times, temparatures, color=c)
    if humidities is not None:
        c = plt.get_cmap("Dark2")(1)
        ax2 = ax1.twinx()
        ax2.yaxis.label.set_color(color=c)
        ax2.set_ylabel(Utils.percentage_text("Humidity "))
        ax2.plot(times, humidities, color=c)
    ax1.xaxis.set_major_locator(HourLocator())
    ax1.xaxis.set_major_formatter(DateFormatter("%H:%M"))

    # convert to pygame image
    f = io.BytesIO()
    plt.savefig(f, bbox_inches="tight", format="png")
    plt.close(fig)
    f.seek(0)
    image = pygame.image.load(f)

    # draw image
    surface = pygame.Surface((rect.width, rect.height))
    surface.blit(image, (0, 0))
    screen.blit(surface, (rect.left, rect.top))

    logging.info("plot time: {:.2f} sec".format(time.perf_counter() - start))


class TemparatureModule(WeatherModule):
    """
    Temparature and humidity sensor module class
    """
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
        self.temparatures = [float(0)] * self.DATA_POINTS
        self.humidities = [float(0)] * self.DATA_POINTS

        # glaph plotting
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
        self.logging(celsius, humidity)

        # Has the value changed
        hash_value = self.sensor_thread.get_hash_value()
        if self.last_hash_value == hash_value:
            return (celsius, humidity, False)
        self.last_hash_value = hash_value
        return (celsius, humidity, True)

    def logging(self, celsius, humidity):
        """data logging
        """
        # run only once a minute
        dt = datetime.datetime.now()
        if dt.second != 0:
            return

        self.times = self.times[1:] + [dt]
        if self.temparatures is not None:
            celsius = 0 if celsius is None else celsius
            self.temparatures = self.temparatures[1:] + [
                float(celsius if self.units ==
                      "si" else Utils.fahrenheit(celsius))
            ]
        if self.humidities is not None:
            humidity = 0 if humidity is None else humidity
            self.humidities = self.humidities[1:] + [float(humidity)]

    def plotting(self, screen):
        """graph plotting
        """
        threading.Thread(target=plotting,
                         args=(screen, self.graph_rect, self.units, self.times,
                               self.temparatures, self.humidities)).start()

    def quit(self):
        if self.sensor_thread:
            self.sensor_thread.quit()
