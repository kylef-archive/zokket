#!/usr/bin/env python2

import zokket


def app(environ, start_response):
    start_response('200 OK', [('Content-type', 'text/plain')])
    return ['Hello World!']

if __name__ == '__main__':
    zokket.WSGIServer(app, 'localhost', 8082)
    zokket.DefaultRunloop.run()
