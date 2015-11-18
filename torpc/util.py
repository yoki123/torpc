# -*- coding: utf-8 -*-

import socket

from tornado import netutil


def get_address_type(address):
    if isinstance(address, str):
        if not hasattr(socket, 'AF_UNIX'):
            raise Exception("Unix socket not support")
        return "uds"
    if isinstance(address, tuple) and len(address) == 2:
        return "tcp"
    raise Exception("Address not support")


def auto_build_socket(address):
    """Auto build a socket.socket instance from address"""

    address_type = get_address_type(address)
    if address_type == 'tcp':
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)

    elif address_type == 'uds':
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    else:
        raise Exception("Unknown address type")
    sock.setblocking(0)
    return sock


def build_listener(address, backlog=0):
    """address: tuple ('0.0.0.0', 1234) or unix domain socket path such as '/tmp/tmp.sock'"""

    address_type = get_address_type(address)

    if address_type == 'tcp':
        host, port = address
        socks = netutil.bind_sockets(port, address=host, backlog=backlog)
        return socks

    if address_type == 'uds':
        sock = netutil.bind_unix_socket(address, mode=0o600, backlog=backlog)
        return [sock]
