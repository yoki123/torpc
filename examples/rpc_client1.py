# -*- coding: utf-8 -*-

from tornado import ioloop

from fizznet import RPCClient
from fizznet import Services


def register_callback(future):
    result = future.result()
    print(result)


if __name__ == '__main__':
    service = Services()


    @service.route()
    def ping():
        return 'pong from rpc client 1'


    rc = RPCClient(('127.0.0.1', 5000), service)

    rc.client.register('client1', register_callback)

    io_loop = ioloop.IOLoop.instance()

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
        print "exited cleanly"
