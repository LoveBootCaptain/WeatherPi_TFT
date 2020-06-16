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
import random
import sys
import threading
import time

import pygame
import requests
from PIL import Image, ImageDraw

PATH = sys.path[0] + '/'
ICON_PATH = PATH + '/icons/'
FONT_PATH = PATH + '/fonts/'
LOG_PATH = PATH + '/logs/'

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

SERVER = config['WEATHERBIT_URL']
HEADERS = {}
WEATHERBIT_COUNTRY = config['WEATHERBIT_COUNTRY']
WEATHERBIT_LANG = config['WEATHERBIT_LANGUAGE']
WEATHERBIT_POSTALCODE = config['WEATHERBIT_POSTALCODE']
WEATHERBIT_HOURS = config['WEATHERBIT_HOURS']
WEATHERBIT_DAYS = config['WEATHERBIT_DAYS']
METRIC = config['LOCALE']['METRIC']

locale.setlocale(locale.LC_ALL, (config['LOCALE']['ISO'], 'UTF-8'))


try:
    # if you do local development you can add a mock server (e.g. from postman.io our your homebrew solution)
    # simple add this variables to your config.json to save api-requests
    # or to create your own custom test data for your own dashboard views)
    if config['ENV'] == 'DEV':
        SERVER = config['MOCKSERVER_URL']
        WEATHERBIT_IO_KEY = config['WEATHERBIT_DEV_KEY']
        HEADERS = {'X-Api-Key': f'{config["MOCKSERVER_API_KEY"]}'}

    elif config['ENV'] == 'STAGE':
        WEATHERBIT_IO_KEY = config['WEATHERBIT_DEV_KEY']

    elif config['ENV'] == 'Pi':
        if config['DISPLAY']['FRAMEBUFFER'] is not False:
            # using the dashboard on a raspberry with TFT displays might make this necessary
            os.putenv('SDL_FBDEV', config['DISPLAY']['FRAMEBUFFER'])
            os.environ["SDL_VIDEODRIVER"] = "fbcon"

        LOG_PATH = '/mnt/ramdisk/'
        WEATHERBIT_IO_KEY = config['WEATHERBIT_IO_KEY']

    logger.info(f"STARTING IN {config['ENV']} MODE")


except Exception as e:
    logger.warning(e)
    quit()

PWM = config['DISPLAY']['PWM']

if PWM:
    logger.info(f'set PWM for brightness control to PIN {PWM}')
    os.system(f"gpio -g mode {PWM} pwm")
else:
    logger.info('no PWM for brightness control configured')

# theme settings from theme config
DISPLAY_WIDTH = int(config["DISPLAY"]["WIDTH"])
DISPLAY_HEIGHT = int(config["DISPLAY"]["HEIGHT"])

SURFACE_WIDTH = 240
SURFACE_HEIGHT = 320

SCALE = float(DISPLAY_WIDTH / SURFACE_WIDTH)
FIT_SCREEN = (int((DISPLAY_WIDTH - (SURFACE_WIDTH * SCALE)) / 2), int((DISPLAY_HEIGHT - (SURFACE_HEIGHT * SCALE)) / 2))

FPS = config['DISPLAY']['FPS']
AA = config['DISPLAY']['AA']

pygame.display.init()
pygame.mixer.quit()
pygame.font.init()
pygame.mouse.set_visible(config['DISPLAY']['MOUSE'])
pygame.display.set_caption('WeatherPiTFT')

tft_surf = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.NOFRAME if config['ENV'] == 'Pi' else 0)

# the drawing area - everything will be drawn here before scaling and rendering on the display tft_surf
display_surf = pygame.Surface((SURFACE_WIDTH, SURFACE_HEIGHT))
# dynamic surface for status bar updates and dynamic values like fps
dynamic_surf = pygame.Surface((SURFACE_WIDTH, SURFACE_HEIGHT))
# exclusive surface for the time
time_surf = pygame.Surface((SURFACE_WIDTH, SURFACE_HEIGHT))
# exclusive surface for the mouse/touch events
mouse_surf = pygame.Surface((SURFACE_WIDTH, SURFACE_HEIGHT))
# surface for the weather data - will only be created once if the data is updated from the api
weather_surf = pygame.Surface((SURFACE_WIDTH, SURFACE_HEIGHT))

clock = pygame.time.Clock()

logger.info(f'display with {DISPLAY_WIDTH}px width and {DISPLAY_HEIGHT}px height is set to {FPS} FPS with AA {AA}')

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

FONT_SMALL = pygame.font.Font(FONT_PATH + FONT_MEDIUM, SMALL_SIZE)
FONT_SMALL_BOLD = pygame.font.Font(FONT_PATH + FONT_BOLD, SMALL_SIZE)
FONT_BIG = pygame.font.Font(FONT_PATH + FONT_MEDIUM, BIG_SIZE)
FONT_BIG_BOLD = pygame.font.Font(FONT_PATH + FONT_BOLD, BIG_SIZE)
DATE_FONT = pygame.font.Font(FONT_PATH + FONT_BOLD, DATE_SIZE)
CLOCK_FONT = pygame.font.Font(FONT_PATH + FONT_BOLD, CLOCK_SIZE)

WEATHERICON = 'unknown'

FORECASTICON_DAY_1 = 'unknown'
FORECASTICON_DAY_2 = 'unknown'
FORECASTICON_DAY_3 = 'unknown'

CONNECTION_ERROR = True
REFRESH_ERROR = True
PATH_ERROR = True
PRECIPTYPE = 'NULL'
PRECIPCOLOR = WHITE

CONNECTION = False
READING = False
UPDATING = False

THREADS = []

JSON_DATA = {}


def image_factory(image_path):
    result = {}
    for img in os.listdir(image_path):
        image_id = img.split('.')[0]
        if image_id == "":
            pass
        else:
            result[image_id] = Image.open(image_path + img)
    return result


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

            surf.blit(self.surf, (155, 140))


class DrawString:
    def __init__(self, surf, string: str, font, color, y: int):
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
        self.surf = surf

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

        self.surf.blit(self.font.render(self.string, True, self.color), (x, self.y))


class DrawImage:
    def __init__(self, surf, image=Image, y=None, size=None, fillcolor=None, angle=None):
        """
        :param image: image from the image_factory()
        :param y: the y-position of the image you want to render
        """
        self.image = image
        self.y = y
        self.img_size = self.image.size
        self.size = size
        self.angle = angle
        self.surf = surf

        if angle:
            self.image = self.image.rotate(self.angle, resample=Image.BICUBIC)

        if size:
            width, height = self.image.size
            if width >= height:
                width, height = (size, int(size / width * height))
            else:
                width, height = (int(size / width * height), size)

            new_image = self.image.resize((width, height), Image.LANCZOS if AA else Image.BILINEAR)
            self.image = new_image
            self.img_size = new_image.size

        self.fillcolor = fillcolor

        self.image = pygame.image.fromstring(self.image.tobytes(), self.image.size, self.image.mode)

    @staticmethod
    def fill(surface, fillcolor: tuple):
        """converts the color on an icon"""
        surface.set_colorkey(BACKGROUND)
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

        self.draw_image(draw_x=position_x, draw_y=position_y)

    def draw_position(self, pos: tuple):
        x, y = pos
        if y == 0:
            y += 1
        self.draw_image(draw_x=int(x), draw_y=int(y))

    def draw_image(self, draw_x, draw_y=None):
        """
        takes x from the functions above and the y from the class to render the image
        """

        if self.fillcolor:

            surface = self.image
            self.fill(surface, self.fillcolor)

            if draw_y:
                self.surf.blit(surface, (draw_x, int(draw_y)))
            else:
                self.surf.blit(surface, (draw_x, self.y))
        else:
            if draw_y:
                self.surf.blit(self.image, (draw_x, int(draw_y)))
            else:
                self.surf.blit(self.image, (draw_x, self.y))


class Update:

    @staticmethod
    def update_json():

        brightness = get_brightness()

        os.system(f'gpio -g pwm {PWM} {brightness}') if PWM is not False else logger.info('not setting pwm')

        logger.info(f'set brightness: {brightness}, pwm configured: {PWM}')

        global THREADS, CONNECTION_ERROR, CONNECTION

        thread = threading.Timer(config["TIMER"]["UPDATE"], Update.update_json)

        thread.start()

        THREADS.append(thread)

        CONNECTION = pygame.time.get_ticks() + 1500  # 1.5 seconds

        try:

            current_endpoint = f'{SERVER}/current'
            daily_endpoint = f'{SERVER}/forecast/daily'
            stats_endpoint = f'{SERVER}/subscription/usage'
            units = 'M' if METRIC else 'I'

            logger.info(f'connecting to server: {SERVER}')

            options = str(f'&postal_code={WEATHERBIT_POSTALCODE}&country={WEATHERBIT_COUNTRY}&lang={WEATHERBIT_LANG}&units={units}')

            current_request_url = str(f'{current_endpoint}?key={WEATHERBIT_IO_KEY}{options}')
            daily_request_url = str(f'{daily_endpoint}?key={WEATHERBIT_IO_KEY}{options}&days={WEATHERBIT_DAYS}')
            stats_request_url = str(f'{stats_endpoint}?key={WEATHERBIT_IO_KEY}')

            current_data = requests.get(current_request_url, headers=HEADERS).json()
            daily_data = requests.get(daily_request_url, headers=HEADERS).json()
            stats_data = requests.get(stats_request_url, headers=HEADERS).json()

            data = {
                'current': current_data,
                'daily': daily_data,
                'stats': stats_data
            }

            with open(LOG_PATH + 'latest_weather.json', 'w+') as outputfile:
                json.dump(data, outputfile, indent=2, sort_keys=True)

            logger.info('json file saved')

            CONNECTION_ERROR = False

        except (requests.HTTPError, requests.ConnectionError) as update_ex:

            CONNECTION_ERROR = True

            logger.warning(f'Connection ERROR: {update_ex}')

    @staticmethod
    def read_json():

        global THREADS, JSON_DATA, REFRESH_ERROR, READING

        thread = threading.Timer(config["TIMER"]["RELOAD"], Update.read_json)

        thread.start()

        THREADS.append(thread)

        READING = pygame.time.get_ticks() + 1500  # 1.5 seconds

        try:

            data = open(LOG_PATH + 'latest_weather.json').read()

            new_json_data = json.loads(data)

            logger.info('json file read by module')
            logger.info(f'{new_json_data}')

            JSON_DATA = new_json_data

            REFRESH_ERROR = False

        except IOError as read_ex:

            REFRESH_ERROR = True

            logger.warning(f'ERROR - json file read by module: {read_ex}')

        Update.icon_path()

    @staticmethod
    def icon_path():

        global WEATHERICON, FORECASTICON_DAY_1, \
            FORECASTICON_DAY_2, FORECASTICON_DAY_3, PRECIPTYPE, PRECIPCOLOR, UPDATING

        icon_extension = '.png'

        updated_list = []

        icon = JSON_DATA['current']['data'][0]['weather']['icon']

        forecast_icon_1 = JSON_DATA['daily']['data'][1]['weather']['icon']
        forecast_icon_2 = JSON_DATA['daily']['data'][2]['weather']['icon']
        forecast_icon_3 = JSON_DATA['daily']['data'][3]['weather']['icon']

        forecast = (str(icon), str(forecast_icon_1), str(forecast_icon_2), str(forecast_icon_3))

        logger.debug(forecast)

        logger.debug(f'validating path: {forecast}')

        for icon in forecast:

            if os.path.isfile(ICON_PATH + icon + icon_extension):

                logger.debug(f'TRUE : {icon}')

                updated_list.append(icon)

            else:

                logger.warning(f'FALSE : {icon}')

                updated_list.append('unknown')

        WEATHERICON = updated_list[0]
        FORECASTICON_DAY_1 = updated_list[1]
        FORECASTICON_DAY_2 = updated_list[2]
        FORECASTICON_DAY_3 = updated_list[3]

        global PATH_ERROR

        if any("unknown" in s for s in updated_list):

            PATH_ERROR = True

        else:

            PATH_ERROR = False

        logger.info(f'update path for icons: {updated_list}')

        Update.get_precip_type()

    @staticmethod
    def get_precip_type():

        global JSON_DATA, PRECIPCOLOR, PRECIPTYPE

        pop = int(JSON_DATA['daily']['data'][0]['pop'])
        rain = float(JSON_DATA['daily']['data'][0]['precip'])
        snow = float(JSON_DATA['daily']['data'][0]['snow'])

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

        Update.create_surface()

    @staticmethod
    def create_surface():

        current_forecast = JSON_DATA['current']['data'][0]
        daily_forecast = JSON_DATA['daily']['data']
        stats_data = JSON_DATA['stats']

        summary_string = current_forecast['weather']['description']
        temp_out_string = str(int(current_forecast['temp']))
        temp_out_unit = '°C' if METRIC else '°F'
        temp_out_string = str(temp_out_string + temp_out_unit)
        rain_string = str(int(JSON_DATA['daily']['data'][0]['pop'])) + ' %'

        today = daily_forecast[0]
        day_1 = daily_forecast[1]
        day_2 = daily_forecast[2]
        day_3 = daily_forecast[3]
        df_forecast = theme["DATE_FORMAT"]["FORECAST_DAY"]
        df_sun = theme["DATE_FORMAT"]["SUNRISE_SUNSET"]

        forecast_day_1_string = convert_timestamp(time.mktime(time.strptime(day_1['datetime'], '%Y-%m-%d')), df_forecast)
        forecast_day_2_string = convert_timestamp(time.mktime(time.strptime(day_2['datetime'], '%Y-%m-%d')), df_forecast)
        forecast_day_3_string = convert_timestamp(time.mktime(time.strptime(day_3['datetime'], '%Y-%m-%d')), df_forecast)

        forecast_day_1_min_max_string = f"{int(day_1['low_temp'])} | {int(day_1['high_temp'])}"
        forecast_day_2_min_max_string = f"{int(day_2['low_temp'])} | {int(day_2['high_temp'])}"
        forecast_day_3_min_max_string = f"{int(day_3['low_temp'])} | {int(day_3['high_temp'])}"

        wind_direction_string = current_forecast['wind_cdir']

        sunrise_string = convert_timestamp(today['sunrise_ts'], df_sun)
        sunset_string = convert_timestamp(today['sunset_ts'], df_sun)

        wind_speed = float(current_forecast['wind_spd'])
        wind_speed = wind_speed * 3.6 if METRIC else wind_speed
        wind_speed_unit = 'km/h' if METRIC else 'mph'
        wind_speed_string = str(f'{round(wind_speed, 1)} {wind_speed_unit}')

        global weather_surf, UPDATING

        new_surf = pygame.Surface((SURFACE_WIDTH, SURFACE_HEIGHT))
        new_surf.fill(BACKGROUND)

        DrawImage(new_surf, images['wifi'], 5, size=15, fillcolor=RED if CONNECTION_ERROR else GREEN).left()
        DrawImage(new_surf, images['refresh'], 5, size=15, fillcolor=RED if REFRESH_ERROR else GREEN).right(8)
        DrawImage(new_surf, images['path'], 5, size=15, fillcolor=RED if PATH_ERROR else GREEN).right(-5)

        DrawImage(new_surf, images[WEATHERICON], 68, size=100).center(2, 0, offset=10)
        DrawImage(new_surf, images[FORECASTICON_DAY_1], 200, size=50).center(3, 0)
        DrawImage(new_surf, images[FORECASTICON_DAY_2], 200, size=50).center(3, 1)
        DrawImage(new_surf, images[FORECASTICON_DAY_3], 200, size=50).center(3, 2)

        DrawImage(new_surf, images['sunrise'], 260, size=25).left()
        DrawImage(new_surf, images['sunset'], 290, size=25).left()

        draw_wind_layer(new_surf, current_forecast['wind_dir'], 285)

        draw_moon_layer(new_surf, 255, 60)

        # draw all the strings
        if config["DISPLAY"]["SHOW_API_STATS"]:
            DrawString(new_surf, str(stats_data['calls_remaining']), FONT_SMALL_BOLD, BLUE, 20).right(offset=-5)

        DrawString(new_surf, summary_string, FONT_SMALL_BOLD, VIOLET, 50).center(1, 0)

        DrawString(new_surf, temp_out_string, FONT_BIG, ORANGE, 75).right()

        DrawString(new_surf, rain_string, FONT_BIG, PRECIPCOLOR, 105).right()
        DrawString(new_surf, PRECIPTYPE, FONT_SMALL_BOLD, PRECIPCOLOR, 140).right()

        DrawString(new_surf, forecast_day_1_string, FONT_SMALL_BOLD, ORANGE, 165).center(3, 0)
        DrawString(new_surf, forecast_day_2_string, FONT_SMALL_BOLD, ORANGE, 165).center(3, 1)
        DrawString(new_surf, forecast_day_3_string, FONT_SMALL_BOLD, ORANGE, 165).center(3, 2)

        DrawString(new_surf, forecast_day_1_min_max_string, FONT_SMALL_BOLD, MAIN_FONT, 180).center(3, 0)
        DrawString(new_surf, forecast_day_2_min_max_string, FONT_SMALL_BOLD, MAIN_FONT, 180).center(3, 1)
        DrawString(new_surf, forecast_day_3_min_max_string, FONT_SMALL_BOLD, MAIN_FONT, 180).center(3, 2)

        DrawString(new_surf, sunrise_string, FONT_SMALL_BOLD, MAIN_FONT, 265).left(30)
        DrawString(new_surf, sunset_string, FONT_SMALL_BOLD, MAIN_FONT, 292).left(30)

        DrawString(new_surf, wind_direction_string, FONT_SMALL_BOLD, MAIN_FONT, 250).center(3, 2)
        DrawString(new_surf, wind_speed_string, FONT_SMALL_BOLD, MAIN_FONT, 300).center(3, 2)

        weather_surf = new_surf

        logger.info(f'summary: {summary_string}')
        logger.info(f'temp out: {temp_out_string}')
        logger.info(f'{PRECIPTYPE}: {rain_string}')
        logger.info(f'icon: {WEATHERICON}')
        logger.info(f'forecast: '
                    f'{forecast_day_1_string} {forecast_day_1_min_max_string} {FORECASTICON_DAY_1}; '
                    f'{forecast_day_2_string} {forecast_day_2_min_max_string} {FORECASTICON_DAY_2}; '
                    f'{forecast_day_3_string} {forecast_day_3_min_max_string} {FORECASTICON_DAY_3}')
        logger.info(f'sunrise: {sunrise_string} ; sunset {sunset_string}')
        logger.info(f'WindSpeed: {wind_speed_string}')

        # remove the ended timer and threads
        global THREADS
        THREADS = [t for t in THREADS if t.is_alive()]
        logging.info(f'threads cleaned: {len(THREADS)} left in the queue')

        pygame.time.delay(1500)
        UPDATING = pygame.time.get_ticks() + 1500  # 1.5 seconds

        return weather_surf

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


def draw_time_layer():
    timestamp = time.time()

    date_day_string = convert_timestamp(timestamp, theme["DATE_FORMAT"]["DATE"])
    date_time_string = convert_timestamp(timestamp, theme["DATE_FORMAT"]["TIME"])

    logger.debug(f'Day: {date_day_string}')
    logger.debug(f'Time: {date_time_string}')

    DrawString(time_surf, date_day_string, DATE_FONT, MAIN_FONT, 0).center(1, 0)
    DrawString(time_surf, date_time_string, CLOCK_FONT, MAIN_FONT, 15).center(1, 0)


def draw_moon_layer(surf, y, size):
    # based on @miyaichi's fork -> great idea :)
    _size = 300
    dt = datetime.datetime.fromtimestamp(JSON_DATA['daily']['data'][0]['ts'])
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

    surf.blit(image, (x, y))


def draw_wind_layer(surf, angle, y):
    # center the wind direction icon and circle on surface
    DrawImage(surf, images['circle'], y, size=30, fillcolor=WHITE).draw_middle_position_icon()
    DrawImage(surf, images['arrow'], y, size=30, fillcolor=RED, angle=-angle).draw_middle_position_icon()

    logger.debug(f'wind direction: {angle}')


def draw_statusbar():
    global CONNECTION, READING, UPDATING

    if CONNECTION:
        DrawImage(dynamic_surf, images['wifi'], 5, size=15, fillcolor=BLUE).left()
        if pygame.time.get_ticks() >= CONNECTION:
            CONNECTION = None

    if UPDATING:
        DrawImage(dynamic_surf, images['refresh'], 5, size=15, fillcolor=BLUE).right(8)
        if pygame.time.get_ticks() >= UPDATING:
            UPDATING = None

    if READING:
        DrawImage(dynamic_surf, images['path'], 5, size=15, fillcolor=BLUE).right(-5)
        if pygame.time.get_ticks() >= READING:
            READING = None


def draw_fps():
    DrawString(dynamic_surf, str(int(clock.get_fps())), FONT_SMALL_BOLD, RED, 20).left()


# ToDo: get touch input working with scaled displays
def draw_event(color=RED):

    pos = pygame.mouse.get_pos()

    size = 16
    radius = int(size / 2)

    tft_rect = tft_surf.get_rect()
    display_surface_rect = display_surf.get_rect()

    ratio_x = int((tft_rect.width / display_surface_rect.width))
    ratio_y = int((tft_rect.height / display_surface_rect.height))

    scaled_pos = (int(pos[0] / ratio_x) - int(FIT_SCREEN[0] / 2), int(pos[1] / ratio_y) - int(FIT_SCREEN[1] / 2))

    pygame.draw.circle(mouse_surf, color, scaled_pos, radius, 1)


def create_scaled_surf(surf, aa=False):
    if aa:
        scaled_surf = pygame.transform.smoothscale(surf, (int(SURFACE_WIDTH * SCALE), int(SURFACE_HEIGHT * SCALE)))
    else:
        scaled_surf = pygame.transform.scale(surf, (int(SURFACE_WIDTH * SCALE), int(SURFACE_HEIGHT * SCALE)))

    return scaled_surf


def quit_all():

    pygame.display.quit()
    pygame.quit()

    global THREADS

    for thread in THREADS:
        logger.info(f'Thread killed {thread}')
        thread.cancel()
        thread.join()

    sys.exit()


def loop():
    Update.run()

    running = True

    while running:
        tft_surf.fill(BACKGROUND)

        # fill the actual main surface and blit the image/weather layer
        display_surf.fill(BACKGROUND)
        display_surf.blit(weather_surf, (0, 0))

        # fill the dynamic layer, make it transparent and usw draw functions that write to that surface
        dynamic_surf.fill(BACKGROUND)
        dynamic_surf.set_colorkey(BACKGROUND)

        draw_statusbar()

        if config["DISPLAY"]["SHOW_FPS"]:
            draw_fps()

        my_particles.move(dynamic_surf, my_particles_list)

        # finally scale the dynamic surface and blit it to the main surface
        display_surf.blit(dynamic_surf, (0, 0))

        # now do the same for the time layer so it did not interfere with the other layers
        # fill the layer and make it transparent as well
        time_surf.fill(BACKGROUND)
        time_surf.set_colorkey(BACKGROUND)

        # draw the time to the layer
        draw_time_layer()
        display_surf.blit(time_surf, (0, 0))

        # draw the mouse events
        # mouse_surf.fill(BACKGROUND)
        # mouse_surf.set_colorkey(BACKGROUND)
        # draw_event(WHITE)

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
                    pygame.image.save(dynamic_surf, f'screenshot-{shot_time}.png')
                    logger.info(f'Screenshot created at {shot_time}')

        # display_surf.blit(mouse_surf, (0, 0))

        # finally scale the main surface and blit it to the tft surface
        # this is performance heavy so do it only once in a loop for the surface that collects all other
        tft_surf.blit(create_scaled_surf(display_surf.convert(32, 0), aa=AA), FIT_SCREEN)

        # update the display with all surfaces merged into the main one
        pygame.display.update()

        # do it as often as FPS configured (30 FPS recommend for particle simulation, 15 runs fine too, 60 is overkill)
        clock.tick(FPS)

    quit_all()


if __name__ == '__main__':

    try:

        my_particles = Particles()
        my_particles_list = my_particles.create_particle_list()
        images = image_factory(ICON_PATH)

        loop()

    except KeyboardInterrupt:

        quit_all()
