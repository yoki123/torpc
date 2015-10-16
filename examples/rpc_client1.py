# -*- coding: utf-8 -*-

from tornado import ioloop

from torpc import RPCClient

if __name__ == '__main__':

    rc = RPCClient(('127.0.0.1', 5000), 'client1')


    @rc.service.register()
    def ping():
        return 'pong from rpc client1'


    io_loop = ioloop.IOLoop.instance()

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
        print "exited cleanly"
