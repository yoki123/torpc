# -*- coding: utf-8 -*-

import socket
import os


def unlink(path):
    from errno import ENOENT

    try:
        os.unlink(path)
    except OSError, ex:
        if ex.errno != ENOENT:
            raise


def link(src, dest):
    from errno import ENOENT

    try:
        os.link(src, dest)
    except OSError, ex:
        if ex.errno != ENOENT:
            raise


def auto_build_socket(address):
    '''
    auto build a socket.socket instance from address
    :param address: tuple ('0.0.0.0', 1234) or unix domain socket path '/tmp/tmp.sock'
    :return: socket.socket instance
    '''
    if isinstance(address, str):
        if os.name == 'nt':
            raise Exception("unix socket not support on nt")
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.setblocking(0)
        return sock
    if isinstance(address, tuple) and len(address) == 2:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        sock.setblocking(0)
        return sock
    raise Exception("address not correct")


def bind_unix_listener(path, backlog=0, user=None):
    pid = os.getpid()
    tempname = '%s.%s.tmp' % (path, pid)
    backname = '%s.%s.bak' % (path, pid)
    unlink(tempname)
    unlink(backname)
    link(path, backname)
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.setblocking(0)
        sock.bind(tempname)

        if user is not None:
            import pwd

            user = pwd.getpwnam(user)
            os.chown(tempname, user.pw_uid, user.pw_gid)
            os.chmod(tempname, 0600)
        sock.listen(backlog)
        os.rename(tempname, path)
        return sock
    finally:
        unlink(backname)


def bind_tcp_listener(address, backlog=0):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    # sock.setsockopt(socket.SOLsocket, socket.SO_REUSEADDR, 1)
    sock.setblocking(0)
    sock.bind(address)
    sock.listen(backlog)
    return sock


def build_listener(address, backlog=0):
    '''
    :param address: tuple ('0.0.0.0', 1234) or unix domain socket path '/tmp/tmp.sock'
    :param backlog: max listen count.
    :return: a socket.socket instance with bind&listen
    '''
    if isinstance(address, str):
        if os.name == 'nt':
            raise Exception("unix socket not support on nt")
        return bind_unix_listener(address, backlog)

    if isinstance(address, tuple) and len(address) == 2:
        return bind_tcp_listener(address, backlog)

    raise Exception("address not correct")
