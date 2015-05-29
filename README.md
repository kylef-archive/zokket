# zokket

[![Build Status](http://img.shields.io/travis/kylef/zokket/master.svg?style=flat)](https://travis-ci.org/kylef/zokket)

zokket is an easy-to-use asynchronous socket networking library for Python
supporting both UDP, TCP sockets along with timers using a delegate interface.

## Installation

```shell
$ pip install zokket
```

## Usage

### Run Loops

The run loop processes and manages sockets and timers. By default a run loop is
created in the background and you can run a run loop as follows:

```python
zokket.DefaultRunloop.run()
```

There are three runloops that you can choose from:

- `SelectRunloop` (Default) - Runloop that makes use of the `select()` system
  call and is available on all platforms. `SelectRunloop` is `O(highest file
  descriptor)`.
- `PollRunloop` - A run loop that uses `poll()` system call, which is not
  available on all platforms. `PollRunloop()` is `O(number of file descriptors)`.
- `QtRunloop` - Provides integration for using Zokket with PyQt4.

To switch the default, you can call the `set_default()` method on a run loop.
For example:

```python
PollRunloop.set_default()
```

You may also configure sockets and timers to use a specific run loop instance.

### TCP Socket

A TCP Socket can be initialised with a delegate and an optional runloop, by
default the default runloop will be used.

```python
from zokket import TCPSocket, DefaultRunloop

class Delegate(object):
    def socket_did_connect(self, sock, host, port):
        print('New connection from {}:{}'.format(host, port))
        sock.send('Hey!\n')

    def socket_read_data(self, sock, data):
        print('Received: {}'.format(data))

TCPSocket(Delegate()).accept(port=5000)
DefaultRunloop.run()
```

You can consult the source code for the full delegate method list.

### UDP Socket

The UDP socket works in a similar way to the TCP socket, refer to the source
code for documentation.

