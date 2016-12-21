# WeatherPi_TFT

a weather display for a raspberry pi and a adafruit (featherwing) TFT ili9341 display written in python3

## Hardware and wiring

i wrote this app on a mac and tested it quite a while. since it uses only standard python3 modules and libraries 
it should work on nearly everything that can run python3 and pygame.

this tutorial is basically for running it on a raspberry pi (zero, 1, 2, 3) and a TFT display which matches up 
with chips like the ones from adafruit. as long as it uses standard spi it should work with the new `dtoverlay`module
in the latest jessie versions of raspbian... i think there is no need for a custom kernel. it's just a little bit 
configuration.

i tested it with following TFT's:

* [TFT FeatherWing - 2.4" 320x240 Touchscreen For All Feathers](https://www.adafruit.com/products/3315)
* [Adafruit 2.4" TFT LCD with Touchscreen Breakout w/MicroSD Socket - ILI9341](https://www.adafruit.com/product/2478)
* adafruit TFT's with ili9341 driver

no configuration needed for:

> skip all the TFT setup parts

* official raspberry pi 7" display
* any HDMI display

### wiring

this should explain how to wire up your display

```
SDO (MISO) TFT Data Out SPI_MISO    = GPIO09
SDI (MOSI) TFT Data In  SPI_MOSI    = GPIO10
SCK TFT Clock           SPI_CLK     = GPIO11

CS TFT Chip Select      SPI_CE0_N   = GPIO08
D/C TFT Data / Command              = GPIO24

RESET Reset                         = GPIO23
 
GND Ground                          = GND
VCC 3V3 supply                      = +3V3 or 5V
```

## Install

### install jessie to a sd card and update

get the latest [NOOBS](https://www.raspberrypi.org/downloads/noobs/) installer from:
```
https://www.raspberrypi.org/downloads/noobs/
```
> i used NOOBS v2.1.0 which was the latest version for now

### setup the SD card
```
TODO: write a tutorial for setting up the SD card
```

### the first boot
```
TODO: write a tutorial for first boot
```

### enable SPI
```
TODO: write a tutorial for setting up SPI
```

### connect to your WiFi
```
TODO: write a tutorial for connecting to WiFi via terminal
```

### update all tools

when your connected to your wifi open a terminal and type:
```bash
sudo apt-get update  -y && sudo apt-get upgrade -y 
```

### install WeatherPi_TFT

```bash
git clone https://github.com/LoveBootCaptain/WeatherPi_TFT.git
```

### install the dependencies

```
TODO: write a requirements.txt
```

### set up the TFT

in /boot/config.txt, add in the following at the bottom 
```
# TFT display and touch panel
dtoverlay=rpi-display
dtparam=rotate=0
dtparam=speed=10000000
dtparam=xohms=100
dtparam=debug=4
```

change /boot/cmdline.txt to add the following to the end of the existing line
```
fbcon=map:10 fbcon=font:VGA8x8 logo.nologo
```

### setup the service

```bash
cd
cd WeatherPi_TFT
sudo cp Service.sh /etc/init.d/WeatherPiTFT
sudo chmod +x /etc/init.d/WeatherPiTFT
sudo chmod +x Weatherpi_TFT.py
```

### run python with root privileges


```bash
sudo chown -v root:root /usr/bin/python3
sudo chmod -v u+s /usr/bin/python3
```

### setting up python3 as default interpreter
```bash
update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
update-alternatives --install /usr/bin/python python /usr/bin/python3.4 2
```

> you can always swap back to python2 with:
> ```
> update-alternatives --config python
> ```
> and choose your prefered version of python

check if python3.x is now default with:
```bash
python --version
```

it should say something like: 
```
Python 3.4.x
```

### update all python modules

open up a python console
```bash
python
```

than run this line by line
```python
import pip
from subprocess import call
for dist in pip.get_installed_distributions():
    call("pip install --upgrade " + dist.project_name, shell=True)
```

if everything is set up and updated correctly:
```bash
sudo reboot
```

### test the service

```bash
sudo service WeatherPiTFT start
sudo service WeatherPiTFT stop
sudo service WeatherPiTFT restart
sudo service WeatherPiTFT status
```

if this is doing what it should you can run the service every time you boot your pi
```bash
sudo update-rc.d WeatherPi_TFT defaults
```

### screenshots

#### darcula styled theme

![Darcula styled Theme for WeatherPi_TFT](https://dl.dropboxusercontent.com/u/6076227/github/darcula_theme.png)

![WeatherPi_TFT](https://dl.dropboxusercontent.com/u/6076227/github/darcula_feather_weather_pi.png)
