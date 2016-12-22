#!/usr/bin/python3
# -*- coding: utf-8 -*-
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

# BLACK = (43, 43, 43)
BLACK = (10, 10, 10)
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

WindIcon_Path = ICON_PATH + 'wind-direction.png'

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
        :param offset: define some offset pixel to move strings a little bit (default=0)
        :return:
        """

        x = 10 + offset

        self.draw_string(x)

    def right(self, offset=0):
        """
        :param offset: define some offset pixel to move strings a little bit (default=0)
        :return:
        """

        x = (DISPLAY_WIDTH - self.size[0] - 10) - offset

        self.draw_string(x)

    def center(self, parts, part, offset=0):
        """
        :param parts: define in how many parts you want to split your display
        :param part: the part in which you want to render text (first part is 0, second is 1, etc.)
        :param offset: define some offset pixel to move strings a little bit (default=0)
        :return:
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
        :param offset: define some offset pixel to move strings a little bit (default=0)
        :return:
        """

        x = 10 + offset

        self.draw_image(x)

    def right(self, offset=0):
        """
        :param offset: define some offset pixel to move strings a little bit (default=0)
        :return:
        """

        x = (DISPLAY_WIDTH - self.size[0] - 10) - offset

        self.draw_image(x)

    def center(self, parts, part, offset=0):
        """
        :param parts: define in how many parts you want to split your display
        :param part: the part in which you want to render text (first part is 0, second is 1, etc.)
        :param offset: define some offset pixel to move strings a little bit (default=0)
        :return:
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

        thread = threading.Timer(60, Update.update_json)

        thread.start()

        threads.append(thread)

        # print(threads)

        DrawImage(SyncWiFi_Path, 5).left()
        pygame.display.update()

        try:

            config_data = open(PATH + 'config.json').read()

            config = json.loads(config_data)

            forecast_io_key = config['FORECAST_IO_KEY']

            options = '?lang=de&units=si&exclude=flags'

            request_url = 'https://api.forecast.io/forecast/' + forecast_io_key + '/52.5152463,13.5046708' + options

            # request_url = 'http://weatherpi/latest_weather.json'

            data = requests.get(request_url).json()

            with open(LOG_PATH + 'latest_weather.json', 'w') as outputfile:
                json.dump(data, outputfile, indent=2, sort_keys=True)

            print('\njson file saved')

            CONNECTION_ERROR = False

            # read_latest_json()

        except (requests.HTTPError, requests.ConnectionError):

            CONNECTION_ERROR = True

            print('Connection ERROR')

            pass

    @staticmethod
    def read_json():

        global threads, json_data, REFRESH_ERROR

        thread = threading.Timer(10, Update.read_json)

        thread.start()

        threads.append(thread)

        # print(threads)

        try:

            data = open(LOG_PATH + 'latest_weather.json').read()

            new_json_data = json.loads(data)

            print('\njson file read by module')

            json_data = new_json_data

            REFRESH_ERROR = False

            # update_icon_path()

        except IOError:

            REFRESH_ERROR = True

            print('ERROR - json file read by module')

        DrawImage(SyncPath_Path, 5).right()
        pygame.display.update()

    @staticmethod
    def icon_path():

        global threads, WeatherIcon_Path, ForeCastIcon_Day_1_Path, \
            ForeCastIcon_Day_2_Path, ForeCastIcon_Day_3_Path, MoonIcon_Path, PRECIPTYPE, PRECIPCOLOR

        thread = threading.Timer(30, Update.icon_path)

        thread.start()

        threads.append(thread)

        # print(threads)

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

        # print(icon, forecast, moon_icon)

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

        DrawImage(SyncRefresh_Path, 5).right(12)
        pygame.display.update()

        print('\nupdate path for icons: {}'.format(updated_list))

        Update.get_precip_type()

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

    @staticmethod
    def run():
        Update.update_json()
        Update.read_json()
        Update.icon_path()


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

    wind_icon = pygame.transform.rotate(pygame.image.load(WindIcon_Path), (360 - angle) + 180)  # (360 - angle) + 180

    position_x = (DISPLAY_WIDTH - ((DISPLAY_WIDTH / 3) / 2) - (wind_icon.get_rect()[2] / 2))

    position_y = y - (wind_icon.get_rect()[3] / 2)

    TFT.blit(wind_icon, (int(position_x), int(position_y)))

    print('\nwind direction: {}'.format(angle))


def draw_image_layer():
    if CONNECTION_ERROR:

        DrawImage(NoWiFi_Path, 5).left()

    else:

        DrawImage(WiFi_Path, 5).left()

    if REFRESH_ERROR:

        DrawImage(NoRefresh_Path, 5).right(12)

    else:

        DrawImage(Refresh_Path, 5).right(12)

    if PATH_ERROR:

        DrawImage(NoPath_Path, 5).right()

    else:

        DrawImage(Path_Path, 5).right()

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

    DrawString(date_day_string, font_small, WHITE, 5).center(1, 0)
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

    DrawString(summary_string, font_small, ORANGE, 55).center(1, 0)
    DrawString(temp_out_string, font_big_bold, ORANGE, 75).right()

    DrawString(rain_string, font_big_bold, PRECIPCOLOR, 105).right()
    DrawString(PRECIPTYPE, font_small_bold, PRECIPCOLOR, 140).right()

    DrawString(forecast_day_1_string, font_small_bold, ORANGE, 165).center(3, 0)
    DrawString(forecast_day_2_string, font_small_bold, ORANGE, 165).center(3, 1)
    DrawString(forecast_day_3_string, font_small_bold, ORANGE, 165).center(3, 2)

    DrawString(forecast_day_1_min_max_string, font_small, WHITE, 180).center(3, 0)
    DrawString(forecast_day_2_min_max_string, font_small, WHITE, 180).center(3, 1)
    DrawString(forecast_day_3_min_max_string, font_small, WHITE, 180).center(3, 2)

    DrawString(sunrise_string, font_small, WHITE, 265).left(30)
    DrawString(sunset_string, font_small, WHITE, 292).left(30)

    DrawString(north_string, font_small, WHITE, 250).center(3, 2)
    DrawString(wind_speed_string, font_small, WHITE, 300).center(3, 2)

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
