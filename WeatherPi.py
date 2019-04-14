#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gettext
import importlib
import json
import locale
import logging
import os
import pygame
import requests
import sys
import threading
import time
from modules.WeatherModule import WeatherModule, Utils

logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format="%(asctime)s %(levelname)s %(message)s")


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


def weather_forecast(api_key, latitude, longitude, language, units):
    global weather_data

    try:
        resopnse = requests.get(
            "https://api.forecast.io/forecast/{}/{},{}".format(
                api_key, latitude, longitude),
            params={
                "lang": language,
                "units": units,
                "exclude": "minutely,hourly,flags"
            })
        resopnse.raise_for_status()

        data = resopnse.json()
        weather_data = data
        logging.info("weather forecast updated")

    except Exception as e:
        logging.error("weather forecast failed: {}".format(e))


class Background(WeatherModule):
    def draw(self, weather):
        self.clean()
        if weather is None:
            self.draw_text("waiting for weather forecast data ...",
                           "regular", "small", "white", (0, self.rect.height / 2), "center")


class Clock(WeatherModule):
    def draw(self, weather):
        timestamp = time.time()
        locale_date = Utils.strftime(timestamp, "%a, %x")
        locale_time = Utils.strftime(timestamp, "%H:%M")
        locale_second = Utils.strftime(timestamp, "%S")

        self.draw_text(locale_date, "bold", "small", "white", (10, 4))
        self.draw_text(locale_time, "regular", "large", "white", (10, 19))
        self.draw_text(locale_second, "regular", "medium", "white", (92, 19))


class Weather(WeatherModule):
    def __init__(self, screen, fonts, language, units, config):
        super().__init__(screen, fonts, language, units, config)
        self.rain_icon = self.load_icon("preciprain.png")
        self.snow_icon = self.load_icon("precipsnow.png")

    def draw(self, weather):
        if weather_data is None:
            return

        currently = weather["currently"]
        summary = currently["summary"]
        temperature = currently["temperature"]
        humidity = currently["humidity"]

        color = Utils.heat_color(temperature, humidity, self.units)
        temperature = Utils.temparature_text(round(temperature, 1), self.units)

        # If precipIntensity is zero, then this property will not be defined
        precip_porobability = currently["precipProbability"]
        if precip_porobability:
            precip_porobability = Utils.percentage_text(
                round(precip_porobability * 100, 1))
            precip_type = currently["precipType"]
        else:
            precip_porobability = Utils.percentage_text(0)
            precip_type = "Precipitation"

        weather_icon = self.load_icon("{}.png".format(currently["icon"]))

        self.draw_text(summary, "bold", "small", "white", (120, 5))
        self.draw_text(temperature, "regular", "large",
                       color, (0, 25), "right")
        self.draw_text(precip_porobability, "regular",
                       "large", color, (120, 55), "right")
        self.draw_text(_(precip_type), "bold", "small",
                       color, (0, 90), "right")
        self.draw_image(weather_icon, (10, 5))

        if precip_type == "rain":
            self.draw_image(self.rain_icon, (120, 65))
        elif precip_type == "show":
            self.draw_image(self.snow_icon, (120, 65))


class DailyWeatherForecast(WeatherModule):
    def draw(self, weather, day):
        if weather_data is None:
            return

        weather = weather["daily"]["data"][day]
        day_of_week = Utils.strftime(weather["time"], "%a")
        temperature = "{} | {}".format(
            int(weather["temperatureMin"]), int(weather["temperatureMax"]))
        weather_icon = self.load_icon("mini_{}.png".format(weather["icon"]))
        self.draw_text(day_of_week, "bold", "small",
                       "orange", (0, 0), "center")
        self.draw_text(temperature, "bold", "small",
                       "white", (0, 15), "center")
        self.draw_image(weather_icon, (15, 35))


class WeatherForecast(WeatherModule):
    def __init__(self, screen, fonts, language, units, config):
        super().__init__(screen, fonts, language, units, config)
        self.forecast_days = config["forecast_days"]
        self.forecast_modules = []
        width = self.rect.width / self.forecast_days
        for i in range(self.forecast_days):
            config["rect"] = [self.rect.x + i * width,
                              self.rect.y, width, self.rect.height]
            self.forecast_modules.append(DailyWeatherForecast(
                screen, fonts, language, units, config))

    def draw(self, weather):
        if weather_data is None:
            return
        for i in range(self.forecast_days):
            self.forecast_modules[i].draw(weather, i + 1)


class SunriseSuset(WeatherModule):
    def __init__(self, screen, fonts, language, units, config):
        super().__init__(screen, fonts, language, units, config)
        self.sunrise_icon = self.load_icon("sunrise.png")
        self.sunset_icon = self.load_icon("sunset.png")

    def draw(self, weather):
        if weather_data is None:
            return

        daily = weather["daily"]["data"]
        surise = Utils.strftime(int(daily[0]["sunriseTime"]), "%H:%M")
        sunset = Utils.strftime(int(daily[0]["sunsetTime"]), "%H:%M")

        self.draw_image(self.sunrise_icon, (10, 20))
        self.draw_image(self.sunset_icon, (10, 50))
        self.draw_text(surise, "bold", "small", "white", (0, 25), "right")
        self.draw_text(sunset, "bold", "small", "white", (0, 55), "right")


class MoonPhase(WeatherModule):
    def draw(self, weather):
        if weather_data is None:
            return

        daily = weather["daily"]["data"]
        moon_phase = int((float(daily[0]["moonPhase"]) * 100 / 3.57) + 0.25)
        moon_icon = self.load_icon("moon-{}.png".format(moon_phase))

        self.draw_image(moon_icon, (10, 10))


class Wind(WeatherModule):
    def __init__(self, screen, fonts, language, units, config):
        super().__init__(screen, fonts, language, units, config)
        self.circle_icon = self.load_icon("circle.png")
        self.arrow_icon = self.load_icon("arrow.png")

    def draw(self, weather):
        if weather_data is None:
            return
        currently = weather["currently"]
        wind_speed = Utils.speed_text(
            round((float(currently["windSpeed"]) * 1.609344), 1), self.units)
        wind_bearing = currently["windBearing"]
        angle = 360 - wind_bearing + 180

        self.draw_text("N", "bold", "small", "white", (0, 10), "center")
        self.draw_text(wind_speed, "bold", "small", "white", (0, 60), "center")
        self.draw_image(self.circle_icon, (25, 30))
        self.draw_image(self.arrow_icon, (25, 35), angle)


def main():
    # initialize thread
    timer_thread = None

    # initialize weather data
    global weather_data
    weather_data = None

    try:
        # load config.json
        with open("{}/config.json".format(sys.path[0]), "r") as f:
            config = json.loads(f.read())
        logging.info("config.json loaded")

        # initialize locale, gettext
        (language_code, encoding) = config["locale"].split(".")
        language = language_code.split("_")[0]
        locale.setlocale(locale.LC_ALL, (language_code, encoding))
        trans = gettext.translation(
            "messages", localedir="locale", languages=[language_code], fallback=True)
        trans.install()

        # start weather forecast thread
        timer_thread = RepeatedTimer(300, weather_forecast, [
            config["api_key"], config["latitude"], config["longitude"],
            language, config["units"]
        ])
        timer_thread.start()
        logging.info("weather forecast thread started")

        # initialize pygame
        os.putenv("SDL_FBDEV", "/dev/fb1")
        pygame.init()
        pygame.mouse.set_visible(False)
        screen = pygame.display.set_mode(config["display"])
        logging.info("pygame initialized")

        # load fonts
        regular = "{}/fonts/{}".format(sys.path[0], config["fonts"]["regular"])
        bold = "{}/fonts/{}".format(sys.path[0], config["fonts"]["bold"])
        fonts = {
            "regular": {
                "small": pygame.font.Font(regular, 14),
                "medium": pygame.font.Font(regular, 22),
                "large": pygame.font.Font(regular, 30),
            },
            "bold": {
                "small": pygame.font.Font(bold, 14),
                "medium": pygame.font.Font(bold, 22),
                "large": pygame.font.Font(bold, 30),
            }
        }
        logging.info("fonts loaded")

        # load modules
        units = config["units"]
        modules = [Background(screen, fonts, language, units, {
                              "rect": screen.get_rect()})]
        for module in config["modules"]:
            name = module["module"]
            conf = module["config"]
            if name in globals():
                logging.info("load built-in module: {}".format(name))
                m = (globals()[name])
            else:
                logging.info("load external module: {}".format(name))
                m = getattr(importlib.import_module(
                    "modules.{}".format(name)), name)
            modules.append((m)(screen, fonts, language, units, conf))
        logging.info("modules loaded")

        # main loop
        running = True
        while running:
            for module in modules:
                module.draw(weather_data)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False

            time.sleep(1)

    except Exception as e:
        print(e)

    finally:
        if timer_thread:
            timer_thread.cancel()
        pygame.quit()
        quit()


if __name__ == "__main__":
    main()
