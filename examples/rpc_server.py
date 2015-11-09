# -*- coding: utf-8 -*-

from tornado import ioloop

from torpc import RPCServer


class MyRPCServer(RPCServer):
    def on_close(self, conn):
        _node_name = None
        for _name, _conn in rpc_clients.iteritems():
            if _conn == conn:
                _node_name = _name
                break
        if _node_name:
            rpc_clients.pop(_node_name)
            print('%s disconnect' % _node_name)


if __name__ == '__main__':
    rpc_clients = {}

    server = MyRPCServer(('127.0.0.1', 5000))


    @server.service.register()
    def sum(x, y):
        return x + y


    @server.service.register()
    def register(conn, name):
        if name in rpc_clients:
            print('already register')
            return
        rpc_clients[name] = conn
        return True


    @server.service.register()
    def call_node(name, method_name, *arg):
        if name not in rpc_clients:
            raise Exception('node {0} not exist'.format(name))
        node = rpc_clients[name]
        future = node.call(method_name, *arg)
        return future


    server.start()

    io_loop = ioloop.IOLoop.instance()

    try:
        io_loop.start()
    except KeyboardInterrupt:
        io_loop.stop()
        print "exited cleanly"
