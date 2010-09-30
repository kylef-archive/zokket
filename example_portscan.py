import zokket

PRIVILEGED_PORTRANGE = range(1, 1024)
REGISTERED_PORTRANGE = range(1024, 49151)

class PortScanner(object):
    def __init__(self, target, portrange=PRIVILEGED_PORTRANGE, simultaneous_connections=100, timeout=0.5):
        self.portrange = portrange
        self.target = target
        self.timeout = timeout
        
        [self.connect() for connection in range(0, simultaneous_connections)]
    
    def connect(self):
        if len(self.portrange) == 0:
            zokket.DefaultRunloop.abort()
            return
        
        s = zokket.TCPSocket(self)
        s.connect(self.target, self.portrange.pop(0), timeout=self.timeout)
    
    def socket_did_connect(self, sock, host, port):
        print "Port %s Open." % (port)
        sock.close()
        self.connect()
    
    def socket_connection_refused(self, sock, host, port):
        print "Port %s Closed" % (port)
        self.connect()
    
    def socket_connection_timeout(self, sock, host, port):
        self.connect()

if __name__ == '__main__':
    PortScanner('127.0.0.1')
    zokket.DefaultRunloop.run()
    print "Portscan ended"
