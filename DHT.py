import Adafruit_DHT
import sys

color_maps = [
    # hot: red
    {"celsius_a": 28, "celsius_b": 99, "color_a": "#ff0000", "color_b": "#ff0000"},
    # fine: orenge - red
    {"celsius_a": 23, "celsius_b": 28, "color_a": "#ffa500", "color_b": "#ff0000"},
    # chilly: white - orenge
    {"celsius_a": 15, "celsius_b": 23, "color_a": "#ffffff", "color_b": "#ffa500"},
    # cold: blue - white
    {"celsius_a": 0, "celsius_b": 15, "color_a": "#0000ff", "color_b": "#ffffff"},
    # cold: blue
    {"celsius_a": -99, "celsius_b": 0, "color_a": "#0000ff", "color_b": "#0000ff"}
]


def hex_to_rgb(hex):
    hex = hex.lstrip("#")
    return tuple(int(hex[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#" + "".join(map(lambda x: "{:02x}".format(x), rgb))


def geometric(a, b, p):
    return int((b - a) * p / 100 + a)


def gradation(color_a, color_b, val_a, val_b, val_x):
    p = (val_x - val_a) / (val_b - val_a) * 100
    rgb_a = hex_to_rgb(color_a)
    rgb_b = hex_to_rgb(color_b)
    rgb_x = [geometric(rgb_a[i], rgb_b[i], p) for i in range(3)]
    return rgb_to_hex(rgb_x)


def fahrenheit(c):
    return (c * 1.8) + 32.0


def celsius(f):
    return (f - 32.0) * 0.555556


def heat_index(f, h):
    if (f < 80):
        return f
    return -42.379 + 2.04901523 * f + 10.14333127 * h - 0.22475541 * \
        f * h - 6.83783 * (10 ** -3) * (f ** 2) - 5.481717 * \
        (10 ** -2) * (h ** 2) + 1.22874 * (10 ** -3) * (f ** 2) * \
        h + 8.5282 * (10 ** -4) * f * (h ** 2) - 1.99 * \
        (10 ** -6) * (f ** 2) * (h ** 2)


def heat_color(f):
    c = celsius(f)
    color = "#ffffff"  # white
    for cm in color_maps:
        if cm["celsius_a"] <= c and c < cm["celsius_b"]:
            color = gradation(cm["color_a"], cm["color_b"], cm["celsius_a"],
                              cm["celsius_b"], c)
            break
    return color


def read(sensor, pin, unit):
    sensor_type = {
        "11": Adafruit_DHT.DHT11,
        "22": Adafruit_DHT.DHT22,
        "2302": Adafruit_DHT.AM2302
    }
    sensor = sensor_type[sensor]
    h, c = Adafruit_DHT.read_retry(sensor, pin)
    if h is None or c is None:
        return (None, None, None)

    f = fahrenheit(c)
    index = heat_index(f, h)
    color = heat_color(index)

    t = c if unit == "si" else f

    return (rount(t, 1), round(h, 1), color)


if __name__ == "__main__":
    (temparature, humidity, color) = read("11", "10, "si")
    print("temparature: {} humidity: {} color: {}".format(
        temparature, humidity, color))
