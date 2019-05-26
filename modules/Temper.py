# pylint: disable=invalid-name, too-many-locals, broad-except
"""Temper module
"""

import os
import re
import select
import struct
import logging
import serial

from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer


def find_temper():
    """Find Temper device
    """

    def read_file(path):
        try:
            with open(path, "r") as fp:
                return fp.read().strip()
        except IOError:
            return None

    def find_devices(path):
        devices = []
        for entry in os.scandir(path):
            if entry.is_dir() and not entry.is_symlink():
                devices.extend(find_devices(os.path.join(path, entry.name)))
            if re.search("tty.*[0-9]", entry.name):
                devices.append(entry.name)
            if re.search("hidraw[0-9]", entry.name):
                devices.append(entry.name)
        return sorted(devices)

    usb_devices = "/sys/bus/usb/devices"
    device = None
    for entry in os.scandir(usb_devices):
        if not entry.is_dir():
            continue

        path = os.path.join(usb_devices, entry.name)
        vendor_id = read_file(os.path.join(path, "idVendor"))
        product_id = read_file(os.path.join(path, "idProduct"))
        bus_no = read_file(os.path.join(path, "busnum"))
        dev_no = read_file(os.path.join(path, "devnum"))
        if not vendor_id or not product_id:
            continue

        if vendor_id == "413d" and product_id == "2107":
            devices = find_devices(path)
            device = os.path.join("/dev/", devices[-1])
            logging.info("Temper: Bus %s Device %s: ID %s:%s Device %s",
                         bus_no, dev_no, vendor_id, product_id, device)
            break

    return device


def read_serial(device):
    """Read tempareture and humidity from serial
    """
    with serial.Serial(device, 9600, timeout=1) as s:
        s.write(b"ReadTemp")
        data = str(s.readline(), "latin-1").strip()
        data += str(s.readline(), "latin-1").strip()

    celsius = humidity = None
    m = re.search(r"Temp-Inner:([0-9.]*).*, ?([0-9.]*)", data)
    if m is not None:
        celsius = float(m.group(1))
        humidity = float(m.group(2))
    return humidity, celsius


def read_hidraw(device):
    """Read tempareture and humidity from hidraw
    """

    def parse_bytes(data, offset, divisor):
        if data[offset] == 0x4e and data[offset + 1] == 0x20:
            return None
        return struct.unpack_from(">h", data, offset)[0] / divisor

    fd = os.open(device, os.O_RDWR)
    os.write(fd, struct.pack("8B", 0x01, 0x80, 0x33, 0x01, 0, 0, 0, 0))
    data = b""
    while True:
        rready, _wready, _xready = select.select([fd], [], [], 0.1)
        if fd not in rready:
            break
        data += os.read(fd, 8)
    os.close(fd)
    celsius = parse_bytes(data, 2, 100.0)
    humidity = parse_bytes(data, 4, 100.0)
    return humidity, celsius


def read_temperature_and_humidity(device, correction_value):
    """Read tempareture and humidity from Temper
    """
    try:
        if device.startswith("/dev/hidraw"):
            humidity, celsius = read_hidraw(device)
        elif device.startswith("/dev/tty"):
            humidity, celsius = read_serial(device)

        celsius = round(celsius + correction_value, 1)
        humidity = round(humidity, 1)
        logging.info("Celsius: %s Humidity: %s", celsius, humidity)
        return humidity, celsius

    except Exception as e:
        logging.error(e, exc_info=True)
        return None


class Temper(WeatherModule):
    """
    Temper module

    This module gets data form Temper sensors and display it
    in Heat Index color.

    example config:
    {
      "module": "DHT",
      "config": {
        "rect": [x, y, width, height],
        "correction_value": -8
      }
     }
    """

    def __init__(self, fonts, location, language, units, config):
        super().__init__(fonts, location, language, units, config)
        self.device = None
        self.correction_value = None
        self.timer_thread = None
        self.last_hash_value = None

        self.correction_value = float(config["correction_value"])
        self.device = find_temper()
        if not self.device:
            logging.error("%s: device not found", __class__.__name__)
            raise Exception()

        # start sensor thread
        self.timer_thread = RepeatedTimer(20, read_temperature_and_humidity,
                                          [self.device, self.correction_value])
        self.timer_thread.start()

    def quit(self):
        if self.timer_thread:
            self.timer_thread.quit()

    def draw(self, screen, weather, updated):
        # No result yet
        result = self.timer_thread.get_result()
        if result is None:
            logging.info("%s: No data from sensor", __class__.__name__)
            return

        # Has the value changed
        hash_value = self.timer_thread.get_hash_value()
        if self.last_hash_value == hash_value:
            return
        self.last_hash_value = hash_value

        (humidity, celsius) = result

        color = Utils.heat_color(celsius, humidity, "si")
        temperature = Utils.temperature_text(
            celsius if self.units == "si" else Utils.fahrenheit(celsius),
            self.units)
        humidity = Utils.percentage_text(humidity) if humidity else None

        for size in ("large", "medium", "small"):
            # Horizontal
            message1 = "{}  {}".format(temperature, humidity)
            message2 = None
            w, h = self.text_size(message1, size, bold=True)
            if w <= self.rect.width and 20 + h <= self.rect.height:
                break

            # Vertical
            message1 = temperature
            message2 = humidity if humidity else None
            w1, h1 = self.text_size(message1, size, bold=True)
            w2, h2 = self.text_size(message2, size, bold=True)
            if max(w1,
                   w2) <= self.rect.width and 20 + h1 + h2 <= self.rect.height:
                break

        self.clear_surface()
        self.draw_text(_("Indoor"), (0, 0), "small", "white")
        (w, h) = self.draw_text(message1, (0, 20), size, color, bold=True)
        if message2:
            self.draw_text(message2, (0, 20 + h), size, color, bold=True)
        self.update_screen(screen)
