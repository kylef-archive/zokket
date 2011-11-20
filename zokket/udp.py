import socket

from zokket.runloop import DefaultRunloop


class UDPSocketDelegate(object):
    def udp_socket_read_data(self, sock, host, port, data):
        pass


class UDPSocket(object):
    def __init__(self, delegate=None, runloop=None):
        self.delegate = delegate

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(0)

        self.uploaded_bytes = 0
        self.downloaded_bytes = 0

        self.runloop = runloop
        self.runloop.register_socket(self)

    def __eq__(self, other):
        if self.socket is not None and other == self.fileno():
            return True

        if id(self) == id(other):
            return True

        return False


    @property
    def runloop(self):
        if not self._runloop:
            self._runloop = DefaultRunloop.default()

        return self._runloop

    @runloop.setter
    def runloop(self, runloop):
        self._runloop = runloop

    # Connecting / Writing

    def bind(self, host='', port=0):
        self.socket.bind((host, port))

    def send(self, host, port, data):
        self.uploaded_bytes += len(data)
        self.socket.sendto(data, (host, port))

    def close(self):
        if self.socket:
            self.runloop.unregister_socket(self)

            self.socket.close()
            self.socket = None

    # Diagnostics

    def fileno(self):
        if self.socket != None:
            return self.socket.fileno()
        return -1

    # Runloop Callbacks

    def readable(self):
        return self.socket != None

    def writable(self):
        return False

    def handle_read_event(self):
        data, addr = self.socket.recvfrom(65565)
        self.downloaded_bytes += len(data)

        if hasattr(self.delegate, 'udp_socket_read_data'):
            self.delegate.udp_socket_read_data(self, addr[0], addr[1], data)

    def handle_write_event(self):
        pass

    def handle_except_event(self):
        pass
