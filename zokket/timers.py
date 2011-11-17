import time
from zokket.runloop import DefaultRunloop


class Timer(object):
    def __init__(self, interval, callback, repeat=False, data=None, runloop=None):
        self.interval = interval
        self.callback = callback
        self.repeat = repeat
        self.data = data
        self.runloop = None
        self.update_timeout()
        self.runloop = runloop

        self.runloop.register_timer(self)

    @property
    def runloop(self):
        if not self._runloop:
            self._runloop = DefaultRunloop.default()

        return self._runloop

    @runloop.setter
    def runloop(self, runloop):
        self._runloop = runloop

    def update_timeout(self):
        self.fire_at = time.time() + self.interval

    def timeout(self):
        return self.fire_at - time.time()

    def fire(self):
        self.callback(self)

    def execute(self):
        self.fire()

        if self.repeat:
            self.update_timeout()
        else:
            self.invalidate()

    def invalidate(self):
        self.interval = 0
        self.repeat = False
        self.fite_at = None

        self.runloop.unregister_timer(self)
