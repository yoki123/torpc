# -*- coding: utf-8 -*-

class NoServiceError(Exception):
    pass


class Services(object):
    def __init__(self):
        self._targets = {}

    def route(self, pid=0):
        def decorator(f):
            if pid:
                _key = pid
            else:
                _key = f.__name__
            if _key in self._targets:
                raise KeyError(_key)
            self._targets[_key] = f
            return f

        return decorator

    def call(self, pid, *args):
        method = self._targets.get(pid)
        if not method:
            raise NoServiceError(pid)
        return method(*args)
