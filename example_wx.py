#!/usr/bin/env python2
# An example of wx and zokket, a simple echo server

import zokket
import wx


class EchoServerFrame(wx.Frame):
    def __init__(self):
        super(EchoServerFrame, self).__init__(None, -1, 'EchoServer')
        self.text = wx.TextCtrl(self, -1, '', style=wx.TE_MULTILINE)

        # Lets listen on port 5000
        zokket.TCPSocket(self).accept(port=5000)

    def append_to_textbox(self, line):
        # We must update the textbox on the main thread, so lets use wx.CallAfter
        wx.CallAfter(self.text.AppendText, line + "\n")

    # Socket delegate methods

    def socket_accepting(self, sock, host, port):
        self.append_to_textbox("*** Listening on (%s)" % port)

    def socket_address_in_use(self, sock, host, port):
        self.append_to_textbox("*** Address in use (%s)" % port)

    def socket_address_refused(self, sock, host, port):
        self.append_to_textbox("*** Address refused (%s)" % port)

    def socket_did_connect(self, sock, host, port):
        self.append_to_textbox("*** Connected (%s:%s)" % (host, port))

    def socket_did_disconnect(self, sock, err=None):
        self.append_to_textbox("*** Disconnected")

    def socket_read_data(self, sock, data):
        self.append_to_textbox("[%s] %s" % (sock, data.strip()))
        sock.send(data)  # Echo data back

if __name__ == '__main__':
    app = wx.PySimpleApp()
    app.TopWindow = EchoServerFrame()
    app.TopWindow.Show()
    zokket.DefaultRunloop.run_in_new_thread()  # Run the zokket runloop (in a new thread)
    app.MainLoop()
    zokket.DefaultRunloop.abort()  # End the zokket runloop as the mainloop has exited
