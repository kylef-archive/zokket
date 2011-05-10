import zokket

class TLSDelegate(object):
    def __init__(self):
        zokket.TCPSocket(self).accept(port=5000)

    # Socket delegate methods

    def socket_did_disconnect(self, sock, err=None):
        print "Socket: Disconnected (%s)" % err

    def socket_will_connect(self, sock):
        # Start TLS using mycert.pem as our certificate.
        sock.start_tls(certfile='mycert.pem')
        return True

    def socket_did_secure(self, sock):
        print "Socket is now secure"

    def socket_read_data(self, sock, data):
        print "[%s] %s" % (sock, data.strip())

if __name__ == '__main__':
    print "Note: This example requires a SSL certificate to be generated, the example uses mycert.pem"
    TLSDelegate()
    zokket.DefaultRunloop.run()
