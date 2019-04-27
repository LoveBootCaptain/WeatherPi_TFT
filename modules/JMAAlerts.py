import gettext
import logging
from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer
from xml.etree import ElementTree as et


def alerts(prefectures, city):
    try:
        response = requests.get(
            "https://www.data.jma.go.jp/developer/xml/feed/extra.xml")
        response.raise_for_status()

        data = et.fromstring(response.content)
        ns = {"ns": "http://www.w3.org/2005/Atom"}
        url = None
        for element in root.findall("./ns:entry", ns):
            if element.find("ns:content", ns).text.find(prefectures) > -1:
                if element.find("ns:title", ns).text == "気象特別警報・警報・注意報":
                    url = element.find("ns:link", ns).attrib["href"]
                    logging.debug("{} {}".format(__class__.__name__), url)
                    break
        if not url:
            return None

        response = requests.get(url)
        response.raise_for_status()

        data = et.fromstring(response.content)
        ns = {"ns": "http://xml.kishou.go.jp/jmaxml1/body/meteorology1/"}
        return list(
            map(
                lambda x: x.text,
                root.findall(
                    "ns:Body/ns:Warning//*[ns:Name='{}}']../ns:Kind/ns:Name".
                    format(city), ns)))

    except Exception as e:
        logging.error(e, exc_info=True)
        return None


class JMAAlerts(WeatherModule):
    """
    気象庁 (Japan Meteorological Agency) alerts module

    example config:
    {
      "module": "JMAAlerts",
      "config": {
        "rect": [x, y, width, height]
       }
    }

    気象庁防災情報XMLフォーマット形式電文の公開（PULL型）で公開されているAtomフィードのうち、
    "高頻度フィード/随時"のフィードに掲載された都道府県のデータフィードから、指定した市区町村の
    注意報、警報、特別警報を取得し、表示する。

    参考：http://xml.kishou.go.jp/xmlpull.html
    """

    def __init__(self, fonts, location, language, units, config):
        super().__init__(fonts, location, language, units, config)
        self.city, self.prefectures = self.location["address"].split(",")
        self.timer_thread = RepeatedTimer(600, alerts,
                                          [self.prefectures, self.city])
        logging.info("{}: thread started".format(__class__.__name__))

    def quit(self):
        if self.timer_thread:
            logging.info("{}: thread stopped".format(__class__.__name__))
            self.timer_thread.quit()

    def draw(self, screen, weather, updated):
        if weather is None:
            message = "waiting for weather forecast data ..."
        else:
            result = self.timer_thread.result()
            if result:
                message = ",".join(result)
            else:
                message = ""

        self.clear_surface()
        if message:
            logging.debug("{}: {} {} {}".format(__class__.__name__,
                                                self.prefectures, self.city,
                                                message))
            for size in ("large", "medium", "small"):
                w, h = self.text_size(message, "bold", size)
                if w <= self.rect.width and h <= self.rect.height:
                    break
            self.draw_text(message, "regular", size, "red", (0, 0), "center")
        self.update_screen(screen)
