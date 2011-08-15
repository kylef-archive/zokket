__all__ = ['SocketException', 'TCPSocketDelegate', 'TCPSocket']

import socket
import os

try:
    import ssl
except ImportError:
    ssl = None

from zokket.timers import Timer
from zokket.runloop import DefaultRunloop

import errno

class SocketException(Exception):
    pass


class TCPSocketDelegate(object):
    """
    An instance of TCPSocket will call methods on its delegate object upon
    completing certain operations or when it encouters errors.

    All instances of TCPSocket should have a delegate that optionally responds
    to these methods. A delegate should be seen as a connection controller.
    """

    def socket_did_disconnect(self, sock, err=None):
        """
        A socket that was previously connected or listening has been closed.

        Additionally an error on connecting could cause this delegate method
        to be called and the exception will be passed.
        """
        pass

    def socket_did_accept_new_socket(self, sock, new_sock):
        """
        An accept socket accepted a new socket.
        """
        pass

    def socket_wants_runloop_for_new_socket(self, sock, new_sock):
        """
        If this method is not implemented then it will use the current runloop.

        This method can be implemented so the socket can run on a seperate
        thread from the accept socket by returning a different runloop
        running on a different thread.
        """
        return RunLoop()

    def socket_will_connect(self, sock):
        """
        The socket calls this method when it is about to connect to a remote
        socket.

        Return True if the socket should continue to connect to the remote
        socket.
        """
        return True

    def socket_connection_refused(self, sock, host, port):
        """
        The connection was refused
        """
        pass

    def socket_did_connect(self, sock, host, port):
        """
        The socket has connected with host and port.
        """
        pass

    def socket_connection_timeout(self, sock, host, port):
        """
        The socket timedout trying to connect to host and port.
        """
        pass

    def socket_read_data(self, sock, data):
        """
        The socket has received data.
        """
        pass

    def socket_address_in_use(self, sock, host, port):
        """
        This method will be called if the address you tried to
        accept on is already in use.
        """
        pass

    def socket_address_refused(self, sock, host, port):
        """
        This method will be called if the address you tried to
        accept on is refused, this usually means you are trying
        to accept on a port <1024 without root priviledges.
        """
        pass

    def socket_accepting(self, sock, host, port):
        """
        This method will be called when a socket is successfully
        listening on the host and port.
        """
        pass

    def socket_did_secure(self, sock):
        """
        This method will be called when TLS negotiation is
        complete, and the rest of the connection will be
        secure. (Unless sock.stop_tls is called).
        """
        pass


class TCPSocket(object):
    def __init__(self, delegate=None, runloop=None):
        """
        The delegate is an object which follows the TCPSocketDelegate protocol.
        """

        self.delegate = delegate
        self.socket = None
        self.connected = False
        self.accepting = False
        self.accepted = False
        self.connect_timeout = None

        self.tls_handshake_stage = None

        self.read_until_data = None
        self.read_until_length = None
        self.read_buffer = ''
        self.buffer_type = 'utf-8'

        self.uploaded_bytes = 0
        self.downloaded_bytes = 0

        if not runloop:
            runloop = DefaultRunloop.default()

        self.attach_to_runloop(runloop)

    def __str__(self):
        if self.connected:
            return '{}:{}'.format(self.connected_host(), self.connected_port())
        elif self.accepting:
            return '{}:{}'.format(self.local_host(), self.local_port())

        return ''

    def __repr__(self):
        if self.connected:
            return '<TCPSocket connect({}:{})>'.format(
                self.connected_host(),
                self.connected_port()
            )
        elif self.accepting:
            return '<TCPSocket listen({}:{})>'.format(
                self.local_host(),
                self.local_port()
            )
        elif self.socket != None:
            return '<TCPSocket connecting>'

        return '<TCPSocket>'

    def __del__(self):
        self.close()

    def __nonzero__(self):
        return (self.socket != None) and self.connected or self.accepting

    # Configuration

    def configure(self):
        self.accepted = True

        if hasattr(self.delegate, 'socket_will_connect'):
            if not self.delegate.socket_will_connect(self):
                self.close()

    def attach_to_runloop(self, runloop):
        self.runloop = runloop
        self.runloop.sockets.append(self)

    # TLS

    def has_tls(self):
        return ssl is not None

    def start_tls(self, keyfile=None, certfile=None, cert_reqs=ssl.CERT_NONE, \
            ca_certs=None, version=ssl.PROTOCOL_SSLv23):
        if not self.has_tls():
            return False

        if self.socket is None:
            return False

        self.socket = ssl.SSLSocket(self.socket, keyfile=keyfile, \
                                    certfile=certfile, cert_reqs=cert_reqs, \
                                    ca_certs=ca_certs, ssl_version=version, \
                                    server_side=self.accepted, \
                                    do_handshake_on_connect=False)
        self.tls_handshake()

        return True

    def stop_tls(self):
        if not self.has_tls():
            return

        self.socket = self.socket.unwrap()

    def tls_cipher(self):
        if not self.has_tls():
            return

        if isinstance(self.socket, ssl.SSLSocket):
            return self.socket.cipher()

    def tls_peer_certificate(self, binary_form=False):
        if not self.has_tls():
            return

        if isinstance(self.socket, ssl.SSLSocket):
            return self.socket.getpeercert(binary_form)

    # Connecting

    def connect(self, host, port, timeout=None):
        """
        Try to establish a connection with host and port.

        If a timeout is defined, after this timeout has been reached the
        TCPSocket will stop trying to connect and the socket_connection_timeout
        TCPSocketDelegate method will be called.

        If the socket establishes the connection before the timeout
        socket_did_connect TCPSocketDelegate method will be called.
        """

        if not self.delegate:
            raise SocketException("Attempting to accept without a delegate. Set a delegate first.")

        if self.socket != None:
            raise SocketException("Attempting to accept while connected or accepting connections. Disconnect first.")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(0)
        self.connecting_address = (host, port)

        try:
            self.socket.connect((host, port))
        except socket.error as e:
            if e.errno in (errno.EINPROGRESS, errno.EALREADY, errno.EWOULDBLOCK):
                if timeout:
                    self.connect_timeout = Timer(timeout, self.connection_timeout, False, (host, port), runloop=self.runloop)
                return
            return self.close(e)

        self.did_connect()

    def connection_timeout(self, timer):
        self.close()

        if hasattr(self.delegate, 'socket_connection_timeout'):
            self.delegate.socket_connection_timeout(self, *timer.data)

    def did_connect(self):
        self.connected = True

        if self.connect_timeout:
            self.connect_timeout.invalidate()

        # Lets make sure that this connection wasn't refused.

        try:
            self.socket.recv(0)
        except socket.error as e:
            if e.errno == errno.ECONNREFUSED:
                if hasattr(self.delegate, 'socket_connection_refused'):
                    self.delegate.socket_connection_refused(self, self.connecting_address[0], self.connecting_address[1])

                self.close()
                return

        if hasattr(self.delegate, 'socket_did_connect'):
            self.delegate.socket_did_connect(self, self.connected_host(), self.connected_port())

    def accept(self, host='', port=0):
        if not self.delegate:
            raise SocketException("Attempting to accept without a delegate. Set a delegate first.")

        if self.socket != None:
            raise SocketException("Attempting to accept while connected or accepting connections. Disconnect first.")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(0)

        try:
            self.socket.bind((host, port))
        except socket.error as e:
            if e.errno == errno.EADDRINUSE:
                self.close()

                if hasattr(self.delegate, 'socket_address_in_use'):
                    self.delegate.socket_address_in_use(self, host, port)

                return
            elif e.errno == errno.EACCES:
                self.close()

                if hasattr(self.delegate, 'socket_address_refused'):
                    self.delegate.socket_address_refused(self, host, port)

                return
            raise e

        self.socket.listen(5)
        self.accepting = True

        if hasattr(self.delegate, 'socket_accepting'):
            self.delegate.socket_accepting(self, host, port)

    def accept_from_socket(self):
        client, address = self.socket.accept()

        new_sock = self.__class__(self.delegate)
        new_sock.socket = client
        new_sock.socket.setblocking(0)

        if hasattr(self.delegate, 'socket_did_accept_new_socket'):
            self.delegate.socket_did_accept_new_socket(self, new_sock)

        if hasattr(self.delegate, 'socket_wants_runloop_for_new_socket'):
            new_sock.attach_to_runloop(self.delegate.socket_wants_runloop_for_new_socket(self, new_sock))
        else:
            new_sock.attach_to_runloop(self.runloop)

        new_sock.configure()

    def tls_handshake(self):
        if not self.has_tls():
            return

        try:
            self.socket.do_handshake()
            self.tls_handshake_stage = None

            if hasattr(self.delegate, 'socket_did_secure'):
                self.delegate.socket_did_secure(self)
        except ssl.SSLError as err:
            if err.args[0] == ssl.SSL_ERROR_WANT_READ:
                self.tls_handshake_stage = 1
            elif err.args[0] == ssl.SSL_ERROR_WANT_WRITE:
                self.tls_handshake_stage = 2
            else:
                raise

    # Disconnect

    def close(self, err=None):
        """
        Disconnect or stop accepting.
        """

        if (self.connected or self.accepted or self.accepting or err) and \
                hasattr(self.delegate, 'socket_did_disconnect'):
            self.delegate.socket_did_disconnect(self, err)

        if self.socket != None:
            if isinstance(self.socket, ssl.SSLSocket):
                self.stop_tls()

            self.socket.close()
            self.socket = None

        self.connected = False
        self.accepting = False

    # Reading

    def read_data(self, data):
        if hasattr(self.delegate, 'socket_read_data'):
            self.delegate.socket_read_data(self, data)

    def dequeue_buffer(self):
        if self.read_until_data != None:
            index = self.read_buffer.find(self.read_until_data)

            if index != -1:
                read_until_data_length = len(self.read_until_data)
                data = self.read_buffer[:index + read_until_data_length]
                self.read_buffer = self.read_buffer[index + read_until_data_length:]

                self.read_data(data)
                self.dequeue_buffer()
        elif self.read_until_length != None:
            if len(self.read_buffer) >= self.read_until_length:
                data = self.read_buffer[:self.read_until_length]
                self.read_buffer = self.read_buffer[self.read_until_length:]

                self.read_data(data)
                self.dequeue_buffer()
        else:
            self.read_data(self.read_buffer)
            self.read_buffer = ''

    def bytes_availible(self):
        if self.socket == None:
            return

        try:
            if isinstance(self.socket, ssl.SSLSocket):
                data = self.socket.read(8192)
            else:
                data = self.socket.recv(8192)

            if not data:
                self.close()
                return

            if isinstance(data, bytes):
                self.read_buffer += data.decode(self.buffer_type)
            else:
                self.read_buffer += data

            self.downloaded_bytes += len(data)
            self.dequeue_buffer()
        except socket.error as e:
            if e.errno in (errno.ECONNRESET, errno.ENOTCONN):
                self.close()

    # Writing

    def send(self, data):
        if self.tls_handshake_stage is not None:
            return

        self.uploaded_bytes += len(data)

        if not isinstance(data, bytes):
            data = data.encode(self.buffer_type)

        try:
            if isinstance(self.socket, ssl.SSLSocket):
                return self.socket.write(data)
            return self.socket.send(data)
        except socket.error as e:
            if e.errno == errno.EWOULDBLOCK:
                return 0
            raise e

    # Diagnostics

    def fileno(self):
        if self.socket != None:
            return self.socket.fileno()
        return -1

    def connected_host(self):
        if self.socket == None:
            return ''

        try:
            return self.socket.getpeername()[0]
        except socket.error:
            return ''

    def connected_port(self):
        if self.socket == None:
            return 0

        try:
            return self.socket.getpeername()[1]
        except socket.error as e:
            return -1

    def local_host(self):
        if self.socket == None:
            return ''

        try:
            return self.socket.getsockname()[0]
        except socket.error:
            return ''

    def local_port(self):
        if self.socket == None:
            return 0

        try:
            return self.socket.getsockname()[1]
        except socket.error:
            return 0

    # Runloop Callbacks

    def readable(self):
        return self.socket != None

    def writable(self):
        if self.socket != None:
            if self.tls_handshake_stage == 2:
                return True
            if not self.accepting:
                return not self.connected
        return False

    def handle_read_event(self):
        if self.socket == None:
            return

        if self.tls_handshake_stage is not None:
            self.tls_handshake()
        elif self.accepting:
            self.accept_from_socket()
        elif not self.connected:
            self.did_connect()
            self.bytes_availible()
        else:
            self.bytes_availible()

    def handle_write_event(self):
        if self.socket == None:
            return

        if self.tls_handshake_stage is not None:
            self.tls_handshake()
        elif not self.connected and not self.accepting:
            self.did_connect()

    def handle_except_event(self):
        pass
