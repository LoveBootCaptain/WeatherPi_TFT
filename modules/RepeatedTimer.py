import hashlib
import logging
import threading


class RepeatedTimer(threading.Timer):
    def __init__(self, interval, function, args=[], kwargs={}):
        super().__init__(interval, self.run, args, kwargs)
        self.thread = None
        self.function = function
        self._return = None
        self._hash = None
        logging.info("{} thread created. interval: {}".format(
            self.function.__name__, self.interval))

    def run(self):
        self.thread = threading.Timer(self.interval, self.run)
        self.thread.start()
        self._return = self.function(*self.args, **self.kwargs)
        self._hash = hashlib.md5(str(self._return).encode()).hexdigest()

    def get_result(self):
        return self._return

    def get_hash_value(self):
        return self._hash

    def quit(self):
        if self.thread is not None:
            logging.info("{} thread stopped".format(self.function.__name__))
            self.thread.cancel()
            self.thread.join()
            del self.thread
