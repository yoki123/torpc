# -*- coding: utf-8 -*-
'''
Maybe this isn't a benchmark, just a test for torpc only now.
'''

import time
import sys

sys.path.append('../')

from multiprocessing import Process
from tornado import ioloop, gen
from torpc import RPCServer, RPCClient


def rpc_server_entry():
    server = RPCServer(('127.0.0.1', 5000))

    @server.service.register()
    def sum(x, y):
        return x + y

    server.start()
    ioloop.IOLoop.instance().start()


def async_callback(f):
    global counter
    counter += 1
    if counter == num_of_test:
        global time_start
        print('async_callback: %d op/s' % (num_of_test / (time.clock() - time_start)))
        io_loop.stop()
        sp.terminate()

    else:
        rpc_client.call("sum", 1, 2, callback=async_callback)


@gen.coroutine
def async_coroutine():
    time_start = time.clock()
    for i in xrange(num_of_test):
        # ret = yield gen.with_timeout(time.time() + 10, rpc_client.call("sum", 1, 2))
        ret = yield rpc_client.call("sum", 1, 2)
    print('async_coroutine: %d op/s' % (num_of_test / (time.clock() - time_start)))


if __name__ == '__main__':

    sp = Process(target=rpc_server_entry, args=())
    sp.start()

    # a simple way to wait rpc server get ready.
    time.sleep(2)

    num_of_test = 100000
    counter = 0
    time_start = time.clock()

    io_loop = ioloop.IOLoop.instance()
    rpc_client = RPCClient(('127.0.0.1', 5000))

    async_coroutine()

    rpc_client.call("sum", 1, 2, callback=async_callback)

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
        sp.terminate()
