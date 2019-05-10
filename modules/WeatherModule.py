import datetime
import io
import logging
import math
import os
import pygame
import requests
import sys
from functools import lru_cache


class Utils:
    color_maps = [
        # hot: red
        {
            "celsius_a": 28,
            "celsius_b": 99,
            "color_a": pygame.Color("red")[:3],
            "color_b": pygame.Color("red")[:3]
        },
        # fine: orange - red
        {
            "celsius_a": 23,
            "celsius_b": 28,
            "color_a": pygame.Color("orange")[:3],
            "color_b": pygame.Color("red")[:3]
        },
        # chilly: white - orange
        {
            "celsius_a": 15,
            "celsius_b": 23,
            "color_a": pygame.Color("white")[:3],
            "color_b": pygame.Color("orange")[:3]
        },
        # cold: blue - white
        {
            "celsius_a": 0,
            "celsius_b": 15,
            "color_a": pygame.Color("blue")[:3],
            "color_b": pygame.Color("white")[:3]
        },
        # cold: blue
        {
            "celsius_a": -99,
            "celsius_b": 0,
            "color_a": pygame.Color("blue")[:3],
            "color_b": pygame.Color("blue")[:3]
        }
    ]

    @staticmethod
    def strftime(timestamp, format):
        return datetime.datetime.fromtimestamp(int(timestamp)).strftime(format)

    @staticmethod
    def percentage_text(value):
        return "{}%".format(value)

    @staticmethod
    def pressure_text(value):
        return "{}pa".format(value)

    @staticmethod
    def speed_text(value, units):
        return ("{}km/h" if units == "si" else "{}mi/h").format(value)

    @staticmethod
    def temparature_text(value, units):
        return ("{}°c" if units == "si" else "{}°f").format(value)

    @staticmethod
    def color(name):
        return pygame.Color(name)[:3]

    @staticmethod
    def heat_index(f, h):
        if (f < 80):
            return f
        return -42.379 + 2.04901523 * f + 10.14333127 * h - 0.22475541 * \
            f * h - 6.83783 * (10 ** -3) * (f ** 2) - 5.481717 * \
            (10 ** -2) * (h ** 2) + 1.22874 * (10 ** -3) * (f ** 2) * \
            h + 8.5282 * (10 ** -4) * f * (h ** 2) - 1.99 * \
            (10 ** -6) * (f ** 2) * (h ** 2)

    @staticmethod
    def celsius(f):
        return (f - 32.0) * 0.555556

    @staticmethod
    def fahrenheit(c):
        return (c * 1.8) + 32.0

    @staticmethod
    def heat_color(temperature, humidity, units):
        def gradation(color_a, color_b, val_a, val_b, val_x):
            def geometric(a, b, p):
                return int((b - a) * p / 100 + a)

            p = (val_x - val_a) / (val_b - val_a) * 100
            color_x = [geometric(color_a[i], color_b[i], p) for i in range(3)]
            return color_x

        f = Utils.fahrenheit(temperature) if units == "si" else temperature
        c = Utils.celsius(Utils.heat_index(f, humidity))

        color = Utils.color("white")
        for cm in Utils.color_maps:
            if cm["celsius_a"] <= c and c < cm["celsius_b"]:
                color = gradation(cm["color_a"], cm["color_b"],
                                  cm["celsius_a"], cm["celsius_b"], c)
                break
        return color

    @staticmethod
    def uv_color(uv_index):
        if uv_index < 3:
            color = "green"
        elif uv_index < 6:
            color = "yellow"
        elif uv_index < 8:
            color = "orange"
        elif uv_index < 11:
            color = "red"
        else:
            color = "violet"
        return Utils.color(color)

    @staticmethod
    def wind_bearing_text(angle):
        if angle > 11.25 and angle <= 33.75:
            text = "NNE"
        elif angle > 33.75 and angle <= 56.25:
            text = "NE"
        elif angle > 56.25 and angle <= 78.75:
            text = "ENE"
        elif angle > 78.75 and angle <= 101.25:
            text = "E"
        elif angle > 101.25 and angle <= 123.75:
            text = "ESE"
        elif angle > 123.75 and angle <= 146.25:
            text = "SE"
        elif angle > 146.25 and angle <= 168.75:
            text = "SSE"
        elif angle > 168.75 and angle <= 191.25:
            text = "S"
        elif angle > 191.25 and angle <= 213.75:
            text = "SSW"
        elif angle > 213.75 and angle <= 236.25:
            text = "SW"
        elif angle > 236.25 and angle <= 258.75:
            text = "WSW"
        elif angle > 258.75 and angle <= 281.25:
            text = "W"
        elif angle > 281.25 and angle <= 303.75:
            text = "WNW"
        elif angle > 303.75 and angle <= 326.25:
            text = "NW"
        elif angle > 326.25 and angle <= 348.75:
            text = "NNW"
        else:
            text = "N"
        return _(text)

    @staticmethod
    @lru_cache()
    def font(name, size, bold):
        logging.debug("font {} {}pxl loaded".format(name, size))
        return pygame.font.SysFont(name, size, bold)

    @staticmethod
    @lru_cache()
    def weather_icon(name, size):
        try:
            file = "{}/icons/{}.png".format(sys.path[0], name)
            if os.path.isfile(file):
                # get icons from local folder
                image = pygame.image.load(file)
            else:
                # get icons from DarkSky
                response = requests.get(
                    "https://darksky.net/images/weather-icons/{}.png".format(
                        name))
                response.raise_for_status()
                image = pygame.image.load(io.BytesIO(response.content))

            # replace color black to dimgray
            pixels = pygame.PixelArray(image)
            pixels.replace(pygame.Color("black"), pygame.Color("dimgray"))
            del pixels

            # resize icon
            (w, h) = image.get_size()
            if w >= h:
                (w, h) = (size, int(size / w * h))
            else:
                (w, h) = (int(size / w * h), size)
            image = pygame.transform.scale(image, (w, h))

            logging.debug("weather icon {} {} loaded".format(name, size))
            return image

        except Exception as e:
            logging.error(e, exc_info=True)
            return None

    @staticmethod
    @lru_cache()
    def moon_icon(age, size):
        image = pygame.Surface((size, size))
        radius = int(size / 2)

        # draw full moon
        pygame.draw.circle(image, pygame.Color("white"), (radius, radius),
                           radius)

        # draw shadow
        theta = age / 14.765 * math.pi
        sum_x = sum_l = 0
        for y in range(-radius, radius, 1):
            alpha = math.acos(y / radius)
            x = radius * math.sin(alpha)
            l = radius * math.cos(theta) * math.sin(alpha)
            if age < 15:
                start = (radius - x, radius + y)
                end = (radius + l, radius + y)
            else:
                start = (radius - l, radius + y)
                end = (radius + x, radius + y)
            pygame.draw.line(image, pygame.Color("dimgray"), start, end)
            sum_x += 2 * x
            sum_l += end[0] - start[0]
        logging.info("moon phase age: {} parcentage: {}%".format(
            age, round(100 - (sum_l / sum_x) * 100, 1)))
        return image

    @staticmethod
    @lru_cache()
    def wind_arrow_icon(wind_bearing, size):
        color = pygame.Color("white")
        width = 0.15 * size  # arrowhead width
        height = 0.25 * size  # arrowhead height

        radius = size / 2
        angle = (90 - wind_bearing) % 360
        theta = angle / 360 * math.pi * 2

        a = (radius + radius * math.cos(theta),
             radius - radius * math.sin(theta))
        b = (radius + radius * math.cos(theta + math.pi),
             radius - radius * math.sin(theta + math.pi))

        base_vector = (b[0] - a[0], b[1] - a[1])
        length = math.sqrt(base_vector[0]**2 + base_vector[1]**2)
        unit_vector = (base_vector[0] / length, base_vector[1] / length)

        l = (b[0] - unit_vector[1] * width - unit_vector[0] * height,
             b[1] + unit_vector[0] * width - unit_vector[1] * height)
        r = (b[0] + unit_vector[1] * width - unit_vector[0] * height,
             b[1] - unit_vector[0] * width - unit_vector[1] * height)

        image = pygame.Surface((size, size))
        pygame.draw.line(image, color, a, b, 2)
        pygame.draw.polygon(image, color, [b, l, r, b], 0)
        return image

    @staticmethod
    def display_sleep():
        DISPLAY_SLEEP = pygame.USEREVENT + 1
        pygame.event.post(pygame.event.Event(DISPLAY_SLEEP))

    @staticmethod
    def display_wakeup():
        DISPLAY_WAKEUP = pygame.USEREVENT + 2
        pygame.event.post(pygame.event.Event(DISPLAY_WAKEUP))


class WeatherModule:
    def __init__(self, fonts, location, language, units, config):
        self.fonts = fonts
        self.location = location
        self.language = language
        self.units = units
        self.config = config
        self.rect = pygame.Rect(config["rect"])
        self.surface = pygame.Surface((self.rect.width, self.rect.height))

    def quit(self):
        pass

    def draw(self, weather):
        pass

    def clear_surface(self):
        self.surface.fill(pygame.Color("black"))

    def update_screen(self, screen):
        screen.blit(self.surface, (self.rect.left, self.rect.top))

    def text_size(self, text, size, *, bold=False):
        return self.font(size, bold).size(text)

    def text_warp(self, text, line_width, size, *, bold=False, max_lines=0):
        font = self.font(size, bold)
        lines = []
        cur_line = ""
        cur_width = 0
        for c in text:
            (w, h) = font.size(c)
            if cur_width + w > line_width:
                lines.append(cur_line)
                cur_line = ""
                cur_width = 0
            cur_line += c
            cur_width += w
        if cur_line:
            lines.append(cur_line)
        if max_lines > 0 and len(lines) > max_lines:
            # Put a placeholder if the text is truncated
            lines = lines[:max_lines]
            lines[max_lines - 1] = lines[max_lines - 1][:-2] + ".."
        return lines

    def font(self, size, bold):
        name = self.fonts["name"]
        if type(size) is str:
            size = self.fonts["size"][size]
        return Utils.font(name, size, bold)

    def draw_text(self,
                  text,
                  position,
                  size,
                  color,
                  *,
                  bold=False,
                  align="left",
                  background="black"):
        """
        :param text: text to draw
        :param position: render relative position (x, y)
        :param size: font size. ["small", "medium", "large"]
        :param color: color name or RGB color tuple
        :param bold: bold flag.
        :param align: text align. ["left", "center", "right"]
        :param background: background color
        """
        if not text:
            return

        (x, y) = position
        font = self.font(size, bold)
        size = font.size(text)
        color = Utils.color(color) if isinstance(color, str) else color
        if align == "center":
            x = (self.rect.width - size[0]) / 2
        elif align == "right":
            x = self.rect.width - size[0]
        self.surface.blit(font.render(text, True, color, background), (x, y))
        (right, bottom) = (x + size[0], size[1])
        return right, bottom

    def draw_image(self, image, position, angle=0):
        """
        :param image: image to draw
        :param position: render relative position (x, y)
        :param angle: counterclockwise  degrees angle
        """
        if not image:
            return

        (x, y) = position
        (w, h) = image.get_size()
        if angle:
            image = pygame.transform.rotate(image, angle)
            x = x + (w - image.get_width()) / 2
            y = h + (h - image.get_height()) / 2
        self.surface.blit(image, (x, y))
        (right, bottom) = (x + w, y + h)
        return right, bottom
