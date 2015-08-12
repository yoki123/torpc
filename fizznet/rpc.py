# -*- coding: utf-8 -*-

import functools
import socket
import struct

import marshal as packer
from tornado.concurrent import TracebackFuture

from tcp import TcpServer, Connection

RPC_REQUEST = 0
RPC_RESPONSE = 1
RPC_NOTICE = 2
RPC_REGISTER = 3  # rpc服务注册
HEAD_LEN = struct.calcsize('!ibi')


def _NoSyncIDGenerator():
    counter = 0
    while True:
        yield counter
        counter += 1
        if counter > (1 << 30):
            counter = 0


class RPCServerError(Exception):
    pass


class RPCConnection(Connection):
    __slots__ = ('_buff', '_generator', '_request_table', 'service')

    def __init__(self, connection, service=None):
        self._buff = ''
        self._generator = _NoSyncIDGenerator()
        self._request_table = {}
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
            err = str(e)
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
            print(e)

    def handle_rpc_register(self, msg_id, method_name, args):
        try:
            result = self.service.call(method_name, self, args)
        except Exception, e:
            err = str(e)
            print(err)
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
            print('time out?')
            return
        if err:
            raise RPCServerError(err)

        future = self._request_table.pop(msg_id)
        future.set_result(ret)

    def _handle_read(self, data):
        self.on_receive(data)

    def on_receive(self, data):
        # 黏包
        self._buff += data
        _cur_len = len(self._buff)

        while _cur_len > HEAD_LEN:
            data_length, msg_type, msg_id = struct.unpack('!ibi', self._buff[:HEAD_LEN])

            if _cur_len - HEAD_LEN >= data_length:
                request = self._buff[HEAD_LEN:HEAD_LEN + data_length]

                # 拆包
                self._buff = self._buff[HEAD_LEN + data_length:]  # 拆包之后，可能有剩余部分
                _cur_len = len(self._buff)

                try:
                    req = packer.loads(request)
                except Exception, e:
                    print(e)
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

    def call(self, method_name, *arg):
        msgid = next(self._generator)
        request = packer.dumps((method_name, arg))
        buff = struct.pack('!ibi', len(request), RPC_REQUEST, msgid) + request

        future = TracebackFuture()
        self._request_table[msgid] = future
        self.write(buff)
        return future

    def notice(self, method_name, *arg):
        msgid = next(self._generator)
        request = packer.dumps((method_name, arg))
        buff = struct.pack('!ibi', len(request), RPC_REQUEST, msgid) + request
        self.write(buff)

    def register(self, name, callback=None):
        msgid = next(self._generator)
        request = packer.dumps(('register', name))
        buff = struct.pack('!ibi', len(request), RPC_REGISTER, msgid) + request
        future = TracebackFuture()
        if callback:
            future.add_done_callback(callback)
        self._request_table[msgid] = future
        self.write(buff)
        return future


class RPCServer(TcpServer):
    def __init__(self, address, service=None):
        self.service = service
        TcpServer.__init__(self, address, RPCConnection)

    def on_connect(self, sock):
        sock.setblocking(0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        # connection.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 60)
        # connection.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 5)
        # connection.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 20)

        conn = self._build_class(sock, self.service)
        close_callback = functools.partial(self.on_close, conn)
        conn.set_close_callback(close_callback)
        conn.read_util_close(conn.on_receive)


class RPCClient(object):
    def __init__(self, address, service=None):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(0)
        self.client = RPCConnection(sock, service)
        self.client.set_close_callback(self.on_closed)
        self.client.connect(address, self.on_connected)

    def call(self, method_name, *arg):
        return self.client.call(method_name, *arg)

    def on_connected(self):
        pass

    def on_closed(self):
        pass

    def register(self, name, callback):
        self.client.register(name, callback)
