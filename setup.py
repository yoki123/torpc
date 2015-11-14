#!/usr/bin/env python
import os

version = '0.0.1'

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='torpc',
      version=version,
      description='A tiny async tcp and duplex rpc implementation using Tornado IOLoop.',
      url='http://github.com/yoki123/torpc',
      download_url='',
      long_description=read('README.rst'),
      author='Yoki',
      author_email='ispeedly@gmail.com',
      keywords=['tornado', 'rpc', 'async'],
      license='MIT',
      packages=['torpc']
)

