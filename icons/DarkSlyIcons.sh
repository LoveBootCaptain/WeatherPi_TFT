#!/bin/sh

for name in "clear-day" "clear-night" "cloudy" "fog"\
            "partly-cloudy-day" "partly-cloudy-night" "rain"\
            "sleet" "snow" "wind"; do

    url="https://darksky.net/images/weather-icons/${name}.png"
    curl -O ${url}

done
