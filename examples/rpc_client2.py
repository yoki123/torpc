# -*- coding: utf-8 -*-

import time

import datetime
from tornado import ioloop, gen

from torpc import Services
from torpc import RPCClient


class MyRPCClient(RPCClient):
    def on_closed(self):
        pass

    def on_connected(self):
        global t1
        t1 = time.time()


def register_callback(future):
    result = future.result()
    print(result)

    f = rpc_client.call('call_note', 'client1', 'ping')
    f.add_done_callback(cb)


@gen.coroutine
def benchmark_with_gen():
    global num_calls, t1
    t1 = time.time()
    for i in xrange(num_calls):
        future = rpc_client.call('sum', 2, 1)
        result = yield gen.with_timeout(datetime.timedelta(60), future)
        assert result == 3
        counter[0] += 1
        if i == num_calls:
            print('qps = %d' % (num_calls / (time.time() - t1)))
            rpc_client.close()
            io_loop.stop()


def cb(future):
    result = future.result()
    # assert result == 'pong from rpc client 1'

    counter[0] += 1
    if counter[0] == num_calls:
        print('qps = %d' % (num_calls / (time.time() - t1)))
        rpc_client.close()
        io_loop.stop()
    else:
        f = rpc_client.call('call_note', 'client1', 'ping')
        f.add_done_callback(cb)


def benchmark_with_callback():
    future = rpc_client.call('sum', 2, 1)
    future.add_done_callback(cb)


if __name__ == '__main__':

    num_calls = 2000
    counter = [0]
    service = Services()

    rpc_client = MyRPCClient(('127.0.0.1', 5000), 'client2')

    # benchmark_with_gen()
    benchmark_with_callback()

    io_loop = ioloop.IOLoop.instance()

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
        print "exited cleanly"
