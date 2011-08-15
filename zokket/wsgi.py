try:
    from urllib.parse import unquote
except ImportError:
    from urllib import unquote

import socket
import email
from zokket.tcp import TCPSocket


class WSGIRequestHandler(object):
    def __init__(self, server, sock, data):
        self.server = server
        self.version = self.server.request_version
        self.socket = sock

        self.handle_data(data)

    def start_response(self, status, headers):
        self.status = status
        self.response_headers = headers

    def handle_data(self, data):
        lines = data.split("\r\n")[:-2]
        request_line = lines.pop(0)
        request_words = request_line.split()

        if len(request_words) == 3:
            [command, path, version] = request_words

            if version[:5] != 'HTTP/':
                self.send_error('400 BAD REQUEST', 'Bad request version ({})'.format(version))
                return
            self.version = version
        elif len(request_words) == 2:
            [command, path] = request_words
        elif not request_words:
            return
        else:
            self.send_error('400 BAD REQUEST', 'Bad request syntax ({})'.format(request_line))
            return

        self.environ = self.server.base_environ.copy()
        self.headers = email.message_from_string("\r\n".join(lines))
        self.environ['SERVER_PROTOCOL'] = version
        self.environ['REQUEST_METHOD'] = command

        if '?' in path:
            path, query = path.split('?', 1)
        else:
            path, query = path, ''

        self.environ['PATH_INFO'] = unquote(path)
        self.environ['QUERY_STRING'] = query
        self.environ['CONTENT_TYPE'] = self.headers.get('Content-Type', '')
        self.environ['CONTENT_LENGTH'] = self.headers.get('Content-Length', '')

        for key, value in self.headers.items():
            key = ('HTTP_' + key.upper().replace('-', '_'))
            if key not in ('HTTP_CONTENT_TYPE', 'HTTP_CONTENT_LENGTH'):
                self.environ[key] = value

        self.environ['REMOTE_HOST'] = self.socket.connected_host()
        self.environ['REMOTE_ADDR'] = self.socket.connected_host()

        self.handle_request()
        self.send_response()

        self.socket.socket.shutdown(socket.SHUT_WR)

        conntype = self.headers.get('Connection', "")
        if conntype.lower() != 'keep-alive':
            self.socket.close()

    def handle_request(self):
        try:
            self.data = self.server.handler(self.environ, self.start_response)
        except Exception:
            self.status = '500 INTERNAL SERVER ERROR'
            self.response_headers = [('Content-type', 'text/plain')]
            self.data = ['Internal Server Error']

    def send_error(self, error, explain):
        self.status = error
        self.data = explain
        self.response_headers = [('Content-type', 'text/plain')]
        self.send_response()
        self.socket.close()

    def send_response(self):
        self.socket.send("{} {}\r\n".format(self.version, self.status))
        self.socket.send("\r\n".join(['{}: {}'.format(*header) for header in self.response_headers]) + "\r\n\r\n")
        self.socket.send("\n".join(self.data) + "\r\n\r\n")


class WSGIServer(object):
    protocol_version = "HTTP/1.0"
    request_version = "HTTP/0.9"

    def __init__(self, handler, host='', port=8082):
        self.handler = handler

        self.socket = TCPSocket(self)
        self.socket.accept(host, port)

        self.base_environ = {}
        self.base_environ['SERVER_NAME'] = socket.getfqdn(self.socket.local_host())
        self.base_environ['SERVER_PORT'] = str(self.socket.local_port())
        self.base_environ['GATEWAY_INTERFACE'] = 'CGI/1.1'
        self.base_environ['REMOTE_HOST'] = ''
        self.base_environ['CONTENT_LENGTH'] = ''
        self.base_environ['SCRIPT_NAME'] = ''

    def socket_did_connect(self, sock, host, port):
        sock.read_until_data = "\r\n\r\n"

    def socket_read_data(self, sock, data):
        WSGIRequestHandler(self, sock, data)
