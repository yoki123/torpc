# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

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
        def decorator(func):
            if command:
                _key = command
            else:
                _key = func.__name__
            if _key in self._targets:
                raise KeyError(_key)
            self._targets[_key] = func
            return func

        return decorator

    def call(self, command, *args):
        method = self._targets.get(command)
        if not method:
            raise NoServiceError(command)
        logger.debug('call method %s' % method.__name__)
        return method(*args)
