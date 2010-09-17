import time

class Timer(object):
    def __init__(self, interval, callback, repeat=False, data=None):
        self.interval = interval
        self.callback = callback
        self.repeat = repeat
        self.data = data
        self.runloop = None
        self.update_timeout()
    
    def update_timeout(self):
        self.fire_at = time.time() + self.interval
    
    def timeout(self):
        return self.fire_at - time.time()
    
    def attach_to_runloop(self, runloop):
        self.runloop = runloop
        self.runloop.timers.append(self)
    
    def fire(self):
        self.callback(self)
    
    def execute(self):
        self.fire()
        
        if self.repeat:
            self.update_timeout()
        else:
            self.invalidate()
    
    def invalidate(self):
        self.runloop.timers.remove(self)
