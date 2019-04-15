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
from modules.BuiltIn import Background, Clock, Weather, WeatherForecast, SunriseSuset, MoonPhase, Wind


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


def main():
    # initialize logger
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")

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
        trans = gettext.translation("messages", localedir="{}/locale".format(
            sys.path[0]), languages=[language_code], fallback=True)
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
        logging.error(e)

    finally:
        if timer_thread:
            timer_thread.cancel()
        pygame.quit()
        quit()


if __name__ == "__main__":
    main()
