# -*- coding: utf-8 -*-

import functools
import struct
import time
import logging
import traceback

import msgpack as packer

from tornado.concurrent import TracebackFuture

from services import Services
from torpc.tcp import TcpServer, Connection
from torpc.util import set_keepalive, auto_build_socket

logger = logging.getLogger(__name__)

RPC_REQUEST = 0
RPC_RESPONSE = 1
RPC_NOTICE = 2
RPC_REGISTER = 3  # just for duplex rpc service
HEAD_LEN = struct.calcsize('!ibi')


def _IDGenerator():
    counter = 0
    while True:
        yield counter
        counter += 1
        if counter > (1 << 30):
            counter = 0


class RPCServerError(Exception):
    pass


class RPCTimeOutError(Exception):
    pass


class RPCConnection(Connection):
    __slots__ = ('_buff', '_generator', '_request_table', '_request_timeout', 'service')

    def __init__(self, connection, service=None, request_timeout=0):
        self._buff = ''
        self._generator = _IDGenerator()
        self._request_table = {}
        self._request_timeout = request_timeout
        self.service = service
        Connection.__init__(self, connection)

    def result_callback(self, msg_id, future):
        result = future.result()
        buff = packer.dumps((None, result))
        self.write(struct.pack('!ibi', len(buff), RPC_RESPONSE, msg_id) + buff)

    def handle_rpc_request(self, msg_id, method_name, *args):
        try:
            result = self.service.call(method_name, *args)
        except Exception, e:
            err = str(traceback.format_exc())
            buff = packer.dumps((err, None))
            self.write(struct.pack('!ibi', len(buff), RPC_RESPONSE, msg_id) + buff)
        else:

            if isinstance(result, TracebackFuture):
                cb = functools.partial(self.result_callback, msg_id)
                result.add_done_callback(cb)
            else:
                buff = packer.dumps((None, result))
                self.write(struct.pack('!ibi', len(buff), RPC_RESPONSE, msg_id) + buff)

    def handle_rpc_notice(self, msg_id, method_name, args):
        try:
            self.service.call(method_name, *args)
        except Exception, e:
            logger.error(str(e))

    def handle_rpc_register(self, msg_id, method_name, args):
        try:
            result = self.service.call(method_name, self, args)
        except Exception, e:
            err = str(traceback.format_exc())
            buff = packer.dumps((err, None))
            self.write(struct.pack('!ibi', len(buff), RPC_RESPONSE, msg_id) + buff)
        else:
            if isinstance(result, TracebackFuture):
                cb = functools.partial(self.result_callback, msg_id)
                result.add_done_callback(cb)
            else:
                buff = packer.dumps((None, result))
                self.write(struct.pack('!ibi', len(buff), RPC_RESPONSE, msg_id) + buff)

    def handle_rpc_response(self, msg_id, err, ret):
        if msg_id not in self._request_table:
            logger.debug('response time out?')
            return
        if err:
            logger.debug('{0} {1} {2}'.format(msg_id, err, ret))
            raise RPCServerError(err)

        future = self._request_table.pop(msg_id)
        future.set_result(ret)

    def _handle_read(self, data):
        self.on_receive(data)

    def on_receive(self, data):
        # sticky package
        self._buff += data
        _cur_len = len(self._buff)

        while _cur_len > HEAD_LEN:
            data_length, msg_type, msg_id = struct.unpack('!ibi', self._buff[:HEAD_LEN])

            if _cur_len - HEAD_LEN >= data_length:
                request = self._buff[HEAD_LEN:HEAD_LEN + data_length]

                # split package;
                # next package data in this package tail.
                self._buff = self._buff[HEAD_LEN + data_length:]

                _cur_len = len(self._buff)

                try:
                    req = packer.loads(request)
                except Exception, e:
                    logger.debug(str(e))
                    return

                if msg_type == RPC_REQUEST:
                    (method_name, args) = req
                    self.handle_rpc_request(msg_id, method_name, *args)

                elif msg_type == RPC_RESPONSE:
                    (err, response) = req
                    self.handle_rpc_response(msg_id, err, response)

                elif msg_type == RPC_NOTICE:
                    (method_name, args) = req
                    self.handle_rpc_notice(msg_id, method_name, args)

                elif msg_type == RPC_REGISTER:
                    (method_name, args) = req
                    self.handle_rpc_register(msg_id, method_name, args)
            else:
                break

    def add_request_table(self, msg_id, future):
        if self._request_timeout:
            self.io_loop.add_timeout(time.time() + self._request_timeout, self.message_timeout_cb, future)
        self._request_table[msg_id] = future

    def call(self, method_name, *arg, **kwargs):
        _callback = kwargs.get('callback')
        msg_id = next(self._generator)
        request = packer.dumps((method_name, arg))
        buff = struct.pack('!ibi', len(request), RPC_REQUEST, msg_id) + request

        future = TracebackFuture()
        self.add_request_table(msg_id, future)

        if _callback:
            future.add_done_callback(_callback)
        self.write(buff)
        return future

    def notice(self, method_name, *arg):
        msgid = next(self._generator)
        request = packer.dumps((method_name, arg))
        buff = struct.pack('!ibi', len(request), RPC_REQUEST, msgid) + request
        self.write(buff)

    def register(self, name, callback=None):
        msg_id = next(self._generator)
        request = packer.dumps(('register', name))
        buff = struct.pack('!ibi', len(request), RPC_REGISTER, msg_id) + request
        future = TracebackFuture()
        if callback:
            future.add_done_callback(callback)
        self.add_request_table(msg_id, future)
        self.write(buff)
        return future

    def message_timeout_cb(self, msg_id):
        if msg_id not in self._request_table:
            logger.debug('not exsit, timeout?')
            return
        self._request_table.pop(msg_id)
        raise RPCTimeOutError(msg_id)


class RPCServer(TcpServer):
    def __init__(self, address, service_cls=None, set_keep_alive=False, request_timeout=0):
        if callable(service_cls):
            self.service = service_cls()
        else:
            self.service = Services()
        TcpServer.__init__(self, address, RPCConnection, set_keep_alive, request_timeout=request_timeout)

    def _handle_connect(self, sock):
        sock.setblocking(0)

        # set keepalive
        if self._set_keep_alive:
            set_keepalive(sock)

        conn = self._build_class(sock, self.service, **self._build_kwargs)
        self.on_connect(conn)

        close_callback = functools.partial(self.on_close, conn)
        conn.set_close_callback(close_callback)

    def on_connect(self, conn):
        logger.debug('on_connect: %s' % repr(conn.getaddress()))
        conn.read_util_close(conn.on_receive)


class RPCClient(object):
    def __init__(self, address, rpc_name='', service_cls=None, request_timeout=0):
        if callable(service_cls):
            self.service = service_cls()
        else:
            self.service = Services()

        self.rpc_name = rpc_name

        sock = auto_build_socket(address)

        self._conn = RPCConnection(sock, self.service, request_timeout)
        self._conn.set_close_callback(self.on_closed)
        self._conn.connect(address, self.on_connected)

    def call(self, method_name, *arg, **kwargs):
        return self._conn.call(method_name, *arg, **kwargs)

    def notice(self, method_name, *arg):
        return self._conn.notice(method_name, *arg)

    def on_connected(self):
        if self.rpc_name:
            self._conn.register(self.rpc_name, self._register_callback)

    def _register_callback(self, future):
        ret = future.result()
        if not ret:
            logger.warning("register failed")
            return
        self.on_registered(ret)

    def on_registered(self, ret):
        logger.debug('on_registered')

    def on_closed(self):
        logger.debug('on_closed')
        self._conn.io_loop.stop()

    def close(self):
        self._conn.close()


class DuplexRPCServer(RPCServer):
    def __init__(self, address, service_cls=None, set_keep_alive=False, request_timeout=0):
        self.rpc_clients = {}
        RPCServer.__init__(self, address, service_cls=service_cls, set_keep_alive=set_keep_alive,
                           request_timeout=request_timeout)
        self.service.dispatch('register', self._rpc_register)
        self.service.dispatch('call_node', self.call_node)

    def on_close(self, conn):
        _node_name = None
        for _name, _conn in self.rpc_clients.iteritems():
            if _conn == conn:
                _node_name = _name
                break
        if _node_name:
            self.rpc_clients.pop(_node_name)
            logger.debug('%s disconnect' % _node_name)

    def call_node(self, name, method_name, *arg):
        if name not in self.rpc_clients:
            raise Exception('node {0} not exist'.format(name))
        node = self.rpc_clients[name]
        future = node.call(method_name, *arg)
        return future

    def _rpc_register(self, conn, name):
        if name in self.rpc_clients:
            logger.warning('%s already register' % name)
            return False
        self.rpc_clients[name] = conn
        self.on_registered(name, conn)
        return True

    def on_registered(self, name, conn):
        logger.debug('%s registered ' % name)
