# -*- coding: utf-8 -*-

from tornado import ioloop

from torpc import TcpClient


class MyTcpClient(TcpClient):
    def on_connected(self):
        self.write('hello')

    def on_receive(self, buf):
        print('receive: {0}'.format(buf))
        self.close()

    def on_close(self):
        print('on_close')
        io_loop.stop()


if __name__ == '__main__':
    client = MyTcpClient(('127.0.0.1', 5000))
    client.start()

    io_loop = ioloop.IOLoop.instance()

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
        print "exited cleanly"
