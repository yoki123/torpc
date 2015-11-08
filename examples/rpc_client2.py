# -*- coding: utf-8 -*-

import time

from tornado import ioloop, gen

from torpc import RPCClient


class MyRPCClient(RPCClient):
    def on_closed(self):
        pass

    def on_connected(self):
        global t1
        t1 = time.time()


@gen.coroutine
def test_rpc():
    ret = yield rpc_client.call('sum', 11, 22)
    print('call sum from rpc server, result:{0}'.format(ret))

    ret = yield rpc_client.call('call_node', "client1", "ping")
    print('call ping from client1 through server, result:{0}'.format(ret))


if __name__ == '__main__':

    rpc_client = MyRPCClient(('127.0.0.1', 5000), 'client2')
    test_rpc()
    io_loop = ioloop.IOLoop.instance()

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
        print "exited cleanly"
