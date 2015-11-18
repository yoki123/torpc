# -*- coding: utf-8 -*-

import logging
import sys

sys.path.append('../')

from tornado import ioloop

from example_utils import log_initialize
from torpc import TcpClient

logger = logging.getLogger(__name__)


class MyTcpClient(TcpClient):
    def on_connected(self):
        self.write('hello')

    def on_receive(self, buf):
        logger.info('received: %s' % buf)
        self.close()

    def on_close(self):
        logger.debug('on_close')
        io_loop.stop()


if __name__ == '__main__':
    log_initialize()
    client = MyTcpClient(('127.0.0.1', 5000))
    client.start()

    io_loop = ioloop.IOLoop.instance()
    io_loop.start()

