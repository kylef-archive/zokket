import select

try:
    from thread import start_new_thread
except ImportError:
    import threading

    def start_new_thread(self, callback, args, kwargs):
        threading.Thread(target=callback, args=args, kwargs=kwargs).start()

class DefaultRunloop(object):
    @classmethod
    def set(cls, rl):
        cls._runloop = rl()

    @classmethod
    def run_in_new_thread(cls):
        return start_new_thread(cls.default().run, (), {})

    @classmethod
    def run(cls):
        return cls.default().run()

    @classmethod
    def default(cls):
        if not hasattr(cls, '_runloop'):
            cls.set(Runloop)
        return cls._runloop

    @classmethod
    def abort(cls):
        cls.default().running = False


class Runloop(object):
    def __init__(self):
        self.sockets = []
        self.timers = []
        self.running = False

    def timeout(self):
        try:
            runtimes = [timer.timeout() for timer in self.timers]
            runtimes.sort()
            timeout = runtimes.pop(0)
            if timeout < 0.0:
                return 0
            return timeout
        except:
            return 180

    def run(self):
        self.running = True

        try:
            while self.running:
                self.run_network()
                self.run_timers()
        except KeyboardInterrupt:
            self.running = False

        self.shutdown()

    def run_network(self):
        r = filter(lambda x: x.readable(), self.sockets)
        w = filter(lambda x: x.writable(), self.sockets)
        e = filter(lambda x: x.socket != None, self.sockets)

        (rlist, wlist, xlist) = select.select(r, w, e, self.timeout())

        [s.handle_except_event() for s in xlist]
        [s.handle_read_event() for s in rlist]
        [s.handle_write_event() for s in wlist]

    def run_timers(self):
        [timer.execute() for timer in self.timers if timer.timeout() <= 0.0]

    def shutdown(self):
        [s.close() for s in self.sockets]
