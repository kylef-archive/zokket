import select

class RunLoop(object):
    def __init__(self):
        self.sockets = []
        self.timers = []
        self.running = False
    
    def timeout(self):
        try:
            runtimes = [timer.timeout() for timer in self.timers]
            runtimes.sort()
            return runtimes.pop(0)
        except:
            return 180
    
    def run(self):
        self.running = True
        
        try:
            while self.running:
                poll(self.sockets, self.timeout())
                [timer.execute() for timer in self.timers if timer.timeout() <= 0.0]
        except KeyboardInterrupt:
            self.running = False
        
        [s.close() for s in self.sockets if s.socket]

def poll(sockets, timeout=30):
    r = filter(lambda x: x.readable(), sockets)
    w = filter(lambda x: x.writable(), sockets)
    e = filter(lambda x: x.socket != None, sockets)
    
    (rlist, wlist, xlist) = select.select(r, w, e, timeout)
    
    for s in xlist:
        s.handle_except_event()
    
    for s in rlist:
        s.handle_read_event()
    
    for s in wlist:
        s.handle_write_event()
