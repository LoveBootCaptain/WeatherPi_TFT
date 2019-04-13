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


class RepeatedTimer(threading.Timer):
    def __init__(self, interval, function, args=[], kwargs={}):
        super().__init__(interval, self.run, args, kwargs)
        self.thread = None
        self.function = function

    def run(self):
        self.thread = threading.Timer(self.interval, self.run)
        self.thread.start()
        self.function(*self.args, **self.kwargs)

    def cancel(self):
        if self.thread is not None:
            self.thread.cancel()
            self.thread.join()
            del self.thread


def weather_forecast():
    global weather_data

    try:
        data = requests.get(
            "https://api.forecast.io/forecast/{}/{},{}".format(
                config["api_key"], config["latitude"], config["longitude"]),
            params={
                "lang": config["language"],
                "units": config["units"],
                "exclude": "minutely,hourly,flags"}).json()
        weather_file = "{}/logs/latest_weather.json".format(sys.path[0])
        with open(weather_file, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
        weather_data = data

        logging.debug("weather forecast updated")

    except Exception as e:
        logging.debug("weather forecast failed")
        logging.debug(e.message)


class WeatherModule:
    def __init__(self, rect):
        """
        :param rect: module area (top, left, width, height)
        """
        self.rect = pygame.Rect(rect)

    def strftime(self, timestamp, format):
        return datetime.datetime.fromtimestamp(int(timestamp)).strftime(format)

    def temparature_text(self, value):
        return ("{}°C" if config["units"] == "si" else "{}°F").format(value)

    def speed_text(self, value):
        return ("{} km/h" if config["units"] == "si" else "{} mi/h").format(value)

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
            return pygame.image.load(file)
        else:
            logging.debug("{} not found.".format(file))
            return None

    def draw_image(self, image, position, angle=0):
        """
        :param image: image to draw
        :param position: render relative position (x, y)
        :param angle: counterclockwise  degrees angle
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
    def draw(self):
        self.clean()
        if weather_data is None:
            self.draw_text("waiting for weather forecast data ...",
                           font_s, white, (0, self.rect.height / 2), "center")


class Clock(WeatherModule):
    def draw(self):
        timestamp = time.time()
        locale_date = self.strftime(timestamp, "%x")
        locale_time = self.strftime(timestamp, "%H:%M")
        locale_second = self.strftime(timestamp, "%S")

        self.draw_text(locale_date, font_s_bold, white, (10, 4))
        self.draw_text(locale_time, font_l_bold, white, (10, 19))
        self.draw_text(locale_second, font_s_bold, white, (92, 19))


class Weather(WeatherModule):
    def __init__(self, rect):
        super().__init__(rect)
        self.rain_icon = self.load_icon("preciprain.png")
        self.snow_icon = self.load_icon("precipsnow.png")

    def draw(self):
        if weather_data is None:
            return

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

        self.draw_text(summary, font_s_bold, color, (120, 5))
        self.draw_text(temperature, font_l, color, (0, 25), "right")
        self.draw_text(precip_porobability, font_l, color, (120, 55), "right")
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
        if weather_data is None:
            return

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
        self.forecast_days = config["forecast_days"]
        self.forecast_modules = []
        for i in range(self.forecast_days):
            self.forecast_modules.append(DailyWeatherForecast(
                (self.rect.x + i * self.rect.width, self.rect.y, self.rect.width, self.rect.height), i))

    def draw(self):
        if weather_data is None:
            return
        for module in self.forecast_modules:
            module.draw()


class SunriseSuset(WeatherModule):
    def __init__(self, rect):
        super().__init__(rect)
        self.sunrise_icon = self.load_icon("sunrise.png")
        self.sunset_icon = self.load_icon("sunset.png")

    def draw(self):
        if weather_data is None:
            return

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
        if weather_data is None:
            return

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
        if weather_data is None:
            return
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
        (config["display_width"], config["display_height"]))
    pygame.display.set_caption("WeatherPi")

    # initialize color
    global white, black, red, blue, orange
    white = pygame.Color("white")[:3]
    black = pygame.Color("black")[:3]
    red = pygame.Color("red")[:3]
    blue = pygame.Color("blue")[:3]
    orange = pygame.Color("orange")[:3]

    # initialize font
    global font_s, font_m, font_l, font_s_bold, font_m_bold, font_l_bold
    font_regular = "{}/fonts/{}".format(sys.path[0], config["font_regular"])
    font_bold = "{}/fonts/{}".format(sys.path[0], config["font_bold"])
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
    logging.basicConfig(filename="WeatherPi.log", level=logging.DEBUG)

    # initialize thread
    timer_thread = None

    # initialize weather data
    global weather_data
    weather_data = None

    try:
        # load config.json
        global config
        with open("{}/config.json".format(sys.path[0]), "r") as f:
            config = json.loads(f.read())

        # init pygame
        init_pygame()

        # start weather forecast thread
        timer_thread = RepeatedTimer(300, weather_forecast)
        timer_thread.start()

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
            # draw modules
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
        if timer_thread:
            timer_thread.cancel()
        pygame.quit()
        quit()


if __name__ == "__main__":
    main()
