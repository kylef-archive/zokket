from PyQt4.QtCore import QObject, QSocketNotifier, SIGNAL, QBasicTimer
from zokket.runloop import DefaultRunloop


class QtRunloop(QObject):
    @classmethod
    def set_default(cls, app=None):
        DefaultRunloop.set(cls)

        if app:
            DefaultRunloop.default().set_application(app)

    def __init__(self):
        super(QtRunloop, self).__init__()
        self.sockets = []
        self.timers = []

    def set_application(self, app):
        self.connect(app, SIGNAL('aboutToQuit()'), self.shutdown)

    def shutdown(self):
        [s.close() for s in self.sockets]

    # timers

    def register_timer(self, timer):
        self.timers.append(timer)

        timer.qtimer = QBasicTimer()
        timer.qtimer.start(timer.interval * 1000, self)

    def unregister_timer(self, timer):
        if hasattr(timer, 'qtimer') and timer.qtimer:
            timer.qtimer.stop()
            timer.qtimer = None

        self.timers.remove(timer)

    def timerEvent(self, event):
        for timer in self.timers:
            if timer.qtimer.timerId() == event.timerId():
                return timer.execute()

    # sockets

    def register_socket(self, socket):
        if socket not in self.sockets:
            self.sockets.append(socket)

        socket.read_notifier = QSocketNotifier(socket.fileno(), QSocketNotifier.Read)
        self.connect(socket.read_notifier, SIGNAL("activated(int)"), self.read_socket)
        socket.read_notifier.setEnabled(socket.readable())

        socket.write_notifier = QSocketNotifier(socket.fileno(), QSocketNotifier.Write)
        self.connect(socket.write_notifier, SIGNAL("activated(int)"), self.write_socket)
        socket.write_notifier.setEnabled(socket.writable())

        #socket.except_notifier = QSocketNotifier(socket.fileno(), QSocketNotifier.Exception)
        #self.connect(socket.except_notifier, SIGNAL("activated(int)"), self.except_event)
        #socket.except_notifier.setEnabled(True)

    def unregister_socket(self, socket):
        if hasattr(self.sockets, 'read_notifier') and self.sockets.read_notifier:
            self.sockets.read_notifier.setEnabled(False)
            self.sockets.read_notifier = None

        if hasattr(self.sockets, 'write_notifier') and self.sockets.write_notifier:
            self.sockets.write_notifier.setEnabled(False)
            self.sockets.write_notifier = None

        if hasattr(self.sockets, 'except_notifier') and self.sockets.except_notifier:
            self.sockets.except_notifier.setEnabled(False)
            self.sockets.except_notifier = None

        self.sockets.remove(socket)

    def update_socket(self, socket):
        if hasattr(socket, 'read_notifier') and socket.read_notifier:
            socket.read_notifier.setEnabled(socket.readable())

        if hasattr(socket, 'write_notifier') and socket.write_notifier:
            socket.write_notifier.setEnabled(socket.writable())

        #if hasattr(socket, 'except_notifier') and socket.except_notifier:
        #    socket.except_notifier.setEnabled(True)

    def read_socket(self, fd):
        for socket in self.sockets:
            if socket.fileno() == fd:
                socket.handle_read_event()
                return

    def write_socket(self, fd):
        for socket in self.sockets:
            if socket.fileno() == fd:
                socket.handle_write_event()
                return

    def except_event(self, fd):
        for socket in self.sockets:
            if socket.fileno() == fd:
                socket.handle_except_event()
                return

