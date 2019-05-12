import gettext
import logging
from modules.WeatherModule import WeatherModule, Utils


def self_update():
    def exec(cmd):
        p = subprocess.Popen(cmd,
                             cwd=sys.path[0],
                             shell=True,
                             stdout=subprocess.PIPE)
        o, e = p.communicate()
        return str(o.strip(), "utf-8")

    try:
        rid = exec("git ls-remote origin HEAD | cut -f1")
        lid = exec("git log --format='%H' -n 1")
        logging.debug("remote: {} local: {}".format(rid, lid))
        if rid == lid:
            logging.debug("Up to date")
        else:
            exec("git pull")
            logging.info("Updated to new version")
            Utils.restart()

    except Exception as e:
        logging.error(e, exc_info=True)


class SelfUpdate(WeatherModule):
    def __init__(self, fonts, location, language, units, config):
        self.check_interval = 86400  # onece a day
        self.check_interval = config[
            "check_interval"] if "check_interval" in config else 86400  # onece a day

        self.timer_thread = RepeatedTimer(self.check_interval, self_update)
        self.timer_thread.start()
        logging.info("{}: thread started".format(__class__.__name__))

    def quit(self):
        if self.timer_thread:
            logging.info("{}: thread stopped".format(__class__.__name__))
            self.timer_thread.quit()
