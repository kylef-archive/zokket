from zokket.tcp import SocketException, TCPSocket
from zokket.udp import UDPSocket
from zokket.timers import Timer
from zokket.runloop import DefaultRunloop, Runloop
from zokket.wsgi import WSGIServer

VERSION = (1, 2, 1)

def get_version():
    return '{}.{}.{}'.format(VERSION[0], VERSION[1], VERSION[2])

