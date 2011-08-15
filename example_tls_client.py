#!/usr/bin/env python2

import sys
import zokket


class TLSDelegate(object):
    def __init__(self):
        # Lets connect to duckduckgo.com
        zokket.TCPSocket(self).connect(host='duckduckgo.com', port=443)

    # Socket delegate methods

    def socket_did_connect(self, sock, host, port):
        sock.start_tls()  # Start TLS

    def socket_did_secure(self, sock):
        print("Connected using {}, version {}, {}-bit.".format(*sock.tls_cipher()))

        sock.send("HEAD / HTTP/1.0\r\n")
        sock.send("Host: duckduckgo.com\r\n")
        sock.send("\r\n")

    def socket_read_data(self, sock, data):
        print(data.strip())

    def socket_did_disconnect(self, sock, err=None):
        sys.exit()

if __name__ == '__main__':
    TLSDelegate()
    zokket.DefaultRunloop.run()
