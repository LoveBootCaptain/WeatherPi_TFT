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
import time
from modules.BuiltIn import Background, Clock, Weather, WeatherForecast, SunriseSuset, MoonPhase, Wind
from modules.RepeatedTimer import RepeatedTimer


def weather_forecast(api_key, latitude, longitude, language, units):
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
        logging.info("weather forecast updated")
        return data

    except Exception as e:
        logging.error("weather forecast failed: {}".format(e))
        return None


def main():
    # initialize logger
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format="%(asctime)s %(levelname)s %(message)s")

    # initialize thread
    timer_thread = None

    # initialize modules
    modules = []

    try:
        # load config file
        file = "/boot/WeatherPi.json"
        if not os.path.exists(file):
            file = "{}/config.json".format(sys.path[0])
        with open(file, "r") as f:
            config = json.loads(f.read())
        logging.info("config.json loaded")

        # initialize locale, gettext
        language = config["locale"].split("_")[0]
        locale.setlocale(locale.LC_ALL, config["locale"])
        trans = gettext.translation("messages", localedir="{}/locale".format(
            sys.path[0]), languages=[language], fallback=True)
        trans.install()

        # start weather forecast thread
        timer_thread = RepeatedTimer(300, weather_forecast, [
            config["api_key"], config["latitude"], config["longitude"],
            language, config["units"]
        ])
        timer_thread.start()
        logging.info("weather forecast thread started")

        # initialize pygame
        os.putenv("SDL_FBDEV", config["SDL_FBDEV"])
        pygame.init()
        pygame.mouse.set_visible(False)
        screen = pygame.display.set_mode(config["display"])
        logging.info("pygame initialized")

        # load fonts
        regular = "{}/fonts/{}".format(sys.path[0], config["fonts"]["regular"])
        bold = "{}/fonts/{}".format(sys.path[0], config["fonts"]["bold"])
        fonts = {"regular": {}, "bold": {}}
        for (style, size) in [["small", 14], ["medium", 22], ["large", 30]]:
            fonts["regular"][style] = pygame.font.Font(regular, size)
            fonts["bold"][style] = pygame.font.Font(bold, size)
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
            weather = timer_thread.result()
            for module in modules:
                module.draw(weather)
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
            logging.info("weather forecast thread stopped")
            timer_thread.quit()
        for module in modules:
            module.quit()
        pygame.quit()
        quit()


if __name__ == "__main__":
    main()
