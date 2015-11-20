# -*- coding: utf-8 -*-

import socket
import errno
import collections
import functools
import logging

from tornado import ioloop
from tornado.iostream import errno_from_exception

from torpc.util import auto_build_socket, build_listener

_ERRNO_WOULDBLOCK = (errno.EAGAIN, errno.EWOULDBLOCK)
if hasattr(errno, "WSAEWOULDBLOCK"):
    _ERRNO_WOULDBLOCK += (errno.WSAEWOULDBLOCK,)

_ERRNO_INPROGRESS = (errno.EINPROGRESS,)
if hasattr(errno, "WSAEINPROGRESS"):
    _ERRNO_INPROGRESS += (errno.WSAEINPROGRESS,)

_ERRNO_CONNRESET = (errno.ECONNRESET, errno.ECONNABORTED, errno.EPIPE,
                    errno.ETIMEDOUT)
if hasattr(errno, "WSAECONNRESET"):
    _ERRNO_CONNRESET += (errno.WSAECONNRESET, errno.WSAECONNABORTED, errno.WSAETIMEDOUT)

logger = logging.getLogger(__name__)

WRITE_EVENT = ioloop.IOLoop.WRITE
READ_EVENT = ioloop.IOLoop.READ
ERROR_EVENT = ioloop.IOLoop.ERROR


class ConnectionClosedError(IOError):
    pass


class Connection(object):
    """Low level connection object.
    """
    __slots__ = (
        'fd', 'io_loop', 'socket', '_write_buffer', '_is_connecting',
        '_is_closed', '_connect_callback', '_read_callback', '_close_callback', '_listened_events', '_read_size')

    def __init__(self, connection):
        self.fd = connection.fileno()
        self.io_loop = ioloop.IOLoop.current()
        self.socket = connection

        self._write_buffer = collections.deque()

        self._is_connecting = False
        self._is_closed = False

        self._connect_callback = None
        self._read_callback = None
        self._close_callback = None
        self._listened_events = 0
        self._read_size = 1024

        self.socket.setblocking(0)

    def getaddress(self):
        return self.socket.getpeername()

    def set_close_callback(self, close_callback):
        self._close_callback = close_callback

    def read_util_close(self, read_callback=None):
        self._read_callback = read_callback
        self._update_event_handler()

    def write(self, buf):
        if not self._is_closed:
            self._write_buffer.append(buf)
            self._update_event_handler(write=True)
        else:
            raise ConnectionClosedError('connect is closed')

    def _handle_read(self, data):
        self._read_callback(data)

    def _handle_events(self, fd, events):
        if self._is_connecting:
            err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            if err != 0:
                logger.debug('connecting error in _handle_events')
                return self.close()

            if self._connect_callback:
                self._connect_callback()
            self._is_connecting = False

        if events & READ_EVENT:
            try:
                _buf = self.socket.recv(self._read_size)
                if _buf:
                    self._handle_read(_buf)
                else:
                    return self.close()

            except socket.error as e:
                if errno_from_exception(e) not in _ERRNO_WOULDBLOCK:
                    logger.debug(str(e))
                    return self.close()

        if events & WRITE_EVENT:
            while self._write_buffer:
                _send_buf = self._write_buffer.popleft()
                try:
                    sent = self.socket.send(_send_buf)
                except (socket.error, IOError, OSError) as e:
                    if errno_from_exception(e) in _ERRNO_WOULDBLOCK:
                        logger.debug("write would block")
                        self._write_buffer.appendleft(_send_buf)
                        break
                    else:
                        return self.close()
                else:
                    if sent < len(_send_buf):
                        self._write_buffer.appendleft(_send_buf)

            # Buf if not calling _update_event_handler?
            if not self._write_buffer:
                self._update_event_handler(write=False)

        if events & ERROR_EVENT:
            err = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
            logger.debug("Error in event loop!: %s" % str(err))
            self.close()

    def close(self):
        if self._is_closed:
            return
        self.io_loop.remove_handler(self.fd)
        self.socket.close()
        self._is_closed = True
        self.socket = None
        self._listened_events = 0

        if self._close_callback:
            self._close_callback()

    def connect(self, address, callback=None):
        self._is_connecting = True
        if callback is not None:
            self._connect_callback = callback

        try:
            self.socket.connect(address)
        except socket.error as e:
            err = errno_from_exception(e)
            if err not in _ERRNO_WOULDBLOCK and err not in _ERRNO_INPROGRESS:
                logger.debug(str(e))
                self.close()

        self._update_event_handler()

    def _update_event_handler(self, write=True):
        if write:
            listened_events = READ_EVENT | WRITE_EVENT | ERROR_EVENT
        else:
            listened_events = READ_EVENT | ERROR_EVENT
        if self._listened_events == 0:
            try:
                self.io_loop.add_handler(self.fd, self._handle_events, listened_events)
            except (OSError, IOError, ValueError):
                self.close()
                return
        else:
            if self._listened_events != listened_events:
                try:
                    self.io_loop.update_handler(self.fd, listened_events)
                except (OSError, IOError, ValueError):
                    self.close()
                    return
        self._listened_events = listened_events

    def set_keepalive(self):
        raise NotImplementedError

    def set_nodelay(self):
        raise NotImplementedError


class TcpServer(object):
    def __init__(self, address, build_class, **build_kwargs):
        self._address = address
        self._build_class = build_class
        self._build_kwargs = build_kwargs

    def _accept_handler(self, sock, fd, events):
        while True:
            try:
                connection, address = sock.accept()
            except socket.error as e:
                if errno_from_exception(e) not in _ERRNO_WOULDBLOCK:
                    raise
                return

            self._handle_connect(connection)

    def _handle_connect(self, sock):
        conn = self._build_class(sock, **self._build_kwargs)
        self.on_connect(conn)

        close_callback = functools.partial(self.on_close, conn)
        conn.set_close_callback(close_callback)

    def start(self, backlog=0):
        socks = build_listener(self._address, backlog=backlog)

        io_loop = ioloop.IOLoop.instance()
        for sock in socks:
            callback = functools.partial(self._accept_handler, sock)
            io_loop.add_handler(sock.fileno(), callback, WRITE_EVENT | READ_EVENT | ERROR_EVENT)

    def handle_stream(self, conn, buff):
        logger.debug('handle_stream')

    def on_close(self, conn):
        logger.debug('on_close')

    def on_connect(self, conn):

        logger.debug('on_connect: %s' % repr(conn.getaddress()))

        handle_receive = functools.partial(self.handle_stream, conn)
        conn.read_util_close(handle_receive)


class TcpClient(object):
    def __init__(self, address):
        self.conn = None
        self._address = address

    def start(self):
        sock = auto_build_socket(self._address)
        self.conn = Connection(sock)
        self.conn.set_close_callback(self.on_close)
        self.conn.connect(self._address, self.on_connected)
        self.conn.read_util_close(self.on_receive)

    def on_connected(self):
        logger.debug('on_connected')

    def write(self, buf):
        self.conn.write(buf)

    def on_receive(self, buf):
        logger.debug('on_receive')

    def on_close(self):
        logger.debug('on_close')

    def close(self):
        self.conn.close()
