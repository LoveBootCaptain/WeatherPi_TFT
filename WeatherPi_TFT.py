#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
import gettext
import json
import locale
import logging
import os
import pygame
import requests
import sys
import threading
import time


class Update:
    @staticmethod
    def get_weather():
        global threads, CONNECTION

        thread = threading.Timer(300, Update.get_weather)
        thread.start()
        threads.append(thread)

        try:
            url = "https://api.forecast.io/forecast/{}/{},{}".format(
                config["FORECAST_IO_KEY"], config["FORECAST_LAT"],
                config["FORECAST_LON"])
            data = requests.get(url,
                                params={
                                    "lang": config["FORECAST_LANGUAGE"],
                                    "units": config["FORECAST_UNITS"],
                                    "exclude": config["FORECAST_EXCLUDES"]
                                }).json()
            weather_file = "{}/logs/latest_weather.json".format(sys.path[0])
            with open(weather_file, "w") as f:
                json.dump(data, f, indent=2, sort_keys=True)

            CONNECTION = True
            logging.debug("weather data saved")

        except Exception as e:
            CONNECTION = False
            logging.debug("get_weather failed")
            logging.debug(e.message)

    @staticmethod
    def load_weather():
        global threads, weather_data, PATH_ERROR, REFRESH

        thread = threading.Timer(30, Update.load_weather)
        thread.start()
        threads.append(thread)

        PATH_ERROR = False
        REFRESH = True
        try:
            weather_file = "{}/logs/latest_weather.json".format(sys.path[0])
            with open(weather_file, "r") as f:
                data = json.loads(f.read())
            weather_data = data
            logging.debug("weather data loaded")

        except Exception as e:
            REFRESH = False
            logging.debug("load_weather failed")
            logging.debug(e.message)

    @staticmethod
    def run():
        Update.get_weather()
        Update.load_weather()


class WeatherModule:
    def __init__(self, rect):
        """
        :param rect: module area (top, left, width, height)
        """
        self.rect = pygame.Rect(rect)

    def strftime(self, timestamp, format):
        return datetime.datetime.fromtimestamp(int(timestamp)).strftime(format)

    def temparature_text(self, value):
        return ("{}°C" if config["FORECAST_UNITS"] == "si" else "{}°F").format(value)

    def speed_text(self, value):
        return ("{} km/h" if config["FORECAST_UNITS"] == "si" else "{} mi/h").format(value)

    def percentage_text(self, value):
        return "{}%".format(value)

    def precip_color(self, precip_type):
        if precip_type == "rain":
            return blue
        elif precip_type == "snow":
            return white
        elif precip_type == "sleet":
            return red
        else:
            return orange

    def draw(self):
        screen.fill(white, rect=self.rect)

    def clean(self):
        screen.fill(black, rect=self.rect)

    def draw_text(self, text, font, color, position, align="left"):
        """
        :param text: text to draw
        :param font: font object
        :param color: rgb color tuple
        :param position: render relative position (x, y)
        :param align: text align. "left", "center", "right"
        """
        (x, y) = position
        size = font.size(text)
        if align == "center":
            x = (self.rect.width - size[0]) / 2
        elif align == "right":
            x = self.rect.width - size[0]
        screen.blit(
            font.render(text, True, color),
            (self.rect.left + x, self.rect.top + y))

    def load_icon(self, icon):
        file = "{}/icons/{}".format(sys.path[0], icon)
        if os.path.isfile(file):
            logging.debug("load icon: {}".format(icon))
            return pygame.image.load(file)
        else:
            global PATH_ERROR
            PATH_ERROR = True
            logging.debug("{} not found.".format(file))
            return None

    def draw_image(self, image, position, angle=0):
        """
        :param image: image to draw
        :param position: render relative position (x, y)
        :param angle:
        """
        if image:
            (x, y) = position
            if angle:
                (w, h) = image.get_size()
                image = pygame.transform.rotate(image, angle)
                x = x + (w - image.get_width()) / 2
                y = h + (h - image.get_height()) / 2
            screen.blit(image, (self.rect.left + x, self.rect.top + y))


class Background(WeatherModule):
    def __init__(self, rect):
        super().__init__(rect)
        self.wifi_icon = self.load_icon("wifi.png")
        self.no_wifi_icon = self.load_icon("no-wifi.png")
        self.fresh_icon = self.load_icon("refresh.png")
        self.no_fresh_icon = self.load_icon("no-refresh.png")
        self.path_icon = self.load_icon("path.png")
        self.no_path_icon = self.load_icon("no-path.png")

    def draw(self):
        self.clean()
        self.draw_image(
            self.wifi_icon if CONNECTION else self.no_wifi_icon, (225, 0))
        self.draw_image(
            self.fresh_icon if REFRESH else self.no_fresh_icon, (225, 15))
        self.draw_image(
            self.no_path_icon if PATH_ERROR else self.path_icon, (225, 30))

        logging.debug("CONNECTION: {}".format(CONNECTION))
        logging.debug("REFRESH: {}".format(REFRESH))
        logging.debug("PATH ERROR: {}".format(PATH_ERROR))


class Clock(WeatherModule):
    def draw(self):
        timestamp = time.time()
        locale_date = self.strftime(timestamp, "%x")
        locale_time = self.strftime(timestamp, "%H:%M")
        locale_second = self.strftime(timestamp, "%S")

        self.draw_text(locale_date, font_s_bold, white, (10, 4))
        self.draw_text(locale_time, font_l_bold, white, (10, 19))
        self.draw_text(locale_second, font_s_bold, white, (92, 19))

        logging.debug("Day: {}".format(locale_date))
        logging.debug("Time: {}".format(locale_time))


class Weather(WeatherModule):
    def __init__(self, rect):
        super().__init__(rect)
        self.rain_icon = self.load_icon("preciprain.png")
        self.snow_icon = self.load_icon("precipsnow.png")

    def draw(self):
        currently = weather_data["currently"]
        summary = currently["summary"]
        temperature = self.temparature_text(currently["temperature"])

        # If precipIntensity is zero, then this property will not be defined
        precip_porobability = currently["precipProbability"]
        if precip_porobability:
            precip_porobability = self.percentage_text(
                precip_porobability * 100)
            precip_type = currently["precipType"]
            color = self.precip_color(currently["precipType"])
        else:
            precip_porobability = self.percentage_text(
                precip_porobability * 100)
            precip_type = "Precipitation"
            color = orange

        weather_icon = self.load_icon("{}.png".format(currently["icon"]))

        self.draw_text(summary, font_s_bold, color, (0, 5), "center")
        self.draw_text(temperature, font_m, color, (0, 25), "right")
        self.draw_text(precip_porobability, font_m, color, (120, 55), "right")
        self.draw_text(_(precip_type), font_s_bold, color, (0, 90), "right")
        self.draw_image(weather_icon, (10, 5))

        if precip_type == "rain":
            self.draw_image(self.rain_icon, (120, 65))
        elif precip_type == "show":
            self.draw_image(self.snow_icon, (120, 65))

        logging.debug("summary: {}".format(summary))
        logging.debug("temperature: {}".format(temperature))
        logging.debug("{}: {}".format(_(precip_type), precip_porobability))
        logging.debug("precip_type: {} ; color: {}".format(
            _(precip_type), color))


class DailyWeatherForecast(WeatherModule):
    def __init__(self, rect, day):
        super().__init__(rect)
        self.day = day

    def draw(self):
        weather = weather_data["daily"]["data"][self.day + 1]
        day_of_week = self.strftime(weather["time"], "%a")
        temperature = "{} | {}".format(
            int(weather["temperatureMin"]), int(weather["temperatureMax"]))
        weather_icon = self.load_icon("mini_{}.png".format(weather["icon"]))
        self.draw_text(day_of_week, font_s_bold, orange, (0, 0), "center")
        self.draw_text(temperature, font_s_bold, white, (0, 15), "center")
        self.draw_image(weather_icon, (15, 35))

        logging.debug("forecast: {} ; {}".format(day_of_week, temperature))


class WeatherForcecast(WeatherModule):
    def __init__(self, rect):
        super().__init__(rect)
        self.forecast_days = config["FORECAST_DAYS"]
        self.forecast_modules = []
        for i in range(self.forecast_days):
            self.forecast_modules.append(DailyWeatherForecast(
                (self.rect.x + i * self.rect.width, self.rect.y, self.rect.width, self.rect.height), i))

    def draw(self):
        for module in self.forecast_modules:
            module.draw()


class SunriseSuset(WeatherModule):
    def __init__(self, rect):
        super().__init__(rect)
        self.sunrise_icon = self.load_icon("sunrise.png")
        self.sunset_icon = self.load_icon("sunset.png")

    def draw(self):
        daily = weather_data["daily"]["data"]
        surise = self.strftime(int(daily[0]["sunriseTime"]), "%H:%M")
        sunset = self.strftime(int(daily[0]["sunsetTime"]), "%H:%M")

        self.draw_image(self.sunrise_icon, (10, 20))
        self.draw_image(self.sunset_icon, (10, 50))
        self.draw_text(surise, font_s_bold, white, (0, 25), "right")
        self.draw_text(sunset, font_s_bold, white, (0, 55), "right")

        logging.debug("sunrise: {} ; sunset {}".format(surise, sunset))


class MoonPhase(WeatherModule):
    def draw(self):
        daily = weather_data["daily"]["data"]
        moon_phase = int((float(daily[0]["moonPhase"]) * 100 / 3.57) + 0.25)
        moon_icon = self.load_icon("moon-{}.png".format(moon_phase))

        self.draw_image(moon_icon, (10, 10))

        logging.debug("moon phase: {}".format(moon_phase))


class Wind(WeatherModule):
    def __init__(self, rect):
        super().__init__(rect)
        self.circle_icon = self.load_icon("circle.png")
        self.arrow_icon = self.load_icon("arrow.png")

    def draw(self):
        currently = weather_data["currently"]
        wind_speed = self.speed_text(
            round((float(currently["windSpeed"]) * 1.609344), 1))
        wind_bearing = currently["windBearing"]
        angle = 360 - wind_bearing + 180

        self.draw_text("N", font_s_bold, white, (0, 10), "center")
        self.draw_text(wind_speed, font_s_bold, white, (0, 60), "center")
        self.draw_image(self.circle_icon, (25, 30))
        self.draw_image(self.arrow_icon, (25, 35), angle)

        logging.debug("wind speed: {}".format(wind_speed))
        logging.debug("wind bearing: {}({})".format(wind_bearing, angle))


def init_pygame():
    os.putenv("SDL_FBDEV", "/dev/fb1")

    # initialize screen
    global screen
    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode(
        (config["DISPLAY_WIDTH"], config["DISPLAY_HEIGHT"]))
    pygame.display.set_caption(__file__)

    # initialize color
    global white, black, red, blue, orange
    white = pygame.Color("white")[:3]
    black = pygame.Color("black")[:3]
    red = pygame.Color("red")[:3]
    blue = pygame.Color("blue")[:3]
    orange = pygame.Color("orange")[:3]

    # initialize font
    global font_s, font_m, font_l, font_s_bold, font_m_bold, font_l_bold
    font_regular = "{}/fonts/{}".format(sys.path[0], config["FONT_REGULAR"])
    font_bold = "{}/fonts/{}".format(sys.path[0], config["FONT_BOLD"])
    font_s = pygame.font.Font(font_regular, 14)
    font_m = pygame.font.Font(font_regular, 22)
    font_l = pygame.font.Font(font_regular, 30)
    font_s_bold = pygame.font.Font(font_bold, 14)
    font_m_bold = pygame.font.Font(font_bold, 22)
    font_l_bold = pygame.font.Font(font_bold, 30)


def main():
    # initialize locale, gettext
    (language_code, encoding) = locale.getdefaultlocale()
    locale.setlocale(locale.LC_ALL, (language_code, encoding))
    trans = gettext.translation(
        "messages", localedir="locale", languages=[language_code], fallback=True)
    trans.install()

    # initialize logging
    logging.basicConfig(filename='logger.log', level=logging.DEBUG)

    # initialize threads
    global threads
    threads = []

    # initialize flags
    global CONNECTION, REFRESH, PATH_ERROR
    CONNECTION = True
    REFRESH = True
    PATH_ERROR = False

    try:
        # load config.json
        global config
        with open("{}/config.json".format(sys.path[0]), "r") as f:
            config = json.loads(f.read())

        # init pygame
        init_pygame()

        # start update thread
        weather_data = {}
        Update.run()

        # load modules
        modules = [
            Background((0, 0, 240, 320)),
            Clock((0, 0, 120, 50)),
            Weather((0, 50, 240, 110)),
            WeatherForcecast((0, 160, 80, 80)),
            SunriseSuset((0, 240, 80, 80)),
            MoonPhase((80, 240, 80, 80)),
            Wind((160, 240, 80, 80))
        ]

        running = True
        while running:
            for module in modules:
                module.draw()
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                        break
                    elif event.key == pygame.K_SPACE:
                        logging.debug("SPACE")

            time.sleep(1)

    except Exception as e:
        logging.debug(e.message)

    finally:
        for thread in threads:
            thread.cancel()
            thread.join()
        pygame.quit()
        quit()


if __name__ == "__main__":
    main()
