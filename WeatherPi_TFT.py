#!/usr/bin/python
# -*- coding: utf-8 -*-
import pygame
import os
import locale
import time
import requests
import threading
import json
import datetime

os.putenv('SDL_FBDEV', '/dev/spidev')

locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')

pygame.init()

pygame.mouse.set_visible(False)

DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 320

BLACK = (43, 43, 43)
WHITE = (255, 255, 255)

RED = (231, 76, 60)
GREEN = (39, 174, 96)
BLUE = (52, 152, 219)

YELLOW = (241, 196, 15)
ORANGE = (255, 147, 0)

TFT = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption('FeatherWeather')

font_small = pygame.font.Font('font/Roboto-Medium.ttf', 14)
font_big = pygame.font.Font('font/Roboto-Medium.ttf', 30)

font_small_bold = pygame.font.Font('font/Roboto-Bold.ttf', 14)
font_big_bold = pygame.font.Font('font/Roboto-Bold.ttf', 30)

Refresh_Path = 'icons/refresh.png'
NoRefresh_Path = 'icons/no-refresh.png'
SyncRefresh_Path = 'icons/sync-refresh.png'

WiFi_Path = 'icons/wifi.png'
NoWiFi_Path = 'icons/no-wifi.png'
SyncWiFi_Path = 'icons/sync-wifi.png'

WeatherIcon_Path = 'icons/unknown.png'

ForeCastIcon_Day_1_Path = 'icons/mini_unknown.png'
ForeCastIcon_Day_2_Path = 'icons/mini_unknown.png'
ForeCastIcon_Day_3_Path = 'icons/mini_unknown.png'

MoonIcon_Path = 'icons/moon-0.png'

SunRise_Path = 'icons/sunrise.png'
SunSet_Path = 'icons/sunset.png'

WindIcon_Path = 'icons/wind-direction.png'

PrecipSnow_Path = 'icons/precipsnow.png'
PrecipRain_Path = 'icons/preciprain.png'

CONNECTION_ERROR = True
REFRESH_ERROR = True
PRECIPTYPE = 'NULL'

threads = []

json_data = {}


def string_align_center(string, font):

    size = font.size(string)

    # print('Size of the string "{}": {}'.format(string, size))

    center = (DISPLAY_WIDTH / 2) - (size[0] / 2)

    # print('Position of the string to align it center: {}'.format(center))

    return center


def string_align_right(string, font):

    size = font.size(string)

    # print('Size of the string "{}": {}'.format(string, size))

    right = DISPLAY_WIDTH - size[0] - 10

    # print('Position of the string to align it right: {}'.format(right))

    return right


def string_align_left(string, font):

    size = font.size(string)

    # print('Size of the string "{}": {}'.format(string, size))

    left = (DISPLAY_WIDTH - size[0]) - (DISPLAY_WIDTH - size[0] - 10)

    # print('Position of the string to align it left: {}'.format(left))

    return left


def string_align_left_center(string, font):

    size = font.size(string)

    # print('Size of the string "{}": {}'.format(string, size))

    left_center = ((DISPLAY_WIDTH / 3) / 2) - (size[0] / 2)

    # print('Position of the string to align it left_center: {}'.format(left_center))

    return left_center


def string_align_right_center(string, font):

    size = font.size(string)

    # print('Size of the string "{}": {}'.format(string, size))

    right_center = (DISPLAY_WIDTH - ((DISPLAY_WIDTH / 3) / 2) - (size[0] / 2))

    # print('Position of the string to align it right_center: {}'.format(right_center))

    return right_center


def get_image_size(image_path):

    image = pygame.image.load(image_path)

    size = image.get_rect().size

    # print('Size of the image "{}": {}'.format(image_path, size))

    return size


def image_align_center(image_path, parts):

    image_size = get_image_size(image_path)

    # print('Size of the image "{}": {}'.format(image_path, image_size))

    center = (DISPLAY_WIDTH / parts) - (image_size[0] / 2)

    # print('Position of the image to align it center: {}'.format(center))

    return center


def image_align_right(image_path, parts):

    image_size = get_image_size(image_path)

    right = (DISPLAY_WIDTH / parts) - image_size[0] - 10

    # print('Position of the image to align it right: {}'.format(right))

    return right


def image_align_left(image_path, parts):

    image_size = get_image_size(image_path)

    left = ((DISPLAY_WIDTH / parts) - image_size[0]) - (DISPLAY_WIDTH - image_size[0] - 10)

    # print('Position of the image to align it left: {}'.format(left))

    return left


def image_align_left_center(image_path, parts):

    image_size = get_image_size(image_path)

    left_center = ((DISPLAY_WIDTH / parts) / 2) - (image_size[0] / 2)

    # print('Position of the image to align it left_center: {}'.format(left_center))

    return left_center


def image_align_right_center(image_path, parts):

    image_size = get_image_size(image_path)

    right_center = (DISPLAY_WIDTH - ((DISPLAY_WIDTH / parts) / 2) - (image_size[0] / 2))

    # print('Position of the image to align it right_center: {}'.format(right_center))

    return right_center


def update_latest_json():

    global threads, CONNECTION_ERROR

    thread_1 = threading.Timer(60, update_latest_json)

    thread_1.start()

    threads.append(thread_1)

    # print(threads)

    draw_img(SyncWiFi_Path, image_align_left, 5, 1)

    pygame.display.update()

    try:

        data = requests.get('http://locutus.dscloud.me:7575/latest_weather.json').json()

        with open('logs/latest_weather.json', 'w') as outputfile:
            json.dump(data, outputfile, indent=2, sort_keys=True)

        print('\njson file saved')

        CONNECTION_ERROR = False

        # read_latest_json()

    except (requests.HTTPError, requests.ConnectionError):

        CONNECTION_ERROR = True

        pass


def read_latest_json():

    global threads, json_data, REFRESH_ERROR

    thread_2 = threading.Timer(10, read_latest_json)

    thread_2.start()

    threads.append(thread_2)

    # print(threads)

    draw_img(SyncRefresh_Path, image_align_right, 5, 1)

    pygame.display.update()

    try:

        data = open('logs/latest_weather.json').read()

        new_json_data = json.loads(data)

        print('\njson file read by module')

        json_data = new_json_data

        REFRESH_ERROR = False

        # update_icon_path()

    except IOError:

        REFRESH_ERROR = True

        print('ERROR - json file read by module')


def get_icon():

    # known conditions: clear-day, clear-night, partly-cloudy-day, partly-cloudy-night, wind, cloudy, rain, snow, fog

    icon = json_data['currently']['icon']

    # print(icon)

    return icon


def get_forecast_icon():

    # known conditions: clear-day, clear-night, partly-cloudy-day, partly-cloudy-night, wind, cloudy, rain, snow, fog

    forecast_icon_1 = json_data['daily']['data'][1]['icon']
    forecast_icon_2 = json_data['daily']['data'][2]['icon']
    forecast_icon_3 = json_data['daily']['data'][3]['icon']

    forecast_list = (str(forecast_icon_1), str(forecast_icon_2), str(forecast_icon_3))

    # print(forecast_list)

    return forecast_list


def get_moon_icon():

    moon_icon = json_data['daily']['data'][0]['moonPhase']

    moon_icon = int((float(moon_icon) * 100 / 3.57) + 0.25)

    moon_icon = 'moon-' + str(moon_icon)

    # print(moon_icon)

    return moon_icon


def update_icon_path():

    global threads, WeatherIcon_Path, ForeCastIcon_Day_1_Path, \
        ForeCastIcon_Day_2_Path, ForeCastIcon_Day_3_Path, MoonIcon_Path

    thread_3 = threading.Timer(30, update_icon_path)

    thread_3.start()

    threads.append(thread_3)

    # print(threads)

    folder_path = 'icons/'
    icon_extension = '.png'
    mini = 'mini_'

    updated_list = []

    icon = get_icon()

    forecast = get_forecast_icon()

    moon = get_moon_icon()

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

                updated_list.append('icons/mini_unknown.png')

            elif 'moon' in path:

                updated_list.append('icons/moon-0.png')

            else:

                updated_list.append('icons/unknown.png')

    WeatherIcon_Path = updated_list[0]
    ForeCastIcon_Day_1_Path = updated_list[1]
    ForeCastIcon_Day_2_Path = updated_list[2]
    ForeCastIcon_Day_3_Path = updated_list[3]
    MoonIcon_Path = updated_list[4]

    print('\nupdate path for icons: {}'.format(updated_list))


def draw_string(string, font, color, align, y):

    TFT.blit(font.render(string, True, color), (align(string, font), y))


def convert_timestamp(timestamp, param_string):

    return datetime.datetime.fromtimestamp(int(timestamp)).strftime(param_string)


def draw_img(image_path, align, y, parts):

    TFT.blit(pygame.image.load(image_path), (align(image_path, parts), y))


def draw_wind_layer(y):

    angle = json_data['currently']['windBearing']

    wind_icon = pygame.transform.rotate(pygame.image.load(WindIcon_Path), (360 - angle) + 180)

    position_x = (DISPLAY_WIDTH - ((DISPLAY_WIDTH / 3) / 2) - (wind_icon.get_rect()[2] / 2))

    position_y = y - (wind_icon.get_rect()[3] / 2)

    TFT.blit(wind_icon, (int(position_x), position_y))

    print('\nwind direction: {}'.format(angle))


def draw_time_layer():

    timestamp = time.time()

    date_time_string = convert_timestamp(timestamp, '%H:%M')
    date_day_string = convert_timestamp(timestamp, '%A - %d. %b %Y')

    print('\nTime: {}'.format(date_time_string))
    print('Day: {}'.format(date_day_string))

    draw_string(date_day_string, font_small, WHITE, string_align_center, 5)
    draw_string(date_time_string, font_big_bold, WHITE, string_align_center, 20)


def draw_image_layer():

    if CONNECTION_ERROR:

        draw_img(NoWiFi_Path, image_align_left, 5, 1)

    else:

        draw_img(WiFi_Path, image_align_left, 5, 1)

    if REFRESH_ERROR:

        draw_img(NoRefresh_Path, image_align_right, 5, 1)

    else:

        draw_img(Refresh_Path, image_align_right, 5, 1)

    if PRECIPTYPE == 'rain':

        draw_img(PrecipRain_Path, image_align_right, 140, 1)

    elif PRECIPTYPE == 'snow':

        draw_img(PrecipSnow_Path, image_align_right, 140, 1)

    else:

        pass

    draw_img(WeatherIcon_Path, image_align_left_center, 65, 2)

    draw_img(ForeCastIcon_Day_1_Path, image_align_left_center, 200, 3)
    draw_img(ForeCastIcon_Day_2_Path, image_align_center, 200, 2)
    draw_img(ForeCastIcon_Day_3_Path, image_align_right_center, 200, 3)

    draw_img(SunRise_Path, image_align_left, 260, 1)
    draw_img(SunSet_Path, image_align_left, 290, 1)

    draw_img(MoonIcon_Path, image_align_center, 255, 2)

    draw_wind_layer(285)

    # draw_img(WiFi_Path, image_align_left_center, 30, 3)
    # draw_img(Refresh_Path, image_align_right_center, 30, 3)

    print('\n')
    print(WeatherIcon_Path)
    print(ForeCastIcon_Day_1_Path)
    print(ForeCastIcon_Day_2_Path)
    print(ForeCastIcon_Day_3_Path)
    print(MoonIcon_Path)


def draw_text_layer():

    draw_time_layer()

    global PRECIPTYPE

    forecast = json_data['daily']['data']

    summary_string = json_data['currently']['summary']
    temp_out_string = str(json_data['currently']['sensor_temp_outside']) + '°C'
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

    if int(json_data['currently']['precipProbability'] * 100) == 0:

        precip_string = 'Niederschlag'

        PRECIPTYPE = 'NULL'

    else:

        precip_type = json_data['currently']['precipType']

        if precip_type == 'rain':

            precip_string = 'Regen' + '         '

            PRECIPTYPE = precip_type

        elif precip_type == 'snow':

            precip_string = 'Schnee' + '         '

            PRECIPTYPE = precip_type

        else:

            precip_string = str(precip_type)

            PRECIPTYPE = precip_type

    north_string = 'N'

    sunrise_string = convert_timestamp(int(json_data['daily']['data'][0]['sunriseTime']), '%H:%M')
    sunset_string = convert_timestamp(int(json_data['daily']['data'][0]['sunsetTime']), '%H:%M')

    wind_speed_string = str(round((float(json_data['currently']['windSpeed']) * 1.609344), 1)) + ' km/h'

    draw_string(summary_string, font_small, ORANGE, string_align_center, 55)
    draw_string(temp_out_string, font_big_bold, ORANGE, string_align_right, 75)

    draw_string(rain_string, font_big_bold, ORANGE, string_align_right, 105)

    if PRECIPTYPE == 'rain':

        draw_string(precip_string, font_small_bold, BLUE, string_align_right, 140)

    elif PRECIPTYPE == 'snow':

        draw_string(precip_string, font_small_bold, WHITE, string_align_right, 140)

    else:

        draw_string(precip_string, font_small_bold, ORANGE, string_align_right, 140)

    draw_string(forecast_day_1_string, font_small_bold, ORANGE, string_align_left_center, 165)
    draw_string(forecast_day_2_string, font_small_bold, ORANGE, string_align_center, 165)
    draw_string(forecast_day_3_string, font_small_bold, ORANGE, string_align_right_center, 165)

    draw_string(forecast_day_1_min_max_string, font_small, WHITE, string_align_left_center, 180)
    draw_string(forecast_day_2_min_max_string, font_small, WHITE, string_align_center, 180)
    draw_string(forecast_day_3_min_max_string, font_small, WHITE, string_align_right_center, 180)

    TFT.blit(font_small.render(sunrise_string, True, WHITE),
             (string_align_left_center(sunrise_string, font_small) + 20, 265))

    TFT.blit(font_small.render(sunset_string, True, WHITE),
             (string_align_left_center(sunset_string, font_small) + 20, 292))

    draw_string(north_string, font_small, WHITE, string_align_right_center, 250)
    draw_string(wind_speed_string, font_small, WHITE, string_align_right_center, 300)

    print('\n')
    print('summary: {}'.format(summary_string))
    print('temp out: {}'.format(temp_out_string))
    print('{}: {}'.format(precip_string, rain_string))
    print('forecast: '
          + forecast_day_1_string + ' ' + forecast_day_1_min_max_string + ' ; '
          + forecast_day_2_string + ' ' + forecast_day_2_min_max_string + ' ; '
          + forecast_day_3_string + ' ' + forecast_day_3_min_max_string
          )
    print('sunrise: {} ; sunset {}'.format(sunrise_string, sunset_string))
    print('WindSpeed: {}'.format(wind_speed_string))


def update_data():

    update_latest_json()
    read_latest_json()
    update_icon_path()


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

    update_data()

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

    quit_all()


if __name__ == '__main__':

    try:

        loop()

    except KeyboardInterrupt:

        quit_all()
