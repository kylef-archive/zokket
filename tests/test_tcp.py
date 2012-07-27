import unittest

from zokket.tcp import TCPSocket


class TCPTest(unittest.TestCase):
    def test_read_until_data(self):
        s = TCPSocket()
        s.read_until_data = b'\r\n'
        s.read_buffer = b'test\r\nanother line\r\nyet another'

        read_buffer = s.dequeue_buffer()
        self.assertEqual(next(read_buffer), b'test\r\n')
        self.assertEqual(next(read_buffer), b'another line\r\n')
        self.assertRaises(StopIteration, next, read_buffer)

        s.read_buffer += b' line\r\n'
        read_buffer = s.dequeue_buffer()
        self.assertEqual(next(read_buffer), b'yet another line\r\n')
        self.assertRaises(StopIteration, next, read_buffer)

    def test_read_until_length(self):
        s = TCPSocket()
        s.read_until_length = 2
        s.read_buffer = b'12345'

        read_buffer = s.dequeue_buffer()
        self.assertEqual(next(read_buffer), b'12')
        self.assertEqual(next(read_buffer), b'34')
        self.assertRaises(StopIteration, next, read_buffer)

        s.read_buffer += b'6'
        read_buffer = s.dequeue_buffer()
        self.assertEqual(next(read_buffer), b'56')
        self.assertRaises(StopIteration, next, read_buffer)

    def test_normal_buffer(self):
        s = TCPSocket()
        s.read_buffer = b'blob'

        read_buffer = s.dequeue_buffer()
        self.assertEqual(next(read_buffer), b'blob')
        self.assertRaises(StopIteration, next, read_buffer)

        s.read_buffer += b'more'
        read_buffer = s.dequeue_buffer()
        self.assertEqual(next(read_buffer), b'more')
        self.assertRaises(StopIteration, next, read_buffer)

