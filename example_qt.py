import sys

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtWebKit

from zokket.qt import QtRunloop
import zokket

class Window(QtGui.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        self.setWindowTitle('zokket - PyQT Example')

        self.editor = QtGui.QTextEdit()
        self.editor.setReadOnly(True)
        self.setCentralWidget(self.editor)
        self.resize(500, 300)

        self.show()

        # Lets connect to duckduckgo.com
        zokket.TCPSocket(self).connect(host='duckduckgo.com', port=443, timeout=15)
        self.editor.append("Connecting to duckduckgo.com...")

    # Socket delegate methods

    def socket_connection_timeout(self, sock, host, port):
        self.editor.append("Connection to %s:%s timed out." % (host, port))

    def socket_did_connect(self, sock, host, port):
        sock.read_until_data = "\r\n"
        sock.start_tls()  # Start TLS

    def socket_did_secure(self, sock):
        self.editor.append("Connected using {}, version {}, {}-bit.\r\n".format(*sock.tls_cipher()))

        sock.send("HEAD / HTTP/1.0\r\n")
        sock.send("Host: duckduckgo.com\r\n")
        sock.send("\r\n")

    def socket_read_data(self, sock, data):
        self.editor.append("> " + data.strip())

    def socket_did_disconnect(self, sock, err=None):
        self.editor.append("\r\nDisconnected")

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)

    # Tell zokket to use the QtRunloop
    QtRunloop.set_default(app)

    # Start our window
    Window()

    sys.exit(app.exec_())
