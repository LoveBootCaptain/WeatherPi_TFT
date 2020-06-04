#!/usr/bin/env python3
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
import logging
import math
import os
import sys
import threading
import time
import random

import pygame
import requests
from PIL import Image, ImageDraw
from functools import lru_cache

PATH = sys.path[0] + '/'

# create logger
logger = logging.getLogger(__package__)
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger.setLevel(logging.INFO)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

config_data = open(PATH + 'config.json').read()
config = json.loads(config_data)

theme_config = config["THEME"]

theme_settings = open(PATH + theme_config).read()
theme = json.loads(theme_settings)

# pygame.init()
pygame.display.init()
pygame.mixer.quit()
pygame.font.init()
pygame.mouse.set_visible(True)

server = config['WEATHERBIT_URL']
headers = {}

locale.setlocale(locale.LC_ALL, (config['LOCALE']['ISO'], 'UTF-8'))

try:
    # if you do local development you can add a mock server (e.g. from postman.io our your homebrew solution)
    # simple add this variables to your config.json to save api-requests
    # or to create your own custom test data for your own dashboard views)
    if config['ENV'] == 'DEV':
        server = config['MOCKSERVER_URL']
        WEATHERBIT_IO_KEY = config['WEATHERBIT_DEV_KEY']
        headers = {'X-Api-Key': f'{config["MOCKSERVER_API_KEY"]}'}

    elif config['ENV'] == 'STAGE':
        WEATHERBIT_IO_KEY = config['WEATHERBIT_DEV_KEY']

    elif config['ENV'] == 'Pi':
        if config['DISPLAY']['FRAMEBUFFER'] is not False:
            # using the dashboard on a raspberry with tft displays might make this necessary
            os.putenv('SDL_FBDEV', config['DISPLAY']['FRAMEBUFFER'])
            os.environ['SDL_VIDEODRIVER'] = 'fbcon'

        WEATHERBIT_IO_KEY = config['WEATHERBIT_IO_KEY']
        pygame.mouse.set_visible(False)

    logger.info(f"STARTING IN {config['ENV']} MODE")


except Exception as config_ex:
    logger.warning(config_ex)
    quit()

clock = pygame.time.Clock()

pwm = config['DISPLAY']['PWM']

if pwm:
    logger.info(f'set PWM for brightness control to PIN {pwm}')
    os.system(f"gpio -g mode {pwm} pwm")
else:
    logger.info('no PWM for brightness control configured')

# theme settings from theme config
DISPLAY_WIDTH = config["DISPLAY"]["WIDTH"]
DISPLAY_HEIGHT = config["DISPLAY"]["HEIGHT"]

SURFACE_WIDTH = 240
SURFACE_HEIGHT = 320

SCALE = int(DISPLAY_WIDTH / SURFACE_WIDTH)
FPS = config['DISPLAY']['FPS']

BACKGROUND = tuple(theme["COLOR"]["BACKGROUND"])
MAIN_FONT = tuple(theme["COLOR"]["MAIN_FONT"])
BLACK = tuple(theme["COLOR"]["BLACK"])
DARK_GRAY = tuple(theme["COLOR"]["DARK_GRAY"])
WHITE = tuple(theme["COLOR"]["WHITE"])
RED = tuple(theme["COLOR"]["RED"])
GREEN = tuple(theme["COLOR"]["GREEN"])
BLUE = tuple(theme["COLOR"]["BLUE"])
LIGHT_BLUE = tuple((BLUE[0], 210, BLUE[2]))
DARK_BLUE = tuple((BLUE[0], 100, 255))
YELLOW = tuple(theme["COLOR"]["YELLOW"])
ORANGE = tuple(theme["COLOR"]["ORANGE"])
VIOLET = tuple(theme["COLOR"]["VIOLET"])
COLOR_LIST = [BLUE, LIGHT_BLUE, DARK_BLUE]

FONT_MEDIUM = theme["FONT"]["MEDIUM"]
FONT_BOLD = theme["FONT"]["BOLD"]
DATE_SIZE = theme["FONT"]["DATE_SIZE"]
CLOCK_SIZE = theme["FONT"]["CLOCK_SIZE"]
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

TFT = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.FULLSCREEN if config['ENV'] == 'Pi' else 0)
TFT.fill(BACKGROUND)

tft = pygame.Surface((SURFACE_WIDTH, SURFACE_HEIGHT))
pygame.display.set_caption('WeatherPiTFT')

font_small = pygame.font.Font(FONT_PATH + FONT_MEDIUM, SMALL_SIZE)
font_big = pygame.font.Font(FONT_PATH + FONT_MEDIUM, BIG_SIZE)

date_font = pygame.font.Font(FONT_PATH + FONT_BOLD, DATE_SIZE)
clock_font = pygame.font.Font(FONT_PATH + FONT_BOLD, CLOCK_SIZE)
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

CONNECTION = True
READING = True
UPDATING = True

threads = []

json_data = {}


@lru_cache()
class Particles(object):
    def __init__(self):
        self.size = 20
        self.count = 15
        self.surf = pygame.Surface((self.size, self.size))

    def create_particle_list(self):

        particle_list = []

        for i in range(self.count):
            x = random.randrange(0, self.size)
            y = random.randrange(0, self.size)
            w = 1
            h = random.randint(2, 3)
            speed = random.choice([1, 2, 3])
            color = random.choice(COLOR_LIST)
            direct = random.choice([0, 0, 1])
            particle_list.append([x, y, w, h, speed, color, direct])
        return particle_list

    def move(self, surf, particle_list):
        # Process each snow flake in the list
        self.surf.fill(BACKGROUND)
        self.surf.set_colorkey(BACKGROUND)

        if not PRECIPTYPE == config['LOCALE']['PRECIP_STR']:

            for i in range(len(particle_list)):

                particle = particle_list[i]
                x, y, w, h, speed, color, direct = particle

                # Draw the snow flake
                if PRECIPTYPE == config['LOCALE']['RAIN_STR']:
                    pygame.draw.rect(self.surf, color, (x, y, w, h), 0)
                else:
                    pygame.draw.rect(self.surf, PRECIPCOLOR, (x, y, 2, 2), 0)

                # Move the snow flake down one pixel
                particle_list[i][1] += speed if PRECIPTYPE == config['LOCALE']['RAIN_STR'] else 1
                if random.choice([True, False]):
                    if PRECIPTYPE == config['LOCALE']['SNOW_STR']:
                        particle_list[i][0] += 1 if direct else 0

                # If the snow flake has moved off the bottom of the screen
                if particle_list[i][1] > self.size:
                    # Reset it just above the top
                    y -= self.size
                    particle_list[i][1] = y
                    # Give it a new x position
                    x = random.randrange(0, self.size)
                    particle_list[i][0] = x
            # pygame.time.delay(75)

            surf.blit(self.surf, (155, 140))


my_particles = Particles()
my_particles_list = my_particles.create_particle_list()


@lru_cache()
class DrawString:
    def __init__(self, string: str, font, color, y: int):
        """
        :param string: the input string
        :param font: the fonts object
        :param color: a rgb color tuple
        :param y: the y position where you want to render the text
        """
        self.string = string
        self.font = font
        self.color = color
        self.y = int(y)
        self.size = self.font.size(self.string)

    def left(self, offset=0):
        """
        :param offset: define some offset pixel to move strings a little bit more left (default=0)
        """

        x = int(10 + offset)

        self.draw_string(x)

    def right(self, offset=0):
        """
        :param offset: define some offset pixel to move strings a little bit more right (default=0)
        """

        x = int((SURFACE_WIDTH - self.size[0] - 10) - offset)

        self.draw_string(x)

    def center(self, parts, part, offset=0):
        """
        :param parts: define in how many parts you want to split your display
        :param part: the part in which you want to render text (first part is 0, second is 1, etc.)
        :param offset: define some offset pixel to move strings a little bit (default=0)
        """

        x = int(((((SURFACE_WIDTH / parts) / 2) + ((SURFACE_WIDTH / parts) * part)) - (self.size[0] / 2)) + offset)

        self.draw_string(x)

    def draw_string(self, x):
        """
        takes x and y from the functions above and render the fonts
        """

        tft.blit(self.font.render(self.string, True, self.color), (x, self.y))


@lru_cache()
class DrawImage:
    def __init__(self, image_path, y=None, size=None, fillcolor=None, angle=None):
        """
        :param image_path: the path to the image you want to render
        :param y: the y-postion of the image you want to render
        """

        self.image_path = image_path
        self.image = Image.open(self.image_path)
        self.y = y
        self.img_size = self.image.size
        self.size = size
        self.angle = angle

        if angle:
            self.image = self.image.rotate(self.angle, resample=Image.BICUBIC)

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

    @staticmethod
    def fill(surface, fillcolor: tuple):
        """converts the color on an icon"""
        w, h = surface.get_size()
        r, g, b = fillcolor
        for x in range(w):
            for y in range(h):
                a: int = surface.get_at((x, y))[3]
                color = pygame.Color(r, g, b, a)
                surface.set_at((x, y), color)

    def left(self, offset=0):
        """
        :param offset: define some offset pixel to move image a little bit more left(default=0)
        """

        x = int(10 + offset)

        self.draw_image(x)

    def right(self, offset=0):
        """
        :param offset: define some offset pixel to move image a little bit more right (default=0)
        """

        x = int((SURFACE_WIDTH - self.img_size[0] - 10) - offset)

        self.draw_image(x)

    def center(self, parts, part, offset=0):
        """
        :param parts: define in how many parts you want to split your display
        :param part: the part in which you want to render text (first part is 0, second is 1, etc.)
        :param offset: define some offset pixel to move strings a little bit (default=0)
        """

        x = int(((((SURFACE_WIDTH / parts) / 2) + ((SURFACE_WIDTH / parts) * part)) - (self.img_size[0] / 2)) + offset)

        self.draw_image(x)

    def draw_middle_position_icon(self):

        position_x = int((SURFACE_WIDTH - ((SURFACE_WIDTH / 3) / 2) - (self.image.get_rect()[2] / 2)))

        position_y = int((self.y - (self.image.get_rect()[3] / 2)))

        self.draw_image(x=position_x, _y=position_y)

    def draw_position(self, pos: tuple):
        x, y = pos
        if y == 0:
            y += 1
        self.draw_image(x=int(x), _y=int(y))

    def draw_image(self, x, _y=None):
        """
        takes x from the functions above and the y from the class to render the image
        """

        if self.fillcolor:

            surface = self.image
            self.fill(surface, self.fillcolor)

            if _y:
                tft.blit(surface, (x, int(_y)))
            else:
                tft.blit(surface, (x, self.y))
        else:
            if _y:
                tft.blit(self.image, (x, int(_y)))
            else:
                tft.blit(self.image, (x, self.y))


class Update:

    @staticmethod
    def update_json():

        brightness = get_brightness()

        os.system(f'gpio -g pwm {pwm} {brightness}') if pwm else None

        logger.info(f'set brightness: {brightness}, pwm configured: {pwm}')

        global threads, CONNECTION_ERROR, CONNECTION

        thread = threading.Timer(config["TIMER"]["UPDATE"], Update.update_json)

        thread.start()

        threads.append(thread)

        CONNECTION = pygame.time.get_ticks() + 1500  # 1.5 seconds

        try:

            current_endpoint = f'{server}/current'
            daily_endpoint = f'{server}/forecast/daily'

            logger.info(f'connecting to server: {server}')

            options = str(f'&postal_code={WEATHERBIT_POSTALCODE}&country={WEATHERBIT_COUNTRY}&lang={WEATHERBIT_LANG}')

            current_request_url = str(f'{current_endpoint}?key={WEATHERBIT_IO_KEY}{options}')
            daily_request_url = str(f'{daily_endpoint}?key={WEATHERBIT_IO_KEY}{options}&days={WEATHERBIT_DAYS}')

            current_data = requests.get(current_request_url, headers=headers).json()
            daily_data = requests.get(daily_request_url, headers=headers).json()

            data = {
                'current': current_data,
                'daily': daily_data
            }

            with open(LOG_PATH + 'latest_weather.json', 'w') as outputfile:
                json.dump(data, outputfile, indent=2, sort_keys=True)

            logger.info('json file saved')

            CONNECTION_ERROR = False

        except (requests.HTTPError, requests.ConnectionError) as update_ex:

            CONNECTION_ERROR = True

            logger.warning(f'Connection ERROR: {update_ex}')

    @staticmethod
    def read_json():

        global threads, json_data, REFRESH_ERROR, READING

        thread = threading.Timer(config["TIMER"]["RELOAD"], Update.read_json)

        thread.start()

        threads.append(thread)

        READING = pygame.time.get_ticks() + 1500  # 1.5 seconds

        try:

            data = open(LOG_PATH + 'latest_weather.json').read()

            new_json_data = json.loads(data)

            logger.info('json file read by module')
            logger.info(f'{new_json_data}')

            json_data = new_json_data

            REFRESH_ERROR = False

        except IOError as read_ex:

            REFRESH_ERROR = True

            logger.warning(f'ERROR - json file read by module: {read_ex}')

        Update.icon_path()

    @staticmethod
    def icon_path():

        global WeatherIcon_Path, ForeCastIcon_Day_1_Path, \
            ForeCastIcon_Day_2_Path, ForeCastIcon_Day_3_Path, PRECIPTYPE, PRECIPCOLOR, UPDATING

        pygame.time.delay(1500)
        UPDATING = pygame.time.get_ticks() + 1500  # 1.5 seconds

        folder_path = ICON_PATH
        icon_extension = '.png'

        updated_list = []

        icon = json_data['current']['data'][0]['weather']['icon']

        forecast_icon_1 = json_data['daily']['data'][1]['weather']['icon']
        forecast_icon_2 = json_data['daily']['data'][2]['weather']['icon']
        forecast_icon_3 = json_data['daily']['data'][3]['weather']['icon']

        forecast = (str(icon), str(forecast_icon_1), str(forecast_icon_2), str(forecast_icon_3))

        logger.debug(forecast)

        WeatherIcon_Path = folder_path + forecast[0] + icon_extension

        ForeCastIcon_Day_1_Path = folder_path + forecast[1] + icon_extension
        ForeCastIcon_Day_2_Path = folder_path + forecast[2] + icon_extension
        ForeCastIcon_Day_3_Path = folder_path + forecast[3] + icon_extension

        path_list = [WeatherIcon_Path, ForeCastIcon_Day_1_Path,
                     ForeCastIcon_Day_2_Path, ForeCastIcon_Day_3_Path]

        logger.debug(f'validating path: {path_list}')

        for path in path_list:

            if os.path.isfile(path):

                logger.debug(f'TRUE : {path}')

                updated_list.append(path)

            else:

                logger.warning(f'FALSE : {path}')

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

        logger.info(f'update path for icons: {updated_list}')

        Update.get_precip_type()

    @staticmethod
    def get_precip_type():

        global json_data, PRECIPCOLOR, PRECIPTYPE

        pop = int(json_data['daily']['data'][0]['pop'])
        rain = float(json_data['daily']['data'][0]['precip'])
        snow = float(json_data['daily']['data'][0]['snow'])

        if pop == 0:

            PRECIPTYPE = config['LOCALE']['PRECIP_STR']
            PRECIPCOLOR = GREEN

        else:

            if rain > 0 and pop > 0:

                PRECIPTYPE = config['LOCALE']['RAIN_STR']
                PRECIPCOLOR = BLUE

            elif snow > 0 and pop > 0:

                PRECIPTYPE = config['LOCALE']['SNOW_STR']
                PRECIPCOLOR = WHITE

        logger.info(f'update PRECIPPOP to: {pop} %')
        logger.info(f'update PRECIPTYPE to: {PRECIPTYPE}')
        logger.info(f'update PRECIPCOLOR to: {PRECIPCOLOR}')

    @staticmethod
    def run():
        Update.update_json()
        Update.read_json()


def get_brightness():
    current_time = time.time()
    current_time = int(convert_timestamp(current_time, '%H'))

    return 25 if current_time >= 20 or current_time <= 5 else 100


def convert_timestamp(timestamp, param_string):
    """
    :param timestamp: takes a normal integer unix timestamp
    :param param_string: use the default convert timestamp to timestring options
    :return: a converted string from timestamp
    """
    timestring = str(datetime.datetime.fromtimestamp(int(timestamp)).astimezone().strftime(param_string))

    return timestring


def draw_moon_layer(y, size):
    # based on @miyaichi's fork -> great idea :)
    _size = 300
    dt = datetime.datetime.fromtimestamp(json_data['daily']['data'][0]['ts'])
    moon_age = (((dt.year - 11) % 19) * 11 + [0, 2, 0, 2, 2, 4, 5, 6, 7, 8, 9, 10][dt.month - 1] + dt.day) % 30

    image = Image.new("RGBA", (_size + 2, _size + 2))
    draw = ImageDraw.Draw(image)

    radius = int(_size / 2)

    # draw full moon
    draw.ellipse([(1, 1), (_size, _size)], fill=WHITE)

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

        draw.line((start, end), fill=DARK_GRAY)

        sum_x += 2 * x
        sum_length += end[0] - start[0]

    logger.debug(f'moon phase age: {moon_age} percentage: {round(100 - (sum_length / sum_x) * 100, 1)}')

    image = image.resize((size, size), Image.LANCZOS)
    image = pygame.image.fromstring(image.tobytes(), image.size, image.mode)

    x = (SURFACE_WIDTH / 2) - (size / 2)

    tft.blit(image, (x, y))


def draw_wind_layer(y):
    angle = json_data['current']['data'][0]['wind_dir']

    # center the wind direction icon and circle on surface
    DrawImage(ICON_PATH + 'circle.png', y, size=30, fillcolor=WHITE).draw_middle_position_icon()
    DrawImage(ICON_PATH + 'arrow.png', y, size=30, fillcolor=RED, angle=-angle).draw_middle_position_icon()

    logger.debug(f'wind direction: {angle}')


def draw_statusbar():

    global CONNECTION, READING, UPDATING

    DrawImage(WiFi_Path, 5, size=15, fillcolor=RED if CONNECTION_ERROR else GREEN).left()

    DrawImage(Refresh_Path, 5, size=15, fillcolor=RED if REFRESH_ERROR else GREEN).right(7)

    DrawImage(Path_Path, 5, size=15, fillcolor=RED if PATH_ERROR else GREEN).right(-5)

    if CONNECTION:
        DrawImage(WiFi_Path, 5, size=15, fillcolor=BLUE).left()
        if pygame.time.get_ticks() >= CONNECTION:
            CONNECTION = None

    if READING:
        DrawImage(Path_Path, 5, size=15, fillcolor=BLUE).right(-5)
        if pygame.time.get_ticks() >= READING:
            READING = None

    if UPDATING:
        DrawImage(Refresh_Path, 5, size=15, fillcolor=BLUE).right(7)
        if pygame.time.get_ticks() >= UPDATING:
            UPDATING = None


def draw_image_layer():

    draw_statusbar()

    DrawImage(WeatherIcon_Path, 68, size=100).center(2, 0, offset=10)

    DrawImage(ForeCastIcon_Day_1_Path, 200, size=50).center(3, 0)
    DrawImage(ForeCastIcon_Day_2_Path, 200, size=50).center(3, 1)
    DrawImage(ForeCastIcon_Day_3_Path, 200, size=50).center(3, 2)

    DrawImage(SunRise_Path, 260, size=25).left()
    DrawImage(SunSet_Path, 290, size=25).left()

    draw_moon_layer(255, 60)
    draw_wind_layer(285)

    logger.debug(WeatherIcon_Path)
    logger.debug(ForeCastIcon_Day_1_Path)
    logger.debug(ForeCastIcon_Day_2_Path)
    logger.debug(ForeCastIcon_Day_3_Path)


def draw_fps():
    DrawString(str(int(clock.get_fps())), font_small_bold, RED, 20).left()


def draw_time_layer():
    timestamp = time.time()

    date_day_string = convert_timestamp(timestamp, theme["DATE_FORMAT"]["DATE"])
    date_time_string = convert_timestamp(timestamp, theme["DATE_FORMAT"]["TIME"])

    logger.debug(f'Day: {date_day_string}')
    logger.debug(f'Time: {date_time_string}')

    DrawString(date_day_string, date_font, MAIN_FONT, 0).center(1, 0)
    DrawString(date_time_string, clock_font, MAIN_FONT, 15).center(1, 0)


def draw_text_layer():
    current_forecast = json_data['current']['data'][0]

    summary_string = current_forecast['weather']['description']
    temp_out_string = str(int(current_forecast['temp'])) + '°C'
    rain_string = str(int(json_data['daily']['data'][0]['pop'])) + ' %'

    daily_forecast = json_data['daily']['data']

    forecast_day_1_string = convert_timestamp(time.mktime(time.strptime(daily_forecast[1]['datetime'], '%Y-%m-%d')),
                                              theme["DATE_FORMAT"]["FORECAST_DAY"])
    forecast_day_2_string = convert_timestamp(time.mktime(time.strptime(daily_forecast[2]['datetime'], '%Y-%m-%d')),
                                              theme["DATE_FORMAT"]["FORECAST_DAY"])
    forecast_day_3_string = convert_timestamp(time.mktime(time.strptime(daily_forecast[3]['datetime'], '%Y-%m-%d')),
                                              theme["DATE_FORMAT"]["FORECAST_DAY"])

    forecast_day_1_min_max_string = str(int(daily_forecast[1]['low_temp'])) + ' | ' + str(
        int(daily_forecast[1]['high_temp']))

    forecast_day_2_min_max_string = str(int(daily_forecast[2]['low_temp'])) + ' | ' + str(
        int(daily_forecast[2]['high_temp']))

    forecast_day_3_min_max_string = str(int(daily_forecast[3]['low_temp'])) + ' | ' + str(
        int(daily_forecast[3]['high_temp']))

    wind_direction_string = current_forecast['wind_cdir']

    sunrise_string = convert_timestamp(daily_forecast[0]['sunrise_ts'], theme["DATE_FORMAT"]["SUNRISE_SUNSET"])
    sunset_string = convert_timestamp(daily_forecast[0]['sunset_ts'], theme["DATE_FORMAT"]["SUNRISE_SUNSET"])

    wind_speed_string = str(round((float(current_forecast['wind_spd']) * 3.6), 1)) + ' km/h'
    draw_time_layer()

    DrawString(summary_string, font_small_bold, VIOLET, 50).center(1, 0)

    DrawString(temp_out_string, font_big, ORANGE, 75).right()

    DrawString(rain_string, font_big, PRECIPCOLOR, 105).right()
    DrawString(PRECIPTYPE, font_small_bold, PRECIPCOLOR, 140).right()

    DrawString(forecast_day_1_string, font_small_bold, ORANGE, 165).center(3, 0)
    DrawString(forecast_day_2_string, font_small_bold, ORANGE, 165).center(3, 1)
    DrawString(forecast_day_3_string, font_small_bold, ORANGE, 165).center(3, 2)

    DrawString(forecast_day_1_min_max_string, font_small_bold, MAIN_FONT, 180).center(3, 0)
    DrawString(forecast_day_2_min_max_string, font_small_bold, MAIN_FONT, 180).center(3, 1)
    DrawString(forecast_day_3_min_max_string, font_small_bold, MAIN_FONT, 180).center(3, 2)

    DrawString(sunrise_string, font_small_bold, MAIN_FONT, 265).left(30)
    DrawString(sunset_string, font_small_bold, MAIN_FONT, 292).left(30)

    DrawString(wind_direction_string, font_small_bold, MAIN_FONT, 250).center(3, 2)
    DrawString(wind_speed_string, font_small_bold, MAIN_FONT, 300).center(3, 2)

    logger.debug(f'summary: {summary_string}')
    logger.debug(f'temp out: {temp_out_string}')
    logger.debug(f'{PRECIPTYPE}: {rain_string}')
    logger.debug(f'forecast: '
                 f'{forecast_day_1_string} {forecast_day_1_min_max_string}; '
                 f'{forecast_day_2_string} {forecast_day_2_min_max_string}; '
                 f'{forecast_day_3_string} {forecast_day_3_min_max_string}')
    logger.debug(f'sunrise: {sunrise_string} ; sunset {sunset_string}')
    logger.debug(f'WindSpeed: {wind_speed_string}')


def draw_to_tft():
    tft.fill(BACKGROUND)
    if config["DISPLAY"]["SHOW_FPS"]:
        draw_fps()
    draw_image_layer()
    draw_text_layer()


def quit_all():

    global threads

    for thread in threads:
        logger.info(f'Thread killed {thread}')
        thread.cancel()
        thread.join()

    pygame.quit()
    sys.exit()


def draw_event(color=RED):
    pos = pygame.mouse.get_pos()
    size = 16
    new_pos = (pos[0] - size / 2, pos[1] - size / 2)
    DrawImage(ICON_PATH + 'circle.png', size=size, fillcolor=color).draw_position(new_pos)


def loop():

    Update.run()

    running = True

    while running:

        draw_to_tft()

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                running = False

                quit_all()

            elif event.type == pygame.MOUSEBUTTONDOWN:

                if pygame.MOUSEBUTTONDOWN:
                    draw_event()

            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:

                    running = False

                    quit_all()

                elif event.key == pygame.K_SPACE:
                    shot_time = convert_timestamp(time.time(), "%Y-%m-%d %H-%M-%S")
                    pygame.image.save(tft, f'screenshot-{shot_time}.png')
                    logger.info(f'Screenshot created at {shot_time}')

        my_particles.move(tft, my_particles_list)
        scaled_tft = pygame.transform.smoothscale(tft, (SURFACE_WIDTH * SCALE, SURFACE_HEIGHT * SCALE))
        _, _, w, h = scaled_tft.get_rect()

        pos = int((DISPLAY_WIDTH - (SURFACE_WIDTH * SCALE)) / 2), int((DISPLAY_HEIGHT - (SURFACE_HEIGHT * SCALE)) / 2)

        TFT.blit(pygame.transform.smoothscale(scaled_tft, (w, h)), pos)

        pygame.display.update()

        clock.tick(FPS)

    quit_all()


if __name__ == '__main__':

    try:

        loop()

    except KeyboardInterrupt:

        quit_all()
