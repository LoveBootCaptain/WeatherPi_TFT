import gettext
import logging
import time
from modules.WeatherModule import WeatherModule, Utils


class Alerts(WeatherModule):
    def draw(self, weather):
        if weather is None:
            message = "waiting for weather forecast data ..."
        elif "alerts" in weather:
            message = weather["alerts"]["title"]
        else:
            message = None

        if message:
            logging.info(message)
            self.draw_text(message, "regular", "small", "white",
                           (0, self.rect.height / 2), "center")


class Clock(WeatherModule):
    def draw(self, weather):
        timestamp = time.time()
        locale_date = Utils.strftime(timestamp, "%a, %x")
        locale_time = Utils.strftime(timestamp, "%H:%M")
        locale_second = Utils.strftime(timestamp, "%S")

        self.draw_text(locale_date, "bold", "small", "white", (10, 4))
        self.draw_text(locale_time, "regular", "large", "white", (10, 19))
        self.draw_text(locale_second, "regular", "medium", "white", (92, 19))


class Weather(WeatherModule):
    def __init__(self, screen, fonts, language, units, config):
        super().__init__(screen, fonts, language, units, config)
        self.rain_icon = self.load_icon("preciprain.png")
        self.snow_icon = self.load_icon("precipsnow.png")
        self.weather_icons = {}
        for name in ("clear-day", "clear-night", "cloudy", "fog",
                     "partly-cloudy-day", "partly-cloudy-night", "rain",
                     "sleet", "snow", "wind"):
            self.weather_icons[name] = self.get_darksky_icon(name, 100)

    def draw(self, weather):
        if weather is None:
            return

        currently = weather["currently"]
        summary = currently["summary"]
        temperature = currently["temperature"]
        humidity = currently["humidity"]

        color = Utils.heat_color(temperature, humidity, self.units)
        temperature = Utils.temparature_text(round(temperature, 1), self.units)

        # If precipIntensity is zero, then this property will not be defined
        precip_porobability = currently["precipProbability"]
        if precip_porobability:
            precip_porobability = Utils.percentage_text(
                round(precip_porobability * 100, 1))
            precip_type = currently["precipType"]
        else:
            precip_porobability = Utils.percentage_text(0)
            precip_type = "Precipitation"

        weather_icon = self.weather_icons[currently["icon"]]

        self.draw_text(summary, "bold", "small", "white", (120, 5))
        self.draw_text(temperature, "regular", "large", color, (0, 25),
                       "right")
        self.draw_text(precip_porobability, "regular", "large", color,
                       (120, 55), "right")
        self.draw_text(
            _(precip_type), "bold", "small", color, (0, 90), "right")
        self.draw_image(weather_icon, (10, 5))

        if precip_type == "rain":
            self.draw_image(self.rain_icon, (120, 65))
        elif precip_type == "show":
            self.draw_image(self.snow_icon, (120, 65))


class DailyWeatherForecast(WeatherModule):
    def __init__(self, screen, fonts, language, units, config, weather_icons):
        super().__init__(screen, fonts, language, units, config)
        self.weather_icons = weather_icons

    def draw(self, weather, day):
        if weather is None:
            return

        daily = weather["daily"]["data"][day]
        day_of_week = Utils.strftime(daily["time"], "%a")
        temperature = "{} | {}".format(
            int(daily["temperatureMin"]), int(daily["temperatureMax"]))
        weather_icon = self.weather_icons[daily["icon"]]

        self.draw_text(day_of_week, "bold", "small", "orange", (0, 0),
                       "center")
        self.draw_text(temperature, "bold", "small", "white", (0, 15),
                       "center")
        self.draw_image(weather_icon, (15, 35))


class WeatherForecast(WeatherModule):
    def __init__(self, screen, fonts, language, units, config):
        super().__init__(screen, fonts, language, units, config)
        weather_icons = {}
        for name in ("clear-day", "clear-night", "cloudy", "fog",
                     "partly-cloudy-day", "partly-cloudy-night", "rain",
                     "sleet", "snow", "wind"):
            weather_icons[name] = self.get_darksky_icon(name, 50)

        self.forecast_days = config["forecast_days"]
        self.forecast_modules = []
        width = self.rect.width / self.forecast_days
        for i in range(self.forecast_days):
            config["rect"] = [
                self.rect.x + i * width, self.rect.y, width, self.rect.height
            ]
            self.forecast_modules.append(
                DailyWeatherForecast(screen, fonts, language, units, config,
                                     weather_icons))

    def draw(self, weather):
        if weather is None:
            return

        for i in range(self.forecast_days):
            self.forecast_modules[i].draw(weather, i + 1)


class SunriseSuset(WeatherModule):
    def __init__(self, screen, fonts, language, units, config):
        super().__init__(screen, fonts, language, units, config)
        self.sunrise_icon = self.load_icon("sunrise.png")
        self.sunset_icon = self.load_icon("sunset.png")

    def draw(self, weather):
        if weather is None:
            return

        daily = weather["daily"]["data"]
        surise = Utils.strftime(int(daily[0]["sunriseTime"]), "%H:%M")
        sunset = Utils.strftime(int(daily[0]["sunsetTime"]), "%H:%M")

        self.draw_image(self.sunrise_icon, (10, 20))
        self.draw_image(self.sunset_icon, (10, 50))
        self.draw_text(surise, "bold", "small", "white", (0, 25), "right")
        self.draw_text(sunset, "bold", "small", "white", (0, 55), "right")


class MoonPhase(WeatherModule):
    def __init__(self, screen, fonts, language, units, config):
        super().__init__(screen, fonts, language, units, config)
        self.moon_icons = {}
        for i in range(28):
            self.moon_icons[str(i)] = self.load_icon("moon-{}.png".format(i))

    def draw(self, weather):
        if weather is None:
            return

        daily = weather["daily"]["data"]
        moon_phase = int((float(daily[0]["moonPhase"]) * 100 / 3.57) + 0.25)
        moon_icon = self.moon_icons[str(moon_phase)]

        self.draw_image(moon_icon, (10, 10))


class Wind(WeatherModule):
    def __init__(self, screen, fonts, language, units, config):
        super().__init__(screen, fonts, language, units, config)
        self.circle_icon = self.load_icon("circle.png")
        self.arrow_icon = self.load_icon("arrow.png")

    def draw(self, weather):
        if weather is None:
            return

        currently = weather["currently"]
        wind_speed = Utils.speed_text(
            round((float(currently["windSpeed"]) * 1.609344), 1), self.units)
        wind_bearing = currently["windBearing"]
        angle = 360 - wind_bearing + 180

        self.draw_text("N", "bold", "small", "white", (0, 10), "center")
        self.draw_text(wind_speed, "bold", "small", "white", (0, 60), "center")
        self.draw_image(self.circle_icon, (25, 30))
        self.draw_image(self.arrow_icon, (25, 35), angle)
