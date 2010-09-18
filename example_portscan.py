import zokket

PRIVILEGED_PORTRANGE = range(1, 1024)
REGISTERED_PORTRANGE = range(1024, 49151)

class PortScanner(object):
    def __init__(self, target, portrange=PRIVILEGED_PORTRANGE, simultaneous_connections=100, timeout=0.05):
        self.portrange = portrange
        self.target = target
        self.timeout = timeout
        
        self.runloop = zokket.RunLoop()
        [self.connect() for connection in range(0, simultaneous_connections)]
        self.runloop.run()
    
    def connect(self):
        if len(self.portrange) == 0:
            self.runloop.running = False
            return
        
        s = zokket.TCPSocket(self)
        s.attach_to_runloop(self.runloop)
        s.connect(self.target, self.portrange.pop(0), timeout=self.timeout)
    
    def socket_did_connect(self, sock, host, port):
        print "Port %s Open." % (port)
        self.connect()
        sock.close()
    
    def socket_connection_refused(self, sock, host, port):
        print "Port %s Closed" % (port)
        self.connect()
    
    def socket_connection_timeout(self, sock, host, port):
        self.connect()

if __name__ == '__main__':
    PortScanner('127.0.0.1')
    print "Portscan ended"
