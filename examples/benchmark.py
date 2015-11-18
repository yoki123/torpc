# -*- coding: utf-8 -*-
import time
import sys
import argparse

sys.path.append('../')

from multiprocessing import Process, Value
from tornado import ioloop, gen
from torpc import RPCServer, RPCClient

from example_utils import log_initialize


def rpc_server_entry(rpc_address):
    log_initialize()
    server = RPCServer(rpc_address)

    @server.service.register()
    def sum(x, y):
        return x + y

    server.start()
    ioloop.IOLoop.instance().start()


def rpc_client_entry(rpc_address, num_of_loop, time_start, time_stop):
    log_initialize()
    rpc_client = RPCClient(rpc_address)

    run_call_server(rpc_client, num_of_loop, time_start, time_stop)

    ioloop.IOLoop.instance().start()


@gen.coroutine
def run_call_server(rpc_client, num_of_loop, time_start, time_stop):
    # The time of first client process beginning
    if time_start.value == 0:
        time_start.value = time.time()

    for i in range(num_of_loop):
        # ret = yield gen.with_timeout(time.time() + 10, rpc_client.call("sum", 1, 2))
        ret = yield rpc_client.call("sum", 1, 2)

    # The time of last client process finished
    time_now = time.time()
    if time_now > time_stop.value:
        time_stop.value = time_now

    ioloop.IOLoop.instance().stop()


ARGS = argparse.ArgumentParser(description="ToRPC RPC benchmark.")
ARGS.add_argument(
    '-c', action="store", dest='client',
    default=1, help='Number of rpc client.')
ARGS.add_argument(
    '-n', action="store", dest='number',
    default=10000, help='Number of loop for per client.')
ARGS.add_argument(
    '-host', action="store", dest='host',
    default='127.0.0.1', help='Host name. (default 127.0.0.1)')
ARGS.add_argument(
    '-p', action="store", dest='port',
    default=5000, type=int, help='Port number (default 5000)')
ARGS.add_argument(
    '-u', action="store", dest='unix_path',
    default=False, help='Use unix domain socket.')

if __name__ == '__main__':

    args = ARGS.parse_args()
    if ':' in args.host:
        args.host, port = args.host.split(':', 1)
        args.port = int(port)

    if args.unix_path:
        rpc_address = args.unix_path
    else:
        rpc_address = (args.host, args.port)

    # print(rpc_address)
    num_of_loop = int(args.number)
    num_of_client = int(args.client)

    time_start = Value('d', 0)
    time_stop = Value('d', 0)

    sp = Process(target=rpc_server_entry, args=(rpc_address,))
    sp.start()

    client_processes = []
    for i in range(num_of_client):
        cp = Process(target=rpc_client_entry, args=(rpc_address, num_of_loop, time_start, time_stop))
        client_processes.append(cp)

    for cp in client_processes:
        cp.start()

    for cp in client_processes:
        cp.join()

    total_time_value = time_stop.value - time_start.value
    print('Throughput: %d [#/sec]' % (num_of_loop * num_of_client / total_time_value))

    sp.terminate()