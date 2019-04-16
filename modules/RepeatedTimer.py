import sys
import threading


class RepeatedTimer(threading.Timer):
    def __init__(self, interval, function, args=[], kwargs={}):
        super().__init__(interval, self.run, args, kwargs)
        self.thread = None
        self.function = function
        self._return = None

    def run(self):
        self.thread = threading.Timer(self.interval, self.run)
        self.thread.start()
        self._return = self.function(*self.args, **self.kwargs)

    def result(self):
        return self._return

    def quit(self):
        if self.thread is not None:
            self.thread.cancel()
            self.thread.join()
            del self.thread
