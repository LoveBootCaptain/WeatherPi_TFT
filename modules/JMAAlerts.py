import gettext
import logging
from modules.WeatherModule import WeatherModule, Utils
from xml.etree import ElementTree as et


def extra_feed(prefectures):
    """
    気象庁防災情報XMLフォーマット形式電文の公開（PULL型）で公開されているAtomフィードのうち、
    "高頻度フィード/随時"　のフィードを取得し、dataのURLを返す。
    参考：http://xml.kishou.go.jp/xmlpull.html

    :param prefectures: 都道府県名
    """
    try:
        response = requests.get(
            "http://www.data.jma.go.jp/developer/xml/feed/extra.xml")
        response.raise_for_status()

        data = et.fromstring(response.content)
        ns = {"ns": "http://www.w3.org/2005/Atom"}
        for element in root.findall("./ns:entry", ns):
            if element.find("ns:content", ns).text.find(prefectures) > -1:
                if element.find("ns:title", ns).text == "気象特別警報・警報・注意報":
                    return element.find("ns:link", ns).attrib["href"]

    except Exception as e:
        return None


def warning(url, city):
    """
    気象庁防災情報XMLフォーマット形式電文の公開（PULL型）で公開されている"高頻度フィード/随時"
    フィードのデータを取得し、指定した市区町村の情報を返す。

    :param url: Data feed url (extra_feed()の返り値)
    :param city: 市区町村名
    """
    try:
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
        return None


def alert(prefectures, city, title):
    url = extra_feed(prefectures)
    if url:
        return warning(url, city)
    return None


class JMAAlerts(WeatherModule):
    def __init__(self, fonts, location, language, units, config):
        super().__init__(fonts, location, language, units, config)
        self.city, self.prefectures = self.location["address"].split(",")
        self.title = "気象特別警報・警報・注意報"
        self.timer_thread = RepeatedTimer(
            600, alert, [self.prefectures, self.city, self.title])
        logging.info("{}: thread started".format(__class__.__name__))

    def quit(self):
        if self.timer_thread:
            logging.info("{}: thread stopped".format(__class__.__name__))
            self.timer_thread.quit()

    def draw(self, screen, weather, updated):
        if weather is None:
            message = "waiting for weather forecast data ..."
        else:
            if self.timer_thread is None:
                return
            result = self.timer_thread.result()
            if result is None:
                return
            message = ",".join(result)
            logging.debug("{}: {} {} {} {}".format(__class__.__name__,
                                                   self.prefectures, self.city,
                                                   self.title, message))

        self.clear_surface()
        self.draw_text(message, "regular", "small", "red", (0, 0), "center")
        self.update_screen(screen)
