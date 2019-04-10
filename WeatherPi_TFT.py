#!/usr/bin/python3
# -*- coding: utf-8 -*-

import datetime
import gettext
import json
import locale
import os
import pygame
import requests
import sys
import threading
import time

BLACK = (10, 10, 10)
DARK_GRAY = (43, 43, 43)
WHITE = (255, 255, 255)

RED = (231, 76, 60)
GREEN = (39, 174, 96)
BLUE = (52, 152, 219)

YELLOW = (241, 196, 15)
ORANGE = (238, 153, 18)

(language_code, encoding) = locale.getdefaultlocale()
locale.setlocale(locale.LC_ALL, (language_code, encoding))
trans = gettext.translation(
    "messages", localedir="locale", languages=[language_code], fallback=True)
trans.install()

CONNECTION_ERROR = True
REFRESH_ERROR = True
PATH_ERROR = True
PRECIPTYPE = "NULL"
PRECIPCOLOR = WHITE

threads = []
weather_data = {}


def icon_file(file):
    return "{}/icons/{}".format(sys.path[0], file)


def log_file(file):
    return "{}/logs/{}".format(sys.path[0], file)


def font_file(file):
    return "{}/fonts/{}".format(sys.path[0], file)


def load_config():
    global config
    data = open("{}/config.json".format(sys.path[0])).read()
    config = json.loads(data)


def convert_timestamp(timestamp, param_string):
    """
    :param timestamp: takes a normal integer unix timestamp
    :param param_string: use the default convert timestamp to timestring options
    :return: a converted string from timestamp
    """

    timestring = str(
        datetime.datetime.fromtimestamp(int(timestamp)).strftime(param_string))

    return timestring


def temparature_text(temperature):
    if config["FORECAST_UNITS"] == "si":
        return "{}°C".format(temperature)
    else:
        return "{}°F".format(temperature)


def percentage_text(value):
    return "{}%".format(value)


def precip_color(precip_type):
    if precip_type == "rain":
        return BLUE
    elif precip_type == "snow":
        return WHITE
    elif precip_type == "sleet":
        return RED
    else:
        return ORENGE


def speed_text(speed):
    if config["FORECAST_UNITS"] == "si":
        return "{} km/h".format(speed)
    else:
        return "{} mi/h".format(speed)


class WeatherModule:
    def __init__(self, rect):
        """
        :param rect: module area (top, left, width, height)
        """
        self.rect = pygame.Rect(rect)

    def draw(self):
        SCREEN.fill(WHITE, rect=self.rect)

    def clean(self):
        SCREEN.fill(BLACK, rect=self.rect)

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
        print(size)
        if align == "center":
            x = (self.rect.width - size[0]) / 2
        elif align == "right":
            x = self.rect.width - size[0]
        SCREEN.blit(
            font.render(text, True, color),
            (self.rect.left + x, self.rect.top + y))

    def draw_file(self, file, position, rotate=0):
        if os.path.isfile(file):
            image = pygame.image.load(file)
            self.draw_image(image, position, rotate)
        else:
            global PATH_ERROR
            PATH_ERROR = True
            print("{} not found.".format(file))

    def draw_image(self, image, position, rotate=0):
        (x, y) = position
        if rotate:
            (w, h) = image.get_size()
            image = pygame.transform.rotate(image, rotate)
            x = x + (w - image.get_width()) / 2
            y = h + (h - image.get_height()) / 2
        SCREEN.blit(image, (self.rect.left + x, self.rect.top + y))


class Update:
    @staticmethod
    def get_weather():
        global threads, CONNECTION_ERROR

        thread = threading.Timer(300, Update.get_weather)
        thread.start()
        threads.append(thread)

        try:
        #   url = "https://api.forecast.io/forecast/{}/{},{}".format(
        #       config["FORECAST_IO_KEY"], config["FORECAST_LAT"],
        #       config["FORECAST_LON"])
        #   data = requests.get(url,
        #                       params={
        #                           "lang": config["FORECAST_LANGUAGE"],
        #                           "units": config["FORECAST_UNITS"],
        #                           "exclude": config["FORECAST_EXCLUDES"]
        #                       }).json()
        #   with open(log_file("latest_weather.json"), "w") as file:
        #       json.dump(data, file, indent=2, sort_keys=True)

            CONNECTION_ERROR = False
            print("\njson file saved")

        except (requests.HTTPError, requests.ConnectionError):
            CONNECTION_ERROR = True
            print("Connection ERROR")

    @staticmethod
    def load_weather():
        global threads, weather_data, PATH_ERROR, REFRESH_ERROR

        thread = threading.Timer(30, Update.load_weather)
        thread.start()
        threads.append(thread)

        PATH_ERROR = REFRESH_ERROR = False
        try:
            data = open(log_file("latest_weather.json")).read()
            new_weather_data = json.loads(data)
            weather_data = new_weather_data
            print("\nweather file loaded")

        except IOError:
            REFRESH_ERROR = True
            print("ERROR - can't load weather file")

    @staticmethod
    def run():
        #Update.get_weather()
        Update.load_weather()


def draw_background():
    SCREEN.fill(BLACK)

    wifi_icon = icon_file("no-wifi.png" if CONNECTION_ERROR else "wifi.png")
    refresh_icon = icon_file("no-refresh.png"
                             if REFRESH_ERROR else "refresh.png")
    path_icon = icon_file("no-path.png" if PATH_ERROR else "path.png")

    wm = WeatherModule((225, 0, 15, 45))
    wm.draw_file(wifi_icon, (0, 0))
    wm.draw_file(refresh_icon, (0, 15))
    wm.draw_file(path_icon, (0, 30))


def draw_clock():
    timestamp = time.time()
    locale_date = convert_timestamp(timestamp, "%x")
    locale_time = convert_timestamp(timestamp, "%H:%M")
    locale_second = convert_timestamp(timestamp, "%S")

    wm = WeatherModule((0, 0, 120, 50))
    wm.draw_text(locale_date, font_small_bold, WHITE, (10, 4))
    wm.draw_text(locale_time, font_big_bold, WHITE, (10, 19))
    wm.draw_text(locale_second, font_small_bold, WHITE, (92, 19))

    print("\nDay: {}".format(locale_date))
    print("Time: {}".format(locale_time))

#def draw_temperature_humidity():
#    wm = WeatherModule((180, 50, 80, 110))
#    print("====")
#    wm.draw_text(_("Indoor"), font_small_bold, WHITE, (0, 25))
#    wm.draw_text("18.9°C", font_small_bold, WHITE, (0, 45))
#    wm.draw_text("47.3%", font_small_bold, WHITE, (0, 65))
#    print("====")

def draw_weather():
    currently = weather_data["currently"]
    summary = currently["summary"]
    temperature = temparature_text(currently["temperature"])

    # If precipIntensity is zero, then this property will not be defined
    precip_robability = currently["precipProbability"]
    if precip_robability:
        precip_robability = percentage_text(precip_robability * 100)
        precip_type = _(currently["precipType"])
        color = precip_color(currently["precipType"])
    else:
        precip_robability = percentage_text(precip_robability * 100)
        precip_type = _("Precipitation")
        color = ORANGE

    weather_icon = icon_file("{}.png".format(currently["icon"]))

    #    DrawString(summary, font_small_bold, ORANGE, 55).center(1, 0)
    #    DrawString(temperature, font_big_bold, ORANGE, 75).right()
    #    DrawString(precip_probability, font_big_bold, precip_color,
    #               105).right()
    #    DrawString(_(precip_type), font_small_bold, precip_color, 140).right()

    wm = WeatherModule((0, 50, 240, 110))
    wm.draw_text(summary, font_small_bold, color, (0, 5), "center")
    wm.draw_text(temperature, font_big_bold, color, (0, 25), "right")
    wm.draw_text(precip_robability, font_big_bold, color, (120, 55), "right")
    wm.draw_text(precip_type, font_small_bold, color, (0, 90), "right")
    wm.draw_file(weather_icon, (10, 5))

    if precip_type == "rain":
        wm.draw_file(icon_file("preciprain.png"), (120, 65))
    elif precip_type == "show":
        wm.draw_file(icon_file("precipsnow.png"), (120, 65))

    print("summary: {}".format(summary))
    print("temperature: {}".format(temperature))
    print("{}: {}".format(_(precip_type), precip_robability))
    print("precip_type: {} ; color: {}".format(precip_type, color))
    print(weather_icon)


def draw_weather_forecast():
    daily = weather_data["daily"]["data"]
    for i in range(config["FORECAST_DAYS"]):
        day_of_week = convert_timestamp(daily[i + 1]["time"], "%a")
        temperature = "{} | {}".format(
            int(daily[i + 1]["temperatureMin"]),
            int(daily[i + 1]["temperatureMax"]))
        weather_icon = icon_file("mini_{}.png".format(daily[i + 1]["icon"]))

        wm = WeatherModule((i * 80, 160, 80, 80))
        wm.draw_text(day_of_week, font_small_bold, ORANGE, (0, 0), "center")
        wm.draw_text(temperature, font_small_bold, WHITE, (0, 15), "center")
        wm.draw_file(weather_icon, (15, 35))

        print("forecast: {} ; {} ; {}".format(day_of_week, temperature, weather_icon))


def draw_sunrise_sunset():
    daily = weather_data["daily"]["data"]
    surise = convert_timestamp(int(daily[0]["sunriseTime"]), "%H:%M")
    sunset = convert_timestamp(int(daily[0]["sunsetTime"]), "%H:%M")

    wm = WeatherModule((0, 240, 80, 80))
    wm.draw_file(icon_file("sunrise.png"), (10, 20))
    wm.draw_file(icon_file("sunset.png"), (10, 50))
    wm.draw_text(surise, font_small_bold, WHITE, (0, 25), "right")
    wm.draw_text(sunset, font_small_bold, WHITE, (0, 55), "right")

    print("sunrise: {} ; sunset {}".format(surise, sunset))


def draw_moon_phase():
    daily = weather_data["daily"]["data"]
    moon_phase = int((float(daily[0]["moonPhase"]) * 100 / 3.57) + 0.25)
    moon_icon = icon_file("moon-{}.png".format(moon_phase))

    wm = WeatherModule((80, 240, 80, 80))
    wm.draw_file(moon_icon, (10, 10))

    print("moon phase: {} ; {}".format(moon_phase, moon_icon))


def draw_wind():
    currently = weather_data["currently"]
    wind_speed = str(
        round((float(currently["windSpeed"]) * 1.609344), 1)) + " km/h"
    wind_bearing = currently["windBearing"]
    angle = 360 - wind_bearing + 180

    wm = WeatherModule((160, 240, 80, 80))
    wm.draw_text("N", font_small_bold, WHITE, (0, 10), "center")
    wm.draw_text(wind_speed, font_small_bold, WHITE, (0, 60), "center")
    wm.draw_file(icon_file("circle.png"), (25, 30))
    wm.draw_file(icon_file("arrow.png"), (25, 35), angle)

    print("wind speed: {}".format(wind_speed))
    print("wind bearing: {}({})".format(wind_bearing, angle))


def refresh_screen():
    draw_background()
    draw_clock()
#    draw_temperature_humidity()
    draw_weather()
    draw_weather_forecast()
    draw_sunrise_sunset()
    draw_moon_phase()
    draw_wind()

    pygame.display.update()
    time.sleep(1)


def quit_all():
    global threads

    for thread in threads:
        thread.cancel()
        thread.join()

    pygame.quit()
    quit()


def loop():
    Update.run()

    running = True
    while running:
        refresh_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    break
                elif event.key == pygame.K_SPACE:
                    print("SPACE")

    quit_all()


def init_pygame():
    global SCREEN, font_small, font_big, font_small_bold, font_big_bold

    os.putenv("SDL_FBDEV", "/dev/fb1")
    pygame.init()
    pygame.mouse.set_visible(False)
    SCREEN = pygame.display.set_mode(
        (config["DISPLAY_WIDTH"], config["DISPLAY_HEIGHT"]))
    # SCREEN = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption("WeatherPi_SCREEN")

    font_small = pygame.font.Font(font_file(config["FONT_REGULAR"]), 14)
    font_big = pygame.font.Font(font_file(config["FONT_REGULAR"]), 30)
    font_small_bold = pygame.font.Font(font_file(config["FONT_BOLD"]), 14)
    font_big_bold = pygame.font.Font(font_file(config["FONT_BOLD"]), 30)


if __name__ == "__main__":
    load_config()

    init_pygame()

    try:
        loop()

    except KeyboardInterrupt:
        quit_all()
