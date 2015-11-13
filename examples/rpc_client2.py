# -*- coding: utf-8 -*-

import logging
import sys

sys.path.append('../')

from tornado import ioloop, gen

from example_utils import log_initialize
from torpc import RPCClient

logger = logging.getLogger(__name__)


@gen.coroutine
def test_rpc():
    ret = yield rpc_client.call('sum', 11, 22)
    logger.info('call sum from the rpc server, result: {0}'.format(ret))

    ret = yield rpc_client.call('call_node', "client1", "ping")
    logger.info('call ping from client1 through the rpc server, result: {0}'.format(ret))

    ret = yield rpc_client.call('ping_client1')
    logger.info('call ping_client1 from the rpc server, result: {0}'.format(ret))


if __name__ == '__main__':
    log_initialize()
    rpc_client = RPCClient(('127.0.0.1', 5000), 'client2')
    test_rpc()

    io_loop = ioloop.IOLoop.instance()
    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
        print "exited cleanly"
