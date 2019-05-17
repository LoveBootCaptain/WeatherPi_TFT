# pylint: disable=invalid-name
"""RepeatedTimer class
"""

import hashlib
import logging
import threading


class RepeatedTimer(threading.Timer):
    """Thread that executes every N seconds
    """

    def __init__(self, interval, function, args=None, kwargs=None):
        super().__init__(interval, self.run, args, kwargs)
        self.thread = None
        self.function = function
        self._return = None
        self._hash_value = None
        logging.info("%s thread created. interval: %s", self.function.__name__,
                     self.interval)

    def run(self):
        """start thread
        """
        self.thread = threading.Timer(self.interval, self.run)
        self.thread.start()
        self._return = self.function(*self.args, **self.kwargs)
        self._hash_value = hashlib.md5(str(self._return).encode()).hexdigest()

    def get_result(self):
        """get return value
        """
        return self._return

    def get_hash_value(self):
        """get hash value of return
        """
        return self._hash_value

    def quit(self):
        """stop this therad
        """
        if self.thread is not None:
            logging.info("%s thread stopped", self.function.__name__)
            self.thread.cancel()
            self.thread.join()
            del self.thread
