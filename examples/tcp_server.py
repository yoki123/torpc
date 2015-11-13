# -*- coding: utf-8 -*-

import logging
import sys

sys.path.append('../')

from tornado import ioloop

from torpc import TcpServer, Connection
from example_utils import log_initialize

logger = logging.getLogger(__name__)


class EchoServer(TcpServer):
    def handle_stream(self, conn, buf):
        logger.info('received: %s' % buf)
        conn.write(buf)


if __name__ == '__main__':
    log_initialize()

    server = EchoServer(('127.0.0.1', 5000), Connection)
    server.start()

    io_loop = ioloop.IOLoop.instance()
    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
        print "exited cleanly"
