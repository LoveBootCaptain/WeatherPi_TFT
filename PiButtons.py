#!/usr/bin/python
# -*- coding: utf-8 -*-

import RPi.GPIO as GPIO
import os
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def shutdown_pi(shutdown):
    print('Button pressed:{} shutdown Pi'.format(shutdown))

    os.system('sudo service WeatherPiTFT stop')
    os.system('sudo shutdown now')


def restart_service(shutdown):
    print('Button pressed:{} restart service'.format(shutdown))

    os.system('sudo service WeatherPiTFT restart')


GPIO.add_event_detect(
    19, GPIO.FALLING, callback=restart_service, bouncetime=1000)
GPIO.add_event_detect(26, GPIO.FALLING, callback=shutdown_pi, bouncetime=1000)

if __name__ == '__main__':

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        os.system('sudo service WeatherPiTFT stop')
        GPIO.cleanup()
