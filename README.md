# WeatherPi_TFT

a weather display for a raspberry pi and a adafruit (featherwing) TFT ili9341 display written in python3

## Hardware and wiring

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

### install WeatherPi_TFT

```
git clone https://github.com/LoveBootCaptain/WeatherPi_TFT.git
```

### install the dependencies

TODO: write a requirements.txt

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

```
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
```
update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
update-alternatives --install /usr/bin/python python /usr/bin/python3.4 2
```

> you can always swap back to python2 with:
> ```
> update-alternatives --config python
> ```
> and choose your prefered version of python

check if python3.x is now default with:
```
python --version
```

it should say something like: 
```
Python 3.4.x
```

### update all python modules

open up a python console
```
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
```
sudo reboot
```

### test the service

```
sudo service WeatherPiTFT start
sudo service WeatherPiTFT stop
sudo service WeatherPiTFT restart
sudo service WeatherPiTFT status
```

if this is doing what it should you can run the service every time you boot your pi
```
sudo update-rc.d WeatherPi_TFT defaults
```

### screenshots

#### darcula styled theme

![Darcula styled Theme for WeatherPi_TFT](https://dl.dropboxusercontent.com/u/6076227/github/darcula_theme.png)

![WeatherPi_TFT](https://dl.dropboxusercontent.com/u/6076227/github/darcula_feather_weather_pi.png)
