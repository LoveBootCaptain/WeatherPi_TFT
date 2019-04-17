#!/bin/sh

# get Darksky Weather Icons
for name in "clear-day" "clear-night" "cloudy" "fog"\
            "partly-cloudy-day" "partly-cloudy-night" "rain"\
            "sleet" "snow" "wind"; do

    curl -o icons/${name}.png "https://darksky.net/images/weather-icons/${name}.png"
done
