# -*- coding: utf-8 -*-

from tornado import ioloop

from torpc import TcpServer, Connection


class EchoServer(TcpServer):
    def handle_stream(self, conn, buf):
        conn.write(buf)


if __name__ == '__main__':
    server = EchoServer(('127.0.0.1', 5000), Connection)
    server.start()

    io_loop = ioloop.IOLoop.instance()
    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
        print "exited cleanly"
