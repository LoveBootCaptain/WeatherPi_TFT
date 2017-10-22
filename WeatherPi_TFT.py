#!/usr/bin/python3
# -*- coding: utf-8 -*-

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

import pygame
import requests

os.putenv('SDL_FBDEV', '/dev/fb1')

locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())

pygame.init()

pygame.mouse.set_visible(False)

DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 320

BLACK = (10, 10, 10)
DARK_GRAY = (43, 43, 43)
WHITE = (255, 255, 255)

RED = (231, 76, 60)
GREEN = (39, 174, 96)
BLUE = (52, 152, 219)

YELLOW = (241, 196, 15)
ORANGE = (238, 153, 18)

ICON_PATH = sys.path[0] + '/icons/'
FONT_PATH = sys.path[0] + '/fonts/'
LOG_PATH = sys.path[0] + '/logs/'
PATH = sys.path[0] + '/'

TFT = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
# TFT = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption('WeatherPi_TFT')

font_small = pygame.font.Font(FONT_PATH + 'Roboto-Medium.ttf', 14)
font_big = pygame.font.Font(FONT_PATH + 'Roboto-Medium.ttf', 30)

font_small_bold = pygame.font.Font(FONT_PATH + 'Roboto-Bold.ttf', 14)
font_big_bold = pygame.font.Font(FONT_PATH + 'Roboto-Bold.ttf', 30)

Refresh_Path = ICON_PATH + 'refresh.png'
NoRefresh_Path = ICON_PATH + 'no-refresh.png'
SyncRefresh_Path = ICON_PATH + 'sync-refresh.png'

WiFi_Path = ICON_PATH + 'wifi.png'
NoWiFi_Path = ICON_PATH + 'no-wifi.png'
SyncWiFi_Path = ICON_PATH + 'sync-wifi.png'

Path_Path = ICON_PATH + 'path.png'
NoPath_Path = ICON_PATH + 'no-path.png'
SyncPath_Path = ICON_PATH + 'sync-path.png'

WeatherIcon_Path = ICON_PATH + 'unknown.png'

ForeCastIcon_Day_1_Path = ICON_PATH + 'mini_unknown.png'
ForeCastIcon_Day_2_Path = ICON_PATH + 'mini_unknown.png'
ForeCastIcon_Day_3_Path = ICON_PATH + 'mini_unknown.png'

MoonIcon_Path = ICON_PATH + 'moon-0.png'

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
    def __init__(self, image_path, y):
        """
        :param image_path: the path to the image you want to render
        :param y: the y-postion of the image you want to render
        """

        self.image_path = image_path
        self.image = pygame.image.load(self.image_path)
        self.y = y
        self.size = self.image.get_rect().size

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

        x = (DISPLAY_WIDTH - self.size[0] - 10) - offset

        self.draw_image(x)

    def center(self, parts, part, offset=0):
        """
        :param parts: define in how many parts you want to split your display
        :param part: the part in which you want to render text (first part is 0, second is 1, etc.)
        :param offset: define some offset pixel to move strings a little bit (default=0)
        """

        x = int(((((DISPLAY_WIDTH / parts) / 2) + ((DISPLAY_WIDTH / parts) * part)) - (self.size[0] / 2)) + offset)

        self.draw_image(x)

    def draw_image(self, x):
        """
        takes x from the functions above and the y from the class to render the image
        """

        TFT.blit(self.image, (x, self.y))



class Update:
    @staticmethod
    def update_json():

        global threads, CONNECTION_ERROR

        thread = threading.Timer(300, Update.update_json)

        thread.start()

        threads.append(thread)

        try:

            config_data = open(PATH + 'config.json').read()

            config = json.loads(config_data)

            forecast_io_key = config['FORECAST_IO_KEY']
            forecast_lang = config['FORECAST_LANGUAGE']
            forecast_units = config['FORECAST_UNITS']
            forecast_lat = config['FORECAST_LAT']
            forecast_lon = config['FORECAST_LON']
            forecast_excludes = config['FORECAST_EXCLUDES']

            api_endpoint = 'https://api.forecast.io/forecast/'

            options = '?lang={}&units={}&exclude={}'.format(forecast_lang, forecast_units, forecast_excludes)

            request_url = str(api_endpoint + forecast_io_key + '/{},{}'.format(forecast_lat, forecast_lon) + options)

            # request_url = 'http://weatherpi/latest_weather.json'

            data = requests.get(request_url).json()

            with open(LOG_PATH + 'latest_weather.json', 'w') as outputfile:
                json.dump(data, outputfile, indent=2, sort_keys=True)

            print('\njson file saved')

            CONNECTION_ERROR = False

        except (requests.HTTPError, requests.ConnectionError):

            CONNECTION_ERROR = True

            print('Connection ERROR')

            pass

        DrawImage(SyncWiFi_Path, 5).left()
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

        DrawImage(SyncPath_Path, 5).right(-5)
        pygame.display.update()

        time.sleep(1)

        Update.icon_path()

    @staticmethod
    def icon_path():

        global WeatherIcon_Path, ForeCastIcon_Day_1_Path, \
            ForeCastIcon_Day_2_Path, ForeCastIcon_Day_3_Path, MoonIcon_Path, PRECIPTYPE, PRECIPCOLOR

        folder_path = ICON_PATH
        icon_extension = '.png'
        mini = 'mini_'

        updated_list = []

        # known conditions:
        # clear-day, clear-night, partly-cloudy-day, partly-cloudy-night, wind, cloudy, rain, snow, fog

        icon = json_data['currently']['icon']

        forecast_icon_1 = json_data['daily']['data'][1]['icon']
        forecast_icon_2 = json_data['daily']['data'][2]['icon']
        forecast_icon_3 = json_data['daily']['data'][3]['icon']

        forecast = (str(forecast_icon_1), str(forecast_icon_2), str(forecast_icon_3))

        moon_icon = json_data['daily']['data'][0]['moonPhase']

        moon_icon = int((float(moon_icon) * 100 / 3.57) + 0.25)

        moon = 'moon-' + str(moon_icon)

        print(icon, forecast, moon_icon)

        WeatherIcon_Path = folder_path + icon + icon_extension

        ForeCastIcon_Day_1_Path = folder_path + mini + forecast[0] + icon_extension
        ForeCastIcon_Day_2_Path = folder_path + mini + forecast[1] + icon_extension
        ForeCastIcon_Day_3_Path = folder_path + mini + forecast[2] + icon_extension

        MoonIcon_Path = folder_path + moon + icon_extension

        path_list = [WeatherIcon_Path, ForeCastIcon_Day_1_Path,
                     ForeCastIcon_Day_2_Path, ForeCastIcon_Day_3_Path, MoonIcon_Path]

        print('\nvalidating path: {}\n'.format(path_list))

        for path in path_list:

            if os.path.isfile(path):

                print('TRUE :', path)

                updated_list.append(path)

            else:

                print('FALSE :', path)

                if 'mini' in path:

                    updated_list.append(ICON_PATH + 'mini_unknown.png')

                elif 'moon' in path:

                    updated_list.append(ICON_PATH + 'moon-unknown.png')

                else:

                    updated_list.append(ICON_PATH + 'unknown.png')

        WeatherIcon_Path = updated_list[0]
        ForeCastIcon_Day_1_Path = updated_list[1]
        ForeCastIcon_Day_2_Path = updated_list[2]
        ForeCastIcon_Day_3_Path = updated_list[3]
        MoonIcon_Path = updated_list[4]

        global PATH_ERROR

        if any("unknown" in s for s in updated_list):

            PATH_ERROR = True

        else:

            PATH_ERROR = False

        print('\nupdate path for icons: {}'.format(updated_list))

        Update.get_precip_type()

        DrawImage(SyncRefresh_Path, 5).right(7)
        pygame.display.update()

    @staticmethod
    def get_precip_type():

        global json_data, PRECIPCOLOR, PRECIPTYPE

        if int(json_data['currently']['precipProbability'] * 100) == 0:

            PRECIPTYPE = 'Niederschlag'
            PRECIPCOLOR = ORANGE

        else:

            precip_type = json_data['currently']['precipType']

            if precip_type == 'rain':

                PRECIPTYPE = 'Regen'
                PRECIPCOLOR = BLUE

            elif precip_type == 'snow':

                PRECIPTYPE = 'Schnee'
                PRECIPCOLOR = WHITE

            else:

                PRECIPTYPE = str(precip_type)
                PRECIPCOLOR = RED

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

    timestring = str(datetime.datetime.fromtimestamp(int(timestamp)).strftime(param_string))

    return timestring


def draw_wind_layer(y):

    angle = json_data['currently']['windBearing']

    circle_icon = pygame.image.load(ICON_PATH + 'circle.png')

    arrow_icon = pygame.transform.rotate(pygame.image.load(ICON_PATH + 'arrow.png'),
                                         (360 - angle) + 180)  # (360 - angle) + 180

    def draw_middle_position_icon(icon):

        position_x = (DISPLAY_WIDTH - ((DISPLAY_WIDTH / 3) / 2) - (icon.get_rect()[2] / 2))

        position_y = (y - (icon.get_rect()[3] / 2))

        position = (position_x, position_y)

        TFT.blit(icon, position)

    draw_middle_position_icon(arrow_icon)
    draw_middle_position_icon(circle_icon)

    print('\nwind direction: {}'.format(angle))


def draw_image_layer():
    if CONNECTION_ERROR:

        DrawImage(NoWiFi_Path, 5).left()

    else:

        DrawImage(WiFi_Path, 5).left()

    if REFRESH_ERROR:

        DrawImage(NoRefresh_Path, 5).right(7)

    else:

        DrawImage(Refresh_Path, 5).right(7)

    if PATH_ERROR:

        DrawImage(NoPath_Path, 5).right(-5)

    else:

        DrawImage(Path_Path, 5).right(-5)

    DrawImage(WeatherIcon_Path, 65).center(2, 0)

    if PRECIPTYPE == 'Regen':

        DrawImage(PrecipRain_Path, 140).right(45)

    elif PRECIPTYPE == 'Schnee':

        DrawImage(PrecipSnow_Path, 140).right(50)

    DrawImage(ForeCastIcon_Day_1_Path, 200).center(3, 0)
    DrawImage(ForeCastIcon_Day_2_Path, 200).center(3, 1)
    DrawImage(ForeCastIcon_Day_3_Path, 200).center(3, 2)

    DrawImage(SunRise_Path, 260).left()
    DrawImage(SunSet_Path, 290).left()

    DrawImage(MoonIcon_Path, 255).center(1, 0)

    draw_wind_layer(285)

    print('\n' + WeatherIcon_Path)
    print(ForeCastIcon_Day_1_Path)
    print(ForeCastIcon_Day_2_Path)
    print(ForeCastIcon_Day_3_Path)
    print(MoonIcon_Path)


def draw_time_layer():
    timestamp = time.time()

    date_time_string = convert_timestamp(timestamp, '%H:%M:%S')
    date_day_string = convert_timestamp(timestamp, '%A - %d. %b %Y')

    print('\nDay: {}'.format(date_day_string))
    print('Time: {}'.format(date_time_string))

    DrawString(date_day_string, font_small_bold, WHITE, 5).center(1, 0)
    DrawString(date_time_string, font_big_bold, WHITE, 20).center(1, 0)


def draw_text_layer():
    forecast = json_data['daily']['data']

    summary_string = json_data['currently']['summary']
    temp_out_string = str(json_data['currently']['temperature']) + '°C'
    rain_string = str(int(json_data['currently']['precipProbability'] * 100)) + ' %'

    forecast_day_1_string = convert_timestamp(forecast[1]['time'], '%a').upper()
    forecast_day_2_string = convert_timestamp(forecast[2]['time'], '%a').upper()
    forecast_day_3_string = convert_timestamp(forecast[3]['time'], '%a').upper()

    forecast_day_1_min_max_string = str(int(forecast[1]['temperatureMin'])) + ' | ' + str(
        int(forecast[0]['temperatureMax']))

    forecast_day_2_min_max_string = str(int(forecast[2]['temperatureMin'])) + ' | ' + str(
        int(forecast[1]['temperatureMax']))

    forecast_day_3_min_max_string = str(int(forecast[3]['temperatureMin'])) + ' | ' + str(
        int(forecast[2]['temperatureMax']))

    north_string = 'N'

    sunrise_string = convert_timestamp(int(json_data['daily']['data'][0]['sunriseTime']), '%H:%M')
    sunset_string = convert_timestamp(int(json_data['daily']['data'][0]['sunsetTime']), '%H:%M')

    wind_speed_string = str(round((float(json_data['currently']['windSpeed']) * 1.609344), 1)) + ' km/h'

    draw_time_layer()

    DrawString(summary_string, font_small_bold, ORANGE, 55).center(1, 0)

    DrawString(temp_out_string, font_big, ORANGE, 75).right()

    DrawString(rain_string, font_big, PRECIPCOLOR, 105).right()
    DrawString(PRECIPTYPE, font_small_bold, PRECIPCOLOR, 140).right()

    DrawString(forecast_day_1_string, font_small_bold, ORANGE, 165).center(3, 0)
    DrawString(forecast_day_2_string, font_small_bold, ORANGE, 165).center(3, 1)
    DrawString(forecast_day_3_string, font_small_bold, ORANGE, 165).center(3, 2)

    DrawString(forecast_day_1_min_max_string, font_small_bold, WHITE, 180).center(3, 0)
    DrawString(forecast_day_2_min_max_string, font_small_bold, WHITE, 180).center(3, 1)
    DrawString(forecast_day_3_min_max_string, font_small_bold, WHITE, 180).center(3, 2)

    DrawString(sunrise_string, font_small_bold, WHITE, 265).left(30)
    DrawString(sunset_string, font_small_bold, WHITE, 292).left(30)

    DrawString(north_string, font_small_bold, WHITE, 250).center(3, 2)
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

                    print('SPACE')

    quit_all()


if __name__ == '__main__':

    try:

        loop()

    except KeyboardInterrupt:

        quit_all()
