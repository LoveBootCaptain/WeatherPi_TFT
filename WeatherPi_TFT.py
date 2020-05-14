#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# MIT License
#
# Copyright (c) 2016 LoveBootCaptain (https://github.com/LoveBootCaptain)
# Author: Stephan Ansorge aka LoveBootCaptain
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import datetime
import json
import locale
import os
import threading
import time
import sys
import math

import pygame
from pygame import gfxdraw
import requests
from PIL import Image


PATH = sys.path[0] + '/'

config_data = open(PATH + 'config.json').read()
config = json.loads(config_data)

theme_config = config["THEME"]

theme_settings = open(PATH + theme_config).read()
theme = json.loads(theme_settings)

# if you do local development you can add a mock server (e.g. from postman.io our your homebrew solution)
# simple add this variables to your config.json to save api-requests
# or to create your own custom test data for your own dashboard views)

try:
    if config['ENV'] == 'DEV':
        server = config['MOCKSERVER_URL']
        headers = {'X-Api-Key': f'{config["MOCKSERVER_API_KEY"]}'}

    elif config['ENV'] == 'STAGE':
        server = config['WEATHERBIT_URL']
        headers = {}

    locale.setlocale(locale.LC_ALL, ('de_DE', 'UTF-8'))
    WEATHERBIT_IO_KEY = config['WEATHERBIT_DEV_KEY']

    pygame.init()
    print(f"{config['ENV']} SYSTEM - STARTING IN LOCAL DEV MODE")

except KeyError as e:
    server = config['WEATHERBIT_URL']
    headers = {}

    # using the dashboard on a raspberry with ili9341 tft displays might make this necessary
    os.putenv('SDL_FBDEV', '/dev/fb1')

    pygame.init()
    pygame.mouse.set_visible(False)

    WEATHERBIT_IO_KEY = config['WEATHERBIT_IO_KEY']

    print(f"STARTING IN PROD MODE FOR RPi")

    # this is needed to set the output of weekdays to your local os settings
    # doesn't work on my dev laptop but on the Pi
    locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())

# theme settings from theme config
DISPLAY_WIDTH = theme["DISPLAY"]["WIDTH"]
DISPLAY_HEIGHT = theme["DISPLAY"]["HEIGHT"]

BLACK = theme["COLOR"]["BLACK"]
DARK_GRAY = theme["COLOR"]["DARK_GRAY"]
WHITE = theme["COLOR"]["WHITE"]
RED = theme["COLOR"]["RED"]
GREEN = theme["COLOR"]["GREEN"]
BLUE = theme["COLOR"]["BLUE"]
YELLOW = theme["COLOR"]["YELLOW"]
ORANGE = theme["COLOR"]["ORANGE"]
VIOLET = theme["COLOR"]["VIOLET"]

FONT_MEDIUM = theme["FONT"]["MEDIUM"]
FONT_BOLD = theme["FONT"]["BOLD"]
DATE_SIZE = theme["FONT"]["DATE_SIZE"]
SMALL_SIZE = theme["FONT"]["SMALL_SIZE"]
BIG_SIZE = theme["FONT"]["BIG_SIZE"]

ICON_PATH = sys.path[0] + '/icons/'
FONT_PATH = sys.path[0] + '/fonts/'
LOG_PATH = sys.path[0] + '/logs/'

WEATHERBIT_COUNTRY = config['WEATHERBIT_COUNTRY']
WEATHERBIT_LANG = config['WEATHERBIT_LANGUAGE']
WEATHERBIT_POSTALCODE = config['WEATHERBIT_POSTALCODE']
WEATHERBIT_HOURS = config['WEATHERBIT_HOURS']
WEATHERBIT_DAYS = config['WEATHERBIT_DAYS']

TFT = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
# TFT = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption('WeatherPiTFT')

font_small = pygame.font.Font(FONT_PATH + FONT_MEDIUM, SMALL_SIZE)
font_big = pygame.font.Font(FONT_PATH + FONT_MEDIUM, BIG_SIZE)

date_font = pygame.font.Font(FONT_PATH + FONT_BOLD, DATE_SIZE)
font_small_bold = pygame.font.Font(FONT_PATH + FONT_BOLD, SMALL_SIZE)
font_big_bold = pygame.font.Font(FONT_PATH + FONT_BOLD, BIG_SIZE)

Refresh_Path = ICON_PATH + 'refresh.png'

WiFi_Path = ICON_PATH + 'wifi.png'

Path_Path = ICON_PATH + 'path.png'

WeatherIcon_Path = ICON_PATH + 'unknown.png'

ForeCastIcon_Day_1_Path = ICON_PATH + 'mini_unknown.png'
ForeCastIcon_Day_2_Path = ICON_PATH + 'mini_unknown.png'
ForeCastIcon_Day_3_Path = ICON_PATH + 'mini_unknown.png'

SunRise_Path = ICON_PATH + 'sunrise.png'
SunSet_Path = ICON_PATH + 'sunset.png'

PrecipSnow_Path = ICON_PATH + 'precipsnow.png'
PrecipRain_Path = ICON_PATH + 'preciprain.png'

CONNECTION_ERROR = True
REFRESH_ERROR = True
PATH_ERROR = True
PRECIPTYPE = 'NULL'
PRECIPCOLOR = WHITE

threads = []

json_data = {}


class DrawString:
    def __init__(self, string, font, color, y):
        """
        :param string: the input string
        :param font: the fonts object
        :param color: a rgb color tuple
        :param y: the y position where you want to render the text
        """
        self.string = string
        self.font = font
        self.color = color
        self.y = y
        self.size = self.font.size(self.string)

    def left(self, offset=0):
        """
        :param offset: define some offset pixel to move strings a little bit more left (default=0)
        """

        x = 10 + offset

        self.draw_string(x)

    def right(self, offset=0):
        """
        :param offset: define some offset pixel to move strings a little bit more right (default=0)
        """

        x = (DISPLAY_WIDTH - self.size[0] - 10) - offset

        self.draw_string(x)

    def center(self, parts, part, offset=0):
        """
        :param parts: define in how many parts you want to split your display
        :param part: the part in which you want to render text (first part is 0, second is 1, etc.)
        :param offset: define some offset pixel to move strings a little bit (default=0)
        """

        x = ((((DISPLAY_WIDTH / parts) / 2) + ((DISPLAY_WIDTH / parts) * part)) - (self.size[0] / 2)) + offset

        self.draw_string(x)

    def draw_string(self, x):
        """
        takes x and y from the functions above and render the fonts
        """

        TFT.blit(self.font.render(self.string, True, self.color), (x, self.y))


class DrawImage:
    def __init__(self, image_path, y, size=None, fillcolor=None, angle=None):
        """
        :param image_path: the path to the image you want to render
        :param y: the y-postion of the image you want to render
        """

        self.image_path = image_path
        # self.image = pygame.image.load(self.image_path).convert_alpha()
        self.image = Image.open(self.image_path)
        self.y = y
        # self.size = self.image.get_rect().size
        self.img_size = self.image.size
        self.size = size
        self.angle = angle

        if size:
            width, height = self.image.size
            if width >= height:
                width, height = (size, int(size / width * height))
            else:
                width, height = (int(size / width * height), size)

            self.image = self.image.resize((width, height), Image.LANCZOS)
            self.img_size = self.image.size

        self.fillcolor = fillcolor

        self.image = pygame.image.fromstring(self.image.tobytes(), self.image.size, self.image.mode)

        if angle:
            self.image = pygame.transform.rotate(self.image, self.angle)

    @staticmethod
    def fill(surface, color):
        """converts the color on an icon"""
        w, h = surface.get_size()
        r, g, b = color
        for x in range(w):
            for y in range(h):
                a = surface.get_at((x, y))[3]
                color = pygame.Color(r, g, b, a)
                surface.set_at((x, y), color)

    def left(self, offset=0):
        """
        :param offset: define some offset pixel to move image a little bit more left(default=0)
        """

        x = 10 + offset

        self.draw_image(x)

    def right(self, offset=0):
        """
        :param offset: define some offset pixel to move image a little bit more right (default=0)
        """

        x = (DISPLAY_WIDTH - self.img_size[0] - 10) - offset

        self.draw_image(x)

    def center(self, parts, part, offset=0):
        """
        :param parts: define in how many parts you want to split your display
        :param part: the part in which you want to render text (first part is 0, second is 1, etc.)
        :param offset: define some offset pixel to move strings a little bit (default=0)
        """

        x = int(((((DISPLAY_WIDTH / parts) / 2) + ((DISPLAY_WIDTH / parts) * part)) - (self.img_size[0] / 2)) + offset)

        self.draw_image(x)

    def draw_middle_position_icon(self):

        position_x = (DISPLAY_WIDTH - ((DISPLAY_WIDTH / 3) / 2) - (self.image.get_rect()[2] / 2))

        position_y = (self.y - (self.image.get_rect()[3] / 2))

        self.draw_image(x=position_x, y=position_y)

    def draw_image(self, x, y=None):
        """
        takes x from the functions above and the y from the class to render the image
        """

        if self.fillcolor:

            surface = self.image
            self.fill(surface, self.fillcolor)

            if not y:
                TFT.blit(surface, (x, self.y))
            else:
                TFT.blit(surface, (x, y))
        else:
            if not y:
                TFT.blit(self.image, (x, self.y))
            else:
                TFT.blit(self.image, (x, y))


class Update:
    @staticmethod
    def update_json():

        global threads, CONNECTION_ERROR

        thread = threading.Timer(300, Update.update_json)

        thread.start()

        threads.append(thread)

        try:

            current_endpoint = f'{server}/current'
            hourly_endpoint = f'{server}/forecast/hourly'
            daily_endpoint = f'{server}/forecast/daily'

            print(f'connecting to server: {server}')

            options = str(f'&postal_code={WEATHERBIT_POSTALCODE}&country={WEATHERBIT_COUNTRY}&lang={WEATHERBIT_LANG}')

            current_request_url = str(f'{current_endpoint}?key={WEATHERBIT_IO_KEY}{options}')
            hourly_request_url = str(f'{hourly_endpoint}?key={WEATHERBIT_IO_KEY}{options}&hours={WEATHERBIT_HOURS}')
            daily_request_url = str(f'{daily_endpoint}?key={WEATHERBIT_IO_KEY}{options}&days={WEATHERBIT_DAYS}')

            current_data = requests.get(current_request_url, headers=headers).json()
            hourly_data = requests.get(hourly_request_url, headers=headers).json()
            daily_data = requests.get(daily_request_url, headers=headers).json()

            data = {
                'current': current_data,
                'hourly': hourly_data,
                'daily': daily_data
            }

            with open(LOG_PATH + 'latest_weather.json', 'w') as outputfile:
                json.dump(data, outputfile, indent=2, sort_keys=True)

            print('\njson file saved')

            CONNECTION_ERROR = False

        except (requests.HTTPError, requests.ConnectionError):

            CONNECTION_ERROR = True

            print('Connection ERROR')

            pass

        DrawImage(WiFi_Path, 5, size=15, fillcolor=BLUE).left()
        pygame.display.update()

    @staticmethod
    def read_json():

        global threads, json_data, REFRESH_ERROR

        thread = threading.Timer(30, Update.read_json)

        thread.start()

        threads.append(thread)

        try:

            data = open(LOG_PATH + 'latest_weather.json').read()

            new_json_data = json.loads(data)

            print('\njson file read by module')

            json_data = new_json_data

            REFRESH_ERROR = False

        except IOError:

            REFRESH_ERROR = True

            print('ERROR - json file read by module')

        DrawImage(Path_Path, 5, size=15, fillcolor=BLUE).right(-5)
        pygame.display.update()

        time.sleep(1)

        Update.icon_path()

    @staticmethod
    def icon_path():

        global WeatherIcon_Path, ForeCastIcon_Day_1_Path, \
            ForeCastIcon_Day_2_Path, ForeCastIcon_Day_3_Path, PRECIPTYPE, PRECIPCOLOR

        folder_path = ICON_PATH
        icon_extension = '.png'

        updated_list = []

        icon = json_data['current']['data'][0]['weather']['icon']

        forecast_icon_1 = json_data['daily']['data'][1]['weather']['icon']
        forecast_icon_2 = json_data['daily']['data'][2]['weather']['icon']
        forecast_icon_3 = json_data['daily']['data'][3]['weather']['icon']

        forecast = (str(icon), str(forecast_icon_1), str(forecast_icon_2), str(forecast_icon_3))

        print(forecast)

        WeatherIcon_Path = folder_path + forecast[0] + icon_extension

        ForeCastIcon_Day_1_Path = folder_path + forecast[1] + icon_extension
        ForeCastIcon_Day_2_Path = folder_path + forecast[2] + icon_extension
        ForeCastIcon_Day_3_Path = folder_path + forecast[3] + icon_extension

        path_list = [WeatherIcon_Path, ForeCastIcon_Day_1_Path,
                     ForeCastIcon_Day_2_Path, ForeCastIcon_Day_3_Path]

        print('\nvalidating path: {}\n'.format(path_list))

        for path in path_list:

            if os.path.isfile(path):

                print('TRUE :', path)

                updated_list.append(path)

            else:

                print('FALSE :', path)

                updated_list.append(ICON_PATH + 'unknown.png')

        WeatherIcon_Path = updated_list[0]
        ForeCastIcon_Day_1_Path = updated_list[1]
        ForeCastIcon_Day_2_Path = updated_list[2]
        ForeCastIcon_Day_3_Path = updated_list[3]

        global PATH_ERROR

        if any("unknown" in s for s in updated_list):

            PATH_ERROR = True

        else:

            PATH_ERROR = False

        print('\nupdate path for icons: {}'.format(updated_list))

        Update.get_precip_type()

        DrawImage(Refresh_Path, 5, size=15, fillcolor=BLUE).right(7)
        pygame.display.update()

    @staticmethod
    def get_precip_type():

        global json_data, PRECIPCOLOR, PRECIPTYPE

        pop = int(json_data['hourly']['data'][0]['pop'])
        rain = float(json_data['hourly']['data'][0]['precip'])
        snow = float(json_data['hourly']['data'][0]['snow'])

        if pop == 0:

            PRECIPTYPE = theme['LOCALE']['PRECIP_STR']
            PRECIPCOLOR = GREEN

        else:

            if rain > 0 and pop > 0:

                PRECIPTYPE = theme['LOCALE']['RAIN_STR']
                PRECIPCOLOR = BLUE

            elif snow > 0 and pop > 0:

                PRECIPTYPE = theme['LOCALE']['SNOW_STR']
                PRECIPCOLOR = WHITE

        print('\nupdate PRECIPTYPE to: {}'.format(PRECIPTYPE))
        print('\nupdate PRECIPCOLOR to: {}'.format(PRECIPCOLOR))
        print('\nupdated PATH')

    @staticmethod
    def run():
        Update.update_json()
        Update.read_json()


def convert_timestamp(timestamp, param_string):

    """
    :param timestamp: takes a normal integer unix timestamp
    :param param_string: use the default convert timestamp to timestring options
    :return: a converted string from timestamp
    """
    timestring = str(datetime.datetime.fromtimestamp(int(timestamp)).astimezone().strftime(param_string))

    return timestring


def draw_moon_layer(y):

    # based on @miyaichi's fork -> great idea :)
    size = 60
    dt = datetime.datetime.fromtimestamp(json_data['daily']['data'][0]['ts'])
    moon_age = (((dt.year - 11) % 19) * 11 + [0, 2, 0, 2, 2, 4, 5, 6, 7, 8, 9, 10][dt.month - 1] + dt.day) % 30

    image = pygame.Surface((size, size))
    image.fill(BLACK)
    image.set_colorkey(BLACK)
    radius = int(size / 2)

    # draw light side of the moon
    pygame.gfxdraw.filled_circle(image, radius, radius, radius, WHITE)
    pygame.gfxdraw.aacircle(image, radius, radius, radius, BLACK)

    # draw dark side of the moon
    theta = moon_age / 14.765 * math.pi
    sum_x = sum_length = 0
    for _y in range(-radius, radius, 1):
        alpha = math.acos(_y / radius)
        x = radius * math.sin(alpha)
        length = radius * math.cos(theta) * math.sin(alpha)
        if moon_age < 15:
            start = (radius - x, radius + _y)
            end = (radius + length, radius + _y)
        else:
            start = (radius - length, radius + _y)
            end = (radius + x, radius + _y)
        pygame.gfxdraw.line(image, int(start[0]), int(start[1]), int(end[0]), int(end[1]), DARK_GRAY)
        sum_x += 2 * x
        sum_length += end[0] - start[0]

    print(f'moon phase age: {moon_age} percentage: {round(100 - (sum_length / sum_x) * 100, 1)}')

    x = (DISPLAY_WIDTH / 2) - (size / 2)

    TFT.blit(image, (x, y))


def draw_wind_layer(y):

    angle = json_data['current']['data'][0]['wind_dir']

    # center the wind direction icon and circle on surface
    DrawImage(ICON_PATH + 'circle.png', y, size=30, fillcolor=WHITE).draw_middle_position_icon()
    DrawImage(ICON_PATH + 'arrow.png', y, size=30, fillcolor=RED, angle=-angle).draw_middle_position_icon()

    print('\nwind direction: {}'.format(angle))


def draw_image_layer():
    if CONNECTION_ERROR:

        DrawImage(WiFi_Path, 5, size=15, fillcolor=RED).left()

    else:

        DrawImage(WiFi_Path, 5, size=15, fillcolor=GREEN).left()

    if REFRESH_ERROR:

        DrawImage(Refresh_Path, 5, size=15, fillcolor=RED).right(7)

    else:

        DrawImage(Refresh_Path, 5, size=15, fillcolor=GREEN).right(7)

    if PATH_ERROR:

        DrawImage(Path_Path, 5, size=15, fillcolor=RED).right(-5)

    else:

        DrawImage(Path_Path, 5, size=15, fillcolor=GREEN).right(-5)

    DrawImage(WeatherIcon_Path, 70, size=100).center(2, 0, offset=10)

    if PRECIPTYPE == theme['LOCALE']['RAIN_STR']:

        DrawImage(PrecipRain_Path, 140, size=20).right(45)

    elif PRECIPTYPE == theme['LOCALE']['SNOW_STR']:

        DrawImage(PrecipSnow_Path, 140, size=20).right(50)

    DrawImage(ForeCastIcon_Day_1_Path, 200, size=50).center(3, 0)
    DrawImage(ForeCastIcon_Day_2_Path, 200, size=50).center(3, 1)
    DrawImage(ForeCastIcon_Day_3_Path, 200, size=50).center(3, 2)

    DrawImage(SunRise_Path, 260, size=25).left()
    DrawImage(SunSet_Path, 290, size=25).left()

    draw_moon_layer(255)
    draw_wind_layer(285)

    print('\n' + WeatherIcon_Path)
    print(ForeCastIcon_Day_1_Path)
    print(ForeCastIcon_Day_2_Path)
    print(ForeCastIcon_Day_3_Path)


def draw_time_layer():
    timestamp = time.time()

    date_time_string = convert_timestamp(timestamp, '%H:%M:%S')
    date_day_string = convert_timestamp(timestamp, '%A - %d. %b %Y')

    print('\nDay: {}'.format(date_day_string))
    print('Time: {}'.format(date_time_string))

    DrawString(date_day_string, date_font, WHITE, 5).center(1, 0)
    DrawString(date_time_string, font_big_bold, WHITE, 20).center(1, 0)


def draw_text_layer():
    current_forecast = json_data['current']['data'][0]

    summary_string = current_forecast['weather']['description']
    temp_out_string = str(current_forecast['temp']) + '°C'
    rain_string = str(int(json_data['hourly']['data'][0]['pop'])) + ' %'

    daily_forecast = json_data['daily']['data']

    forecast_day_1_string = convert_timestamp(time.mktime(time.strptime(daily_forecast[1]['datetime'], '%Y-%m-%d')), '%a')
    forecast_day_2_string = convert_timestamp(time.mktime(time.strptime(daily_forecast[2]['datetime'], '%Y-%m-%d')), '%a')
    forecast_day_3_string = convert_timestamp(time.mktime(time.strptime(daily_forecast[3]['datetime'], '%Y-%m-%d')), '%a')

    forecast_day_1_min_max_string = str(int(daily_forecast[1]['low_temp'])) + ' | ' + str(
        int(daily_forecast[1]['high_temp']))

    forecast_day_2_min_max_string = str(int(daily_forecast[2]['low_temp'])) + ' | ' + str(
        int(daily_forecast[2]['high_temp']))

    forecast_day_3_min_max_string = str(int(daily_forecast[3]['low_temp'])) + ' | ' + str(
        int(daily_forecast[3]['high_temp']))

    wind_direction_string = current_forecast['wind_cdir']

    sunrise_string = convert_timestamp(daily_forecast[0]['sunrise_ts'], '%H:%M')
    sunset_string = convert_timestamp(daily_forecast[0]['sunset_ts'], '%H:%M')

    wind_speed_string = str(round((float(current_forecast['wind_spd']) * 3.6), 1)) + ' km/h'

    draw_time_layer()

    DrawString(summary_string, font_small_bold, VIOLET, 55).center(1, 0)

    DrawString(temp_out_string, font_big, ORANGE, 75).right()

    DrawString(rain_string, font_big, PRECIPCOLOR, 105).right()
    DrawString(PRECIPTYPE, font_small_bold, PRECIPCOLOR, 140).right()

    DrawString(forecast_day_1_string.upper(), font_small_bold, ORANGE, 165).center(3, 0)
    DrawString(forecast_day_2_string.upper(), font_small_bold, ORANGE, 165).center(3, 1)
    DrawString(forecast_day_3_string.upper(), font_small_bold, ORANGE, 165).center(3, 2)

    DrawString(forecast_day_1_min_max_string, font_small_bold, WHITE, 180).center(3, 0)
    DrawString(forecast_day_2_min_max_string, font_small_bold, WHITE, 180).center(3, 1)
    DrawString(forecast_day_3_min_max_string, font_small_bold, WHITE, 180).center(3, 2)

    DrawString(sunrise_string, font_small_bold, WHITE, 265).left(30)
    DrawString(sunset_string, font_small_bold, WHITE, 292).left(30)

    DrawString(wind_direction_string, font_small_bold, WHITE, 250).center(3, 2)
    DrawString(wind_speed_string, font_small_bold, WHITE, 300).center(3, 2)

    print('\nsummary: {}'.format(summary_string))
    print('temp out: {}'.format(temp_out_string))
    print('{}: {}'.format(PRECIPTYPE, rain_string))
    print('forecast: '
          + forecast_day_1_string + ' ' + forecast_day_1_min_max_string + ' ; '
          + forecast_day_2_string + ' ' + forecast_day_2_min_max_string + ' ; '
          + forecast_day_3_string + ' ' + forecast_day_3_min_max_string
          )
    print('sunrise: {} ; sunset {}'.format(sunrise_string, sunset_string))
    print('WindSpeed: {}'.format(wind_speed_string))


def draw_to_tft():
    TFT.fill(BLACK)

    draw_image_layer()
    draw_text_layer()

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

        draw_to_tft()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                running = False

                quit_all()

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    running = False

                    quit_all()

                elif event.key == pygame.K_SPACE:
                    pygame.image.save(TFT, f'screenshot-{convert_timestamp(time.time(), "%Y-%m-%d %H-%M-%S")}.png')
                    print('SPACE')

    quit_all()


if __name__ == '__main__':

    try:

        loop()

    except KeyboardInterrupt:

        quit_all()
