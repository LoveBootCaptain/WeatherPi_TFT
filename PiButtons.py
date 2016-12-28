#!/usr/bin/python
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


GPIO.add_event_detect(19, GPIO.FALLING, callback=restart_service, bouncetime=1000)
GPIO.add_event_detect(26, GPIO.FALLING, callback=shutdown_pi, bouncetime=1000)

if __name__ == '__main__':

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        os.system('sudo service WeatherPiTFT stop')
        GPIO.cleanup()
