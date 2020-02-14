# WeatherPi

Weather Station for Raspberry Pi and Small LCDs  
(Raspberry Piと小型液晶向けのウェザーステーション)

![Front View](https://user-images.githubusercontent.com/129797/56935584-e8348580-6b2c-11e9-940a-002c280885bd.png)


<img width="480" alt="480x320 en" src="https://user-images.githubusercontent.com/129797/56856836-95c55e80-699e-11e9-8d4d-7422eef36732.png">

fig: 480x320 en

<img width="240" alt="240x320 en" src="https://user-images.githubusercontent.com/129797/56856807-9f9a9200-699d-11e9-8730-7571c7249ea7.png">

fig: 240x320 en

## Feature
* Modularized display parts  
  (表示パーツはモジュール化してあるので、カスタマイズが可能です)
* Heat Index color / UV Index color support  
  (Heat Index/UV Indexで表示色を変更します)
* Custom module support
  (カスタムモジュールを作成して組み込むことができます)  
  [External modules](#external-modules)
* i18n (internationalization) support  
  (ロケールの変更や表示文字列の翻訳が可能です)  
  [I18n](#I18n)

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
| Name                    |          | Default                                  | Description                                                                                                        |
| ----------------------- | -------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| darksky_api_key         | required |                                          | **[DarkSky API Key](https://darksky.net/dev)**                                                                     |
| google_api_key          | optional |                                          | [Google Geocoding API darksky_api_key](https://developers.google.com/maps/documentation/geocoding/start)           |
| address                 | optional |                                          | The address of a location. <br> latitude and longitude can be omitted if google_api_key and address are specified. |
| latitude <br> longitude | required |                                          | The latitude and longitude of a location (in decimal degrees). Positive is east, negative is west.                 |
| locale                  | required | en_US.UTF-8                              | Locale. Specify the display language of time and weather information.                                              |
| units                   | required | si                                       | Unit of weather　information.                                                                                      |
| SDL_FBDEV               | required | /dev/fb1                                 | Frame buffer device to use in the linux fbcon driver, instead of /dev/fb0.                                         |
| display                 | required |                                          | Display size. [Width, Height]                                                                                      |
| fonts.name              | required | Sans                                     | Font name.                                                                                                         |
| fonts.size              | required | {"large": 30, "medium": 22, "small": 14} | Font size list. (Style name and point)                                                                             |


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

* if you use DigistampTemper, install pyusb
```bash
sudo pip3 install pyusb
```

* if you use WeatherForcustGraph, install matplotlib
```bash
sudo pip3 install matplotlib
```

### test
```bash
./WeatherPi.py [--debug]
```

## Customize weather icons
By default, the DarkSky icon is resized to display, but you can change it to any icon you like.
To change the icons, place the following 10 icons in the icons folder:  
(デフォルトではDarkSkyのアイコンを表示しますが、iconsフォルダに以下の10個のファイルを用意すれば、変更することができます。)

* clear-day.png, clear-night.png, rain.png, snow.png, sleet.png, wind.png, fog.png, cloudy.png, partly-cloudy-day.png, partly-cloudy-night.png

| Name            | Default                                                                          | Name                    | Default                                                                                  |
| --------------- | -------------------------------------------------------------------------------- | ----------------------- | ---------------------------------------------------------------------------------------- |
| clear-day.png   | <img width="100" src="https://darksky.net/images/weather-icons/clear-day.png">   | wind.png                | <img width="100" src="https://darksky.net/images/weather-icons/wind.png">                |
| clear-night.png | <img width="100" src="https://darksky.net/images/weather-icons/clear-night.png"> | fog.png                 | <img width="100" src="https://darksky.net/images/weather-icons/fog.png">                 |
| rain.png        | <img width="100" src="https://darksky.net/images/weather-icons/rain.png">        | cloudy.png              | <img width="100" src="https://darksky.net/images/weather-icons/cloudy.png">              |
| snow.png        | <img width="100" src="https://darksky.net/images/weather-icons/snow.png">        | partly-cloudy-day.png   | <img width="100" src="https://darksky.net/images/weather-icons/partly-cloudy-day.png">   |
| sleet.png       | <img width="100" src="https://darksky.net/images/weather-icons/sleet.png">       | partly-cloudy-night.png | <img width="100" src="https://darksky.net/images/weather-icons/partly-cloudy-night.png"> |



## I18n

You can change the display language of dates and information.  
(日付と情報の表示言語を変更することができます。)


<img width="480" alt="480x320 ja" src="https://user-images.githubusercontent.com/129797/56856869-5a775f80-699f-11e9-9c37-ba41ab48d696.png">


fig 480x320 ja


<img width="240" alt="240x320 ja" src="https://user-images.githubusercontent.com/129797/56856844-c0171c00-699e-11e9-9a83-4522546b8d0f.png">

fig 240x320 ja

### Font
Install the font for your locale. I recommend [Google Fonts](https://fonts.google.com/) and [Google NotoFonts](https://www.google.com/get/noto/).  
(ロケールにあったフォントをインストールします。日本語であれば、"Noto Sans CJK JP"をインストールして、等幅フォント"Noto Sans CJK JP"を設定することを勧めます。)

[How to install fonts](https://www.google.com/get/noto/help/install/)

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
All modules require the following configuration:
```
"modules": [
  {
    "module": "<Module Name>",
    "config": {
      "rect": [<x>, <y>, <width>, <height>]
    }
  }
```

### Built-in Modules
| Name            | Description                         | Options                                 | Size              |
| --------------- | ----------------------------------- | --------------------------------------- | ----------------- |
| Alerts          | Any severe weather alerts pertinent | None                                    | 240x15 - 480x15   |
| Clock           | Current Time                        | None                                    | 140x60            |
| Location        | Current location                    |                                         | 140x15            |
| Weather         | Current Weather                     | icon_size (default 100)                 | 240x100 - 480x100 |
| WeatherForecast | Weather Forecast                    | forecast_days<br>icon_size (default 50) | 240x80 - 480x80   |
| SunriseSuset    | Sunrise, Sunset time                | icon_size (default 40)                  | 80x80             |
| MoonPhase       | Moon Phase                          | icon_size (default 50)                  | 80x80             |
| Wind            | Wind direction, speed               | icon_size (default 30)                  | 80x80             |


### External modules
| Name                                                            | Description                                                             | Options                                                                                                                                                                               | Size              |
| --------------------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| DHT                                                             | Adafruit temperature/humidity sensor                                    | pin: pin number<br>correction_value: (調整値)                                                                                                                                         | 60x60 - 70x120    |
| [DigistampTemper](https://github.com/miyaichi/DigisparkTemper)  | DigisparkTemper (usb temperature/humidity sensor)                       | correction_value: (調整値)                                                                                                                                                            | 60x60 - 70x120    |
| [IrMagitianT](http://www.omiya-giken.com/?page_id=837)          | Temperature sensor on the infrared remote control system "irMagician-T" | correction_value: (調整値)                                                                                                                                                            | 60x35 - 70x60     |
| [JMAAlerts](http://xml.kishou.go.jp/xmlpull.html)               | JMA weather alerts<br>(気象庁の注意報、警報、特別警報を表示)                  | prefecture: (都道府県)<br>city: (市区町村)                                                                                                                                            | 240x15 - 480x15   |
| [NatureRemo](https://nature.global/jp/landing-page-dm-g/)       | Temperature and humidity sensor on Nature Remo/Remo mini                | token: (access tokens to access Nature API)<br>name: (device name)                                                                                                                    | 100x60            |
| PIR                                                             | PIR(Passive Infrared Ray）Motion Sensor                                 | pin: pin number<br>power_save_delay: delay (in seconds) before the monitor will be turned off.                                                                                        | None              |
| SelfUpdate                                                      | Update and restart if there is a newer version on GitHub                | check_interval (default 86400 # once a day)                                                                                                                                           | -                 |
| [TEMPer](http://www.pcsensor.com/usb-hygrometer/temperhum.html) | TEMPerHUM/TEMPer thermometer & hygrometer                               | correction_value: (調整値)                                                                                                                                                            | 60x60 - 70x120    |
| WeatherForcustGraph                                             | Plots weather condition data for the next 48 hours.                     | conditions: Weather conditions to display.<br>Available weather conditions is following:<br>temperature, apparentTemperature, dewPoint, humidity, pressure, windSpeed, uvIndex, ozone | The size you want |

## Plots a graph
Temperature and humidity sensors and weather forecast data can be displayed in a graph.
（温湿度センサーや気象予想データをグラフで表示することができます。）

* Temperature and humidity sensor modules (DHT, DigisparkTemper, IrMagitianT, NatureRemo, TEMPer)
  Each module holds the last 6 hours of sensor data and can display it graphically. To plot the graph, define the graph drawing area with "graph_rect" parameter in the module config.
  （各モジュールは過去６時間分のセンサーデータを保持して、それをグラフで表示することができます。グラフを表示するには、モジュールのconfigに"graph_rect"パラメータでグラフの描画領域を定義します。）

  example config:
  ```
  {
    "module": "<Module name>",
    "config": {
      "rect": [x, y, width, height],
      ...
      "graph_rect": [x, y, width, height]
    }
  }
  ```

* WeatherGorcustGraph module
  It can graphically displays the weather data for the next 48 hours or 7 days provided by DarkSky. To plot the graph, define up to two weather condition names with the conditions parameter in the module's config.
  （DarkSkyが提供する今後48時間または7日間の天気データをグラフィカルに表示できます。グラフを表示するには、モジュールのconfigにconditionsパラメータで気象条件名を最大２つまで定義します。）

  ![fig](https://user-images.githubusercontent.com/129797/74575281-b4e2ba80-4fc9-11ea-8b8b-72ca6b28c418.png)

  example config:
  ```
  {
    "module": "WeatherForcustGraph",
    "config": {
      "rect": [x, y, width, height],
      "block": "hourly",
      "conditions": ["temperature", "humidity"]
    }
  }
  ```

  * Abailable block and conditions are following:
    （有効なblockとconditionは以下の通りです）
    hourly:
        temperature, apparentTemperature, dewPoint, humidity,
        pressure, windSpeed, uvIndex, ozone
    daily:
        precipIntensity, precipIntensityMax, precipProbability,
        temperatureHigh, temperatureLow, apparentTemperatureHigh,
        apparentTemperatureLow, dewPoint, humidity, pressure,
        windSpeed, windGust, cloudCover, uvIndex, uvIndexTime,
        visibility, ozone, temperatureMin, temperatureMax,
        apparentTemperatureMin, "apparentTemperatureMax

    Refer: https://darksky.net/dev/docs

## Credit

* [WeatherPi_TFT](https://github.com/LoveBootCaptain/WeatherPi_TFT) His wonderful software is the beginning of my project
* [adafruit](https://github.com/adafruit) for [hardware](https://www.adafruit.com/) and [tutorials](https://learn.adafruit.com/)
* [DarkSky / forecast.io](https://darksky.net) weather api and [documentation](https://darksky.net/dev/)
* [気象庁防災情報XMLフォーマット](http://xml.kishou.go.jp/)
* [Google Fonts](https://fonts.google.com/)
* [Google NotoFonts](https://www.google.com/get/noto/)
