# pylint: disable=invalid-name,too-many-locals
"""Utility class and WeatherModule class
"""

import datetime
import io
import logging
import math
import os
import sys
from functools import lru_cache
import requests
import pygame


class Utils:
    """Utility class
    """
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
    def strftime(timestamp, fmt):
        """
        Format unix timestamp to text.
        """
        return datetime.datetime.fromtimestamp(int(timestamp)).strftime(fmt)

    @staticmethod
    def percentage_text(value):
        """
        Format percentega value to text.
        """
        return "{}%".format(value)

    @staticmethod
    def pressure_text(value):
        """
        Format pressure value to text.
        """
        return "{}pa".format(value)

    @staticmethod
    def speed_text(value, units):
        """
        Format speed value to text
        """
        return ("{}km/h" if units == "si" else "{}mi/h").format(value)

    @staticmethod
    def temperature_text(value, units):
        """
        Format temperature value to text
        """
        return ("{}°c" if units == "si" else "{}°f").format(value)

    @staticmethod
    def color(name):
        """
        Convert Color name to RGB value
        """
        return pygame.Color(name)[:3]

    @staticmethod
    def heat_index(f, h):
        """
        Calculate heat index from temperature and humidity
        """
        if f < 80:
            return f
        return -42.379 + 2.04901523 * f + 10.14333127 * h - 0.22475541 * \
            f * h - 6.83783 * (10 ** -3) * (f ** 2) - 5.481717 * \
            (10 ** -2) * (h ** 2) + 1.22874 * (10 ** -3) * (f ** 2) * \
            h + 8.5282 * (10 ** -4) * f * (h ** 2) - 1.99 * \
            (10 ** -6) * (f ** 2) * (h ** 2)

    @staticmethod
    def celsius(value):
        """
        Convert fahrenheit to celsius
        """
        return (value - 32.0) * 0.555556

    @staticmethod
    def fahrenheit(value):
        """
        Convert  celsius to fahrenheit
        """
        return (value * 1.8) + 32.0

    @staticmethod
    def heat_color(temperature, humidity, units):
        """
        Return heat index color
        """

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
            if cm["celsius_a"] <= c < cm["celsius_b"]:
                color = gradation(cm["color_a"], cm["color_b"],
                                  cm["celsius_a"], cm["celsius_b"], c)
                break
        return color

    @staticmethod
    def uv_color(uv_index):
        """
        Return UV index color
        """
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
        """Return wind bearig text
        """
        if 11.25 < angle <= 33.75:
            text = "NNE"
        elif 33.75 < angle <= 56.25:
            text = "NE"
        elif 56.25 < angle <= 78.75:
            text = "ENE"
        elif 78.75 < angle <= 101.25:
            text = "E"
        elif 101.25 < angle <= 123.75:
            text = "ESE"
        elif 123.75 < angle <= 146.25:
            text = "SE"
        elif 146.25 < angle <= 168.75:
            text = "SSE"
        elif 168.75 < angle <= 191.25:
            text = "S"
        elif 191.25 < angle <= 213.75:
            text = "SSW"
        elif 213.75 < angle <= 236.25:
            text = "SW"
        elif 236.25 < angle <= 258.75:
            text = "WSW"
        elif 258.75 < angle <= 281.25:
            text = "W"
        elif 281.25 < angle <= 303.75:
            text = "WNW"
        elif 303.75 < angle <= 326.25:
            text = "NW"
        elif 326.25 < angle <= 348.75:
            text = "NNW"
        else:
            text = "N"
        return _(text)

    @staticmethod
    @lru_cache()
    def font(name, size, bold):
        """Create a new Font object
        """
        logging.debug("font %s %spxl loaded", name, size)
        return pygame.font.SysFont(name, size, bold)

    @staticmethod
    @lru_cache()
    def weather_icon(name, size):
        """Create a weather image
        """
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

            logging.debug("weather icon %s %s loaded", name, size)
            return image

        except Exception as e:
            logging.error(e, exc_info=True)
            return None

    @staticmethod
    @lru_cache()
    def moon_icon(age, size):
        """Create a moon phase image
        """
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
        logging.info("moon phase age: %s parcentage: %s", age,
                     round(100 - (sum_l / sum_x) * 100, 1))
        return image

    @staticmethod
    @lru_cache()
    def wind_arrow_icon(wind_bearing, size):
        """Create a wind direction allow image
        """
        color = pygame.Color("white")
        width = 0.15 * size  # arrowhead width
        height = 0.25 * size  # arrowhead height

        radius = size / 2
        angle = (90 - wind_bearing) % 360
        theta = angle / 360 * math.pi * 2

        tail = (radius + radius * math.cos(theta),
                radius - radius * math.sin(theta))
        head = (radius + radius * math.cos(theta + math.pi),
                radius - radius * math.sin(theta + math.pi))

        base_vector = (head[0] - tail[0], head[1] - tail[1])
        length = math.sqrt(base_vector[0]**2 + base_vector[1]**2)
        unit_vector = (base_vector[0] / length, base_vector[1] / length)

        left = (head[0] - unit_vector[1] * width - unit_vector[0] * height,
                head[1] + unit_vector[0] * width - unit_vector[1] * height)
        right = (head[0] + unit_vector[1] * width - unit_vector[0] * height,
                 head[1] - unit_vector[0] * width - unit_vector[1] * height)

        image = pygame.Surface((size, size))
        pygame.draw.line(image, color, tail, head, 2)
        pygame.draw.polygon(image, color, [head, left, right, head], 0)
        return image

    @staticmethod
    def display_sleep():
        """Send display sleep event
        """
        DISPLAY_SLEEP = pygame.USEREVENT + 1
        pygame.event.post(pygame.event.Event(DISPLAY_SLEEP))

    @staticmethod
    def display_wakeup():
        """Send display wakeup event
        """
        DISPLAY_WAKEUP = pygame.USEREVENT + 2
        pygame.event.post(pygame.event.Event(DISPLAY_WAKEUP))

    @staticmethod
    def restart():
        """
        send system restart event
        """
        RESTART = pygame.USEREVENT + 3
        pygame.event.post(pygame.event.Event(RESTART))


class WeatherModule:
    """Weather Module
    """

    def __init__(self, fonts, location, language, units, config):
        """Initialize
        """
        self.fonts = fonts
        self.location = location
        self.language = language
        self.units = units
        self.config = config
        self.rect = pygame.Rect(config["rect"])
        self.surface = pygame.Surface((self.rect.width, self.rect.height))

    def quit(self):
        """Destractor
        """

    def draw(self, screen, weather, updated):
        """Draw surface
        """

    def clear_surface(self):
        """Clear Surface
        """
        self.surface.fill(pygame.Color("black"))

    def update_screen(self, screen):
        """Draw surface on screen
        """
        screen.blit(self.surface, (self.rect.left, self.rect.top))

    def text_size(self, text, size, *, bold=False):
        """
        determine the amount of space needed to render text
        """
        if not text:
            return (0, 0)
        return self.font(size, bold).size(text)

    def text_warp(self, text, line_width, size, *, bold=False, max_lines=0):
        """
        Text wrapping
        """
        font = self.font(size, bold)
        lines = []
        cur_line = ""
        cur_width = 0
        for c in text:
            (w, _h) = font.size(c)
            if cur_width + w > line_width:
                lines.append(cur_line)
                cur_line = ""
                cur_width = 0
            cur_line += c
            cur_width += w
        if cur_line:
            lines.append(cur_line)
        if 0 < max_lines < len(lines):
            # Put a placeholder if the text is truncated
            lines = lines[:max_lines]
            lines[max_lines - 1] = lines[max_lines - 1][:-2] + ".."
        return lines

    def font(self, size, bold):
        """
        create a new Font object
        """
        name = self.fonts["name"]
        if isinstance(size, str):
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
        Draw text.

        Parameters
        ----------
        text:
            text to draw
        position:
            render relative position (x, y)
        size:
            font size. ["small", "medium", "large"]
        color:
            color name or RGB color tuple
        bold:
            bold flag.
        align:
            text align. ["left", "center", "right"]
        background:
            background color
        """
        if not text:
            return position

        (x, y) = position
        font = self.font(size, bold)
        (w, h) = font.size(text)
        color = Utils.color(color) if isinstance(color, str) else color
        if align == "center":
            x = (self.rect.width - w) / 2
        elif align == "right":
            x = self.rect.width - w
        self.surface.blit(font.render(text, True, color, background), (x, y))
        (right, bottom) = (x + w, h)
        return right, bottom

    def draw_image(self, image, position, angle=0):
        """
        Draw an image.

        Parameters
        ----------
        image:
            image to draw
        position:
            render relative position (x, y)
        angle:
            counterclockwise  degrees angle
        """
        if not image:
            return position

        (x, y) = position
        (w, h) = image.get_size()
        if angle:
            image = pygame.transform.rotate(image, angle)
            x = x + (w - image.get_width()) / 2
            y = h + (h - image.get_height()) / 2
        self.surface.blit(image, (x, y))
        (right, bottom) = (x + w, y + h)
        return right, bottom
