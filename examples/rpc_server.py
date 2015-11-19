# -*- coding: utf-8 -*-

import sys

sys.path.append('../')

from tornado import ioloop

from example_utils import log_initialize
from torpc import DuplexRPCServer

if __name__ == '__main__':
    log_initialize()
    server = DuplexRPCServer(('127.0.0.1', 5000))


    @server.service.register()
    def sum(x, y):
        return x + y


    @server.service.register()
    def ping_client1():
        # call client1 and return the future object
        future = server.call_node('client1', 'ping')
        return future


    server.start()

    ioloop.IOLoop.instance().start()
