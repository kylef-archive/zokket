import select
import threading

class DefaultRunloop(object):
    @classmethod
    def set(cls, rl):
        cls._runloop = rl()

    @classmethod
    def run_in_new_thread(cls):
        return threading.Thread(target=cls.default().run, args=(), kwargs={}).start()

    @classmethod
    def run(cls):
        return cls.default().run()

    @classmethod
    def default(cls):
        if not hasattr(cls, '_runloop'):
            cls.set(SelectRunloop)
        return cls._runloop

    @classmethod
    def abort(cls):
        cls.default().running = False

class BaseRunloop(object):
    @classmethod
    def set_default(cls):
        DefaultRunloop.set(cls)

    def run(self):
        raise NotImplemented

    def register_socket(self, socket):
        return

    def unregister_socket(self, socket):
        return

    def update_socket(self, socket):
        """
        This is called when the state of a socket changes, when
        socket.writable/readable may of changed.
        """
        return

class TimerRunloopMixin(object):
    def __init__(self):
        self.timers = []

    def register_timer(self, timer):
        if timer not in self.timers:
            self.timers.append(timer)

    def unregister_timer(self, timer):
        if timer in self.timers:
            self.timers.remove(timer)

    def run_timers(self):
        [timer.execute() for timer in self.timers if timer.timeout() <= 0.0]

    def timer_timeout(self):
        try:
            runtimes = [timer.timeout() for timer in self.timers]
            runtimes.sort()
            timeout = runtimes.pop(0)
            if timeout < 0.0:
                return 0
            return timeout
        except:
            return 180

class Runloop(BaseRunloop, TimerRunloopMixin):
    def __init__(self):
        super(Runloop, self).__init__()
        self.sockets = []
        self.running = False

    def run(self):
        self.running = True

        try:
            while self.running:
                self.run_network()
                self.run_timers()
        except (KeyboardInterrupt, SystemExit):
            self.running = False

        self.shutdown()

        while len(self.sockets):
            self.run_network()

    def run_network(self):
        raise NotImplemented

    def shutdown(self):
        [s.close() for s in self.sockets]

    def register_socket(self, socket):
        if socket not in self.sockets:
            self.sockets.append(socket)

    def unregister_socket(self, socket):
        if socket in self.sockets:
            self.sockets.remove(socket)

class SelectRunloop(Runloop):
    def run_network(self):
        r = filter(lambda x: x.readable(), self.sockets)
        w = filter(lambda x: x.writable(), self.sockets)
        e = filter(lambda x: x.socket != None, self.sockets)

        (rlist, wlist, xlist) = select.select(r, w, e, self.timer_timeout())

        [s.handle_except_event() for s in xlist]
        [s.handle_read_event() for s in rlist]
        [s.handle_write_event() for s in wlist]


class PollRunloop(Runloop):
    def __init__(self):
        super(PollRunloop, self).__init__()
        self.poll = select.poll()

    def socket_for_fd(self, fd):
        for socket in self.sockets:
            if socket == fd:
                return socket

    def run_network(self):
        for fd, flag in self.poll.poll():
            socket = self.socket_for_fd(fd)
            if socket is None:
                continue

            if flag & (select.POLLIN | select.POLLPRI):
                socket.handle_read_event()
            elif flag & select.POLLOUT:
                socket.handle_write_event()
            elif flag & select.POLLERR:
                socket.handle_except_event()

    def eventmask(self, socket):
        mask = select.POLLERR | select.POLLHUP | select.POLLPRI

        if socket.writable():
            mask = select.POLLOUT | mask

        if socket.readable():
            mask = select.POLLIN | mask

        return mask

    def register_socket(self, socket):
        super(PollRunloop, self).register_socket(socket)
        self.poll.register(socket, self.eventmask(socket))

    def update_socket(self, socket):
        super(PollRunloop, self).update_socket(socket)
        self.poll.modify(socket, self.eventmask(socket))

    def unregister_socket(self, socket):
        super(PollRunloop, self).unregister_socket(socket)
        self.poll.unregister(socket)
