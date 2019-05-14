import logging
import subprocess
import sys
from modules.WeatherModule import WeatherModule, Utils
from modules.RepeatedTimer import RepeatedTimer


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
        logging.info("remote: {} local: {}".format(rid, lid))
        if rid == lid:
            logging.debug("Up to date")
        else:
            exec("sudo -u pi git pull")
            logging.info("Updated to new version")
            Utils.restart()

    except Exception as e:
        logging.error(e, exc_info=True)


class SelfUpdate(WeatherModule):
    """
    Self update module

    This module detects git updates and updates itself.

    example config:
    {
      "module": "SelfUpdate",
      "config": {
        "check_interval": 86400
      }
    }
    """

    def __init__(self, fonts, location, language, units, config):
        self.check_interval = None
        if isinstance(config["check_interval"], int):
            self.check_interval = config["check_interval"]
        if self.check_interval is None:
            raise ValueError(__class__.__name__)

        self.timer_thread = RepeatedTimer(self.check_interval, self_update)
        self.timer_thread.start()

    def quit(self):
        if self.timer_thread:
            self.timer_thread.quit()
