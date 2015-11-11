# -*- coding: utf-8 -*-

class NoServiceError(Exception):
    pass


class Services(object):
    def __init__(self):
        self._targets = {}

    def dispatch(self, key, func):
        if key in self._targets:
            raise KeyError(key)
        self._targets[key] = func

    def register(self, command=0):
        def decorator(f):
            if command:
                _key = command
            else:
                _key = f.__name__
            if _key in self._targets:
                raise KeyError(_key)
            self._targets[_key] = f
            return f

        return decorator

    def call(self, command, *args):
        method = self._targets.get(command)
        if not method:
            raise NoServiceError(command)
        return method(*args)
