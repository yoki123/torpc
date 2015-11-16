# -*- coding: utf-8 -*-

import logging


def log_initialize():
    log_format = '%(asctime)s %(filename)s[line:%(lineno)d] [%(levelname)s] %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)
