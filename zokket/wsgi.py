import urllib
import mimetools
import StringIO
import socket

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
                self.send_error('400 BAD REQUEST', 'Bad request version (%s)' % version)
                return
            self.version = version
        elif len(request_words) == 2:
            [command, path] = request_words
        elif not request_words:
            return
        else:
            self.send_error('400 BAD REQUEST', 'Bad request syntax (%s)' % request_line)
            return

        self.environ = self.server.base_environ.copy()
        self.headers = mimetools.Message(StringIO.StringIO("\r\n".join(lines)), 0)
        self.environ['SERVER_PROTOCOL'] = version
        self.environ['REQUEST_METHOD'] = command

        if '?' in path:
            path, query = path.split('?', 1)
        else:
            path, query = path, ''

        self.environ['PATH_INFO'] = urllib.unquote(path)
        self.environ['QUERY_STRING'] = query

        if self.headers.typeheader is None:
            self.environ['CONTENT_TYPE'] = self.headers.type
        else:
            self.environ['CONTENT_TYPE'] = self.headers.typeheader

        length = self.headers.getheader('content-length')
        if length:
            self.environ['CONTENT_LENGTH'] = length

        for h in self.headers.headers:
            k, v = h.split(':', 1)
            k = k.replace('-', '_').upper()
            v = v.strip()
            if k in self.environ:
                continue  # skip content length, type,etc.
            if 'HTTP_' + k in self.environ:
                # comma-separate multiple headers
                self.environ['HTTP_' + k] += ',' + v
            else:
                self.environ['HTTP_' + k] = v

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
        self.socket.send("%s %s\r\n" % (self.version, self.status))
        self.socket.send("\r\n".join(['%s: %s' % header for header in self.response_headers]) + "\r\n\r\n")
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
