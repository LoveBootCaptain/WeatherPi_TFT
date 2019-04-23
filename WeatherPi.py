#!/usr/bin/python3
# -*- coding: utf-8 -*-

import gettext
import hashlib
import importlib
import json
import locale
import logging
import os
import pygame
import requests
import sys
import time
from modules.BuiltIn import Alerts, Clock, Weather, WeatherForecast, SunriseSuset, MoonPhase, Wind
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
        hash = hashlib.md5(json.dumps(data).encode()).hexdigest()
        return data, hash

    except Exception as e:
        logging.error("darksky weather forecast api failed: {}".format(e))
        return None


def geolocode(key, language, address, latitude, longitude):
    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "address": address,
                "language": language,
                "latlng": "{},{}".format(latitude, longitude),
                "key": key
            })
        response.raise_for_status()
        data = response.json()
        location = data["results"][0]["geometry"]["location"]
        components = []
        for component in data["results"][0]["address_components"]:
            if component["types"][0] in [
                    "locality", "administrative_area_level_1"
            ]:
                components.append(component["short_name"])
        address = ",".join(components)
        return location["lat"], location["lng"], address

    except Exception as e:
        logging.error("google geocode api failed: {}".format(e))
        return None


def main():
    # initialize logger
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout,
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
        trans = gettext.translation("messages",
                                    localedir="{}/locale".format(sys.path[0]),
                                    languages=[language],
                                    fallback=True)
        trans.install()

        # initialize address, latitude and longitude
        if config["google_api_key"]:
            results = geolocode(config["google_api_key"], language,
                                config["address"], config["latitude"],
                                config["longitude"])
            if results is not None:
                latitude, longitude, address = results
                logging.info("location: {},{} {}".format(
                    latitude, longitude, address))
                config["latitude"] = latitude
                config["longitude"] = longitude
                config["address"] = address

        # start weather forecast thread
        timer_thread = RepeatedTimer(300, weather_forecast, [
            config["darksky_api_key"], config["latitude"], config["longitude"],
            language, config["units"]
        ])
        timer_thread.start()
        logging.info("weather forecast thread started")

        # initialize pygame
        os.putenv("SDL_FBDEV", config["SDL_FBDEV"])
        pygame.init()
        pygame.mouse.set_visible(False)
        screen = pygame.display.set_mode(config["display"])
        SCREEN_SLEEP = pygame.USEREVENT + 1
        SCREEN_WAKEUP = pygame.USEREVENT + 2
        logging.info("pygame initialized")

        # load modules
        location = {
            "latitude": config["latitude"],
            "longitude": config["longitude"],
            "address": config["address"]
        }
        units = config["units"]
        fonts = {}
        for style in ["regular", "bold"]:
            fonts[style] = "{}/fonts/{}".format(sys.path[0],
                                                config["fonts"][style])
        modules = []
        for module in config["modules"]:
            name = module["module"]
            conf = module["config"]
            if name in globals():
                logging.info("load built-in module: {}".format(name))
                m = (globals()[name])
            else:
                logging.info("load external module: {}".format(name))
                m = getattr(importlib.import_module("modules.{}".format(name)),
                            name)
            modules.append((m)(fonts, language, units, conf))
        logging.info("modules loaded")

        # main loop
        running = True
        screen_on = True
        last_hash = None
        while running:
            # weather data check
            result = timer_thread.result()
            (weather, hash) = result if result is not None else (None, None)
            if last_hash == hash:
                updated = False
            else:
                logging.info("weather data updated")
                last_hash = hash
                updated = True

            # update screen
            for module in modules:
                module.draw(screen, weather, updated)
            if screen_on:
                pygame.display.update()

            # event check
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == SCREEN_SLEEP:
                    screen.fill(pygame.Color("black"))
                    pygame.display.update()
                    screen_on = False
                elif event.type == SCREEN_WAKEUP:
                    last_hash = None
                    screen_on = True

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
