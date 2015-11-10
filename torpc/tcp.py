# -*- coding: utf-8 -*-

import socket
import errno
import collections
import functools
import logging
import os

from tornado import ioloop

_ERRNO_WOULDBLOCK = (errno.EAGAIN, errno.EWOULDBLOCK)
_ERRNO_INPROGRESS = (errno.EINPROGRESS,)
logger = logging.getLogger(__name__)


class ConnectionClosedError(IOError):
    pass


class Connection(object):
    __slots__ = (
        'fd', 'io_loop', 'socket', '_write_buffer', '_added_handler', '_connecting',
        '_closed', '_connect_callback', '_read_callback', '_close_callback')

    def __init__(self, connection):
        self.fd = connection.fileno()
        self.io_loop = ioloop.IOLoop.current()
        self.socket = connection

        self._write_buffer = collections.deque()

        self._added_handler = False
        self._connecting = False
        self._closed = False

        self._connect_callback = None
        self._read_callback = None
        self._close_callback = None

    def set_close_callback(self, close_callback):
        self._close_callback = close_callback

    def read_util_close(self, read_callback=None):
        self._read_callback = read_callback
        if self._added_handler:
            # only read_util_close and read_util_close will call add_handler, so, only READ and WRITE event.
            self.io_loop.update_handler(self.fd, self.io_loop.READ | self.io_loop.WRITE)
        else:
            self.io_loop.add_handler(self.fd, self._handle_events, self.io_loop.READ)
            self._added_handler = True

    def write(self, buf):
        if not self._closed:
            self._write_buffer.append(buf)
            self.io_loop.update_handler(self.fd, self.io_loop.WRITE)
        else:
            raise ConnectionClosedError('connect is closed')

    def _handle_read(self, data):
        self._read_callback(data)

    def _handle_events(self, fd, events):
        if self._connecting:
            err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if err != 0:
                logger.debug('{0} {1}'.format(err, os.strerror(err)))
                return self.close()

            if self._connect_callback:
                self._connect_callback()
            self._connecting = False

        if events & self.io_loop.READ:
            try:
                _buf = self.socket.recv(1024)
                if not _buf:
                    if self._write_buffer:
                        self.io_loop.update_handler(self.fd, self.io_loop.WRITE)
                    else:
                        return self.close()
                else:
                    self._handle_read(_buf)

            except socket.error as e:
                if e.args[0] not in _ERRNO_WOULDBLOCK:
                    logger.debug(str(e))
                    return self.close()

        if events & self.io_loop.WRITE:
            try:
                while self._write_buffer:
                    _send_buf = self._write_buffer.popleft()
                    while _send_buf:
                        sent = self.socket.send(_send_buf)
                        _send_buf = _send_buf[sent:]

                self.io_loop.update_handler(self.fd, self.io_loop.READ)
            except socket.error as e:
                if e.args[0] not in _ERRNO_WOULDBLOCK:
                    logger.debug(str(e))
                    return self.close()

        if events & self.io_loop.ERROR:
            err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            logger.warning(str(err))
            self.close()

    def close(self):
        self.io_loop.remove_handler(self.fd)
        self.socket.close()
        self._closed = True
        self.socket = None

        if self._close_callback:
            self._close_callback()

    def connect(self, address, callback=None):
        self._connecting = True
        if callback is not None:
            self._connect_callback = callback

        try:
            self.socket.connect(address)
        except socket.error as e:
            if e.args[0] not in _ERRNO_WOULDBLOCK and \
                            e.args[0] not in _ERRNO_INPROGRESS:
                logger.debug(str(e))
                self.close()

        if self._added_handler:
            self.io_loop.update_handler(self.fd, self.io_loop.WRITE | self.io_loop.READ)
        else:
            self.io_loop.add_handler(self.fd, self._handle_events, self.io_loop.WRITE)
            self._added_handler = True


class TcpServer(object):
    def __init__(self, address, build_class, set_keep_alive=False, **build_kwargs):
        self._address = address
        self._build_class = build_class
        self._set_keep_alive = set_keep_alive
        self._build_kwargs = build_kwargs

    def _accept_handler(self, sock, fd, events):
        while True:
            try:
                connection, address = sock.accept()
            except socket.error, e:
                if e[0] not in _ERRNO_WOULDBLOCK:
                    raise
                return

            self._handle_connect(connection)

    def _handle_connect(self, sock):
        sock.setblocking(0)

        # set keepalive
        if self._set_keep_alive:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 60)
            sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 5)
            sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 20)

        conn = self._build_class(sock, **self._build_kwargs)
        self.on_connect(conn)
        close_callback = functools.partial(self.on_close, conn)
        conn.set_close_callback(close_callback)

        handle_receive = functools.partial(self.handle_stream, conn)
        conn.read_util_close(handle_receive)

    def start(self, backlog=0):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setblocking(0)
        sock.bind(self._address)
        sock.listen(backlog)

        io_loop = ioloop.IOLoop.instance()
        callback = functools.partial(self._accept_handler, sock)
        io_loop.add_handler(sock.fileno(), callback, io_loop.READ)

    def handle_stream(self, conn, buff):
        pass

    def on_close(self, conn):
        pass

    def on_connect(self, conn):
        pass


class TcpClient(object):
    def __init__(self, address):
        self.conn = None
        self._address = address

    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setblocking(0)
        self.conn = Connection(sock)
        self.conn.set_close_callback(self.on_close)
        self.conn.connect(self._address, self.on_connected)
        self.conn.read_util_close(self.on_receive)

    def on_connected(self):
        pass

    def write(self, buf):
        self.conn.write(buf)

    def on_receive(self, buf):
        pass

    def on_close(self):
        pass

    def close(self):
        self.conn.close()
