from zokket.tcp import SocketException, TCPSocket
from zokket.udp import UDPSocket
from zokket.timers import Timer
from zokket.runloop import DefaultRunloop, Runloop
from zokket.wsgi import WSGIServer

VERSION = (1, 2, 0)

def get_version():
    version = '{}.{}'.format(VERSION[0], VERSION[1])
    if VERSION[2]:
        version = '{}.{}'.format(version, VERSION[2])
    return version
