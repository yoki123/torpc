# -*- coding: utf-8 -*-

from tornado import ioloop

from torpc import DuplexRPCServer

if __name__ == '__main__':

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

    io_loop = ioloop.IOLoop.instance()

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
        print "exited cleanly"
