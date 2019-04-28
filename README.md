# WeatherPi

Weather Station for Raspberry Pi and Small LCDs  
(Raspberry Piと小型液晶向けのウェザーステーション)


<img width="480" alt="480x320 en" src="https://user-images.githubusercontent.com/129797/56856836-95c55e80-699e-11e9-8d4d-7422eef36732.png">

fig: 480x320 en

<img width="240" alt="240x320 en" src="https://user-images.githubusercontent.com/129797/56856807-9f9a9200-699d-11e9-8730-7571c7249ea7.png">

fig: 240x320 en

## Feature
* Modularized display parts  
  (表示パーツはモジュール化してあるので、カスタマイズが可能です)
* Heat Index color / UV Index color support  
  (Heat Index/UV Indexで表示色を変更します)
* Custom module support（ex. DHT11 temperature/humidity sensor module)  
  (カスタムモジュールを作成して組み込むことができます)
* i18n (internationalization) support  
  (ロケールの変更や表示文字列の翻訳が可能です)

## Installation

### install and update tools
```bash
sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install rng-tools gettext -y
```

### install WeatherPi
```bash
git clone https://github.com/miyaichi/WeatherPi.git
cd WeatherPi
```

### copy config file and customize it
```bash
cp example.240x320.config.json config.json
```
or
```bash
cp example.480x320.config.json config.json
```

#### config.json
| Name                    |          | Default           | Description                                                                                                        |
| ----------------------- | -------- | ----------------- | ------------------------------------------------------------------------------------------------------------------ |
| darksky_api_key         | required |                   | **[DarkSky API Key](https://darksky.net/dev)**                                                                     |
| google_api_key          | optional |                   | [Google Geocoding API darksky_api_key](https://developers.google.com/maps/documentation/geocoding/start)           |
| address                 | optional |                   | The address of a location. <br> latitude and longitude can be omitted if google_api_key and address are specified. |
| latitude <br> longitude | required |                   | The latitude and longitude of a location (in decimal degrees). Positive is east, negative is west.                 |
| locale                  | required | en_US.UTF-8       | Locale. Specify the display language of time and weather information.                                              |
| units                   | required | si                | Unit of weather　information.                                                                                      |
| SDL_FBDEV               | required | /dev/fb1          | Frame buffer device to use in the linux fbcon driver, instead of /dev/fb0.                                         |
| display                 | required |                   | Display size. [Width, Height]                                                                                      |
| fonts.regular           | required | Roboto-Medium.ttf | Regular font file name. (Font files should be placed in the fonts folder.)                                         |
| fonts.bold              | required | Roboto-Bold.ttf   | Bold font file name. (Font files should be placed in the fonts folder.)                                            |

* for language-support, units, latitude and longitude please refer to -> **[DarkSky API Docs](https://darksky.net/dev/docs/forecast)**


### setup the services
```bash
cd
cd WeatherPi
sudo cp WeatherPi_Service.sh /etc/init.d/WeatherPi
sudo chmod +x /etc/init.d/WeatherPi
sudo chmod +x WeatherPi.py
sudo systemctl enable WeatherPi
```

### run python with root privileges
* this is useful if you like to run your python scripts on boot and with sudo support in python
```bash
sudo chown -v root:root /usr/bin/python3
sudo chmod -v u+s /usr/bin/python3
```

### setting up python3 as default interpreter
* this should start your wanted python version just by typing `python` in the terminal
* helps if you have projects in python2 and python3 and don't want to hassle with the python version in your service scripts

```bash
update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1
update-alternatives --install /usr/bin/python python /usr/bin/python3.5 2
```

### update all python modules
* open up a python console
```bash
python3
```

* than run this line by line
```python
import pip
from subprocess import call
for dist in pip.get_installed_distributions():
    call("pip install --upgrade " + dist.project_name, shell=True)
```

* if you use DHT11, DHT22 and AM2302 sensor, install Adafruit_DHT
```bash
sudo pip3 install Adafruit_DHT
```

### test
```bash
./WeatherPi.py [--debug]
```

## I18n

You can change the display language of dates and information.


<img width="480" alt="480x320 ja" src="https://user-images.githubusercontent.com/129797/56856869-5a775f80-699f-11e9-9c37-ba41ab48d696.png">


fig 480x320 ja


<img width="240" alt="240x320 ja" src="https://user-images.githubusercontent.com/129797/56856844-c0171c00-699e-11e9-9a83-4522546b8d0f.png">

fig 240x320 ja

### Font
* Get the TryeType font and put it in the fonts folder

### Translation files
* init message.po file
```bash
cd locale
cp -Rp en <your language>
```

* edit messages.po (msgstr section).
```bash
msgfmt <your language>/LC_MESSAGES/messages.po -o <your language>/LC_MESSAGES/messages.po
```

## Modules
```
TODO: write a document for built-in and external modules
```
### Built-in Modules

| Name            | Description                         | Options       | Size              |
| --------------- | ----------------------------------- | ------------- | ----------------- |
| Alerts          | Any severe weather alerts pertinent |               | 240x15 - 480x15   |
| Clock           | Current Time                        |               | 140x60            |
| Location        | Current location                    |               | 140x15            |
| Weather         | Current Weather                     |               | 240x100 - 480x100 |
| WeatherForecast | Weather Forcusts                    | forecast_days | 240x80 - 480x80   |
| SunriseSuset    | Sunsine, Sunset time                |               | 80x80             |
| MoonPhase       | Moon MoonPhase                      |               | 80x80             |
| Wind            | Wind direction, speed               |               | 80x80             |

### External modules

| Name      | Description                                                  | Options                 | Size            |
| --------- | ------------------------------------------------------------ | ----------------------- | --------------- |
| JMAAlerts | JMA weather alerts<br>(気象庁の注意報、警報、特別警報を表示) |                         | 240x15 - 480x15 |
| DHT       | Adafruit temperature/humidity sensor                         | pin<br>correction_value | 100x60          |
| PIR       | PIR(Passive Infrared Ray）Motion Sensor                      | pin<br>power_save_delay | -               |

## Credit
* original software: [WeatherPi_TFT](https://github.com/LoveBootCaptain/WeatherPi_TFT)
* [squix78](https://github.com/squix78) for his [esp8266 weather station color](https://github.com/squix78/esp8266-weather-station-color) which inspired me to make it in python for a raspberry and another weather api
* [adafruit](https://github.com/adafruit) for [hardware](https://www.adafruit.com/) and [tutorials](https://learn.adafruit.com/)
* [darksky / forecast.io](https://darksky.net) weather api and [documentation](https://darksky.net/dev/)
* fonts: [google](https://fonts.google.com/)
* fonts: [Noto-Sans-CJK-JP](https://github.com/minoryorg/Noto-Sans-CJK-JP)
