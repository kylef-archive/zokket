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

        if not runloop:
            runloop = DefaultRunloop.default()

        self.uploaded_bytes = 0
        self.downloaded_bytes = 0

        self.attach_to_runloop(runloop)

    # Configuration

    def attach_to_runloop(self, runloop):
        self.runloop = runloop
        self.runloop.sockets.append(self)

    # Connecting / Writing

    def bind(self, host='', port=0):
        self.socket.bind((host, port))

    def send(self, host, port, data):
        self.uploaded_bytes += len(data)
        self.socket.sendto(data, (host, port))

    def close(self):
        if self.socket:
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
