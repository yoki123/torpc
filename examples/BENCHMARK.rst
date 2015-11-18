Echo server in python
=====================

Based on https://github.com/methane/echoserver

environment::

	OS: CentOS 6.6 x64
	CPU: Intel i5-3470 3.20GHz (4 cores)
	Memory: 8 GB 1600 MHz DDR3
	Python: 2.7.10
	PyPy: 4.0.0

mybench.sh

.. code:: shell

	#!/bin/sh
	./client -c1 -o1 -h100000 127.0.0.1
	./client -c2 -o1 -h100000 127.0.0.1
	./client -c3 -o1 -h100000 127.0.0.1
	./client -c10 -o1 -h100000 127.0.0.1

Gevent
------
Gevent 1.0.2 + CPython 2.7.10::

	Throughput: 26571.11 [#/sec]
	Throughput: 31528.65 [#/sec]
	Throughput: 33338.36 [#/sec]
	Throughput: 36480.10 [#/sec]

Twisted
-------
Twisted 15.2.1 + CPython 2.7.10::

	Throughput: 15559.43 [#/sec]
	Throughput: 18636.95 [#/sec]
	Throughput: 20074.41 [#/sec]
	Throughput: 23030.79 [#/sec]

Twisted 15.2.1 + PyPy 4.0::

	Throughput: 37047.29 [#/sec]
	Throughput: 65331.75 [#/sec]
	Throughput: 78213.38 [#/sec]
	Throughput: 105245.08 [#/sec]

Asyncio
-------
Asyncio 3.4.3 + CPython 3.5::

	Throughput: 22377.98 [#/sec]
	Throughput: 29548.20 [#/sec]
	Throughput: 33483.62 [#/sec]
	Throughput: 41098.14 [#/sec]

Tornado
-------
Tornado 4.2.1 + CPython 2.7.10::

	Throughput: 12831.44 [#/sec]
	Throughput: 14863.33 [#/sec]
	Throughput: 15751.25 [#/sec]
	Throughput: 17155.48 [#/sec]

Tornado 4.2.1 + PyPy 4.0::

	Throughput: 32798.74 [#/sec]
	Throughput: 58277.28 [#/sec]
	Throughput: 71234.85 [#/sec]
	Throughput: 90368.60 [#/sec]

ToRPC
-----
ToRPC 0.0.1 + python 2.7.10::

	Throughput: 21263.85 [#/sec]
	Throughput: 27327.71 [#/sec]
	Throughput: 30019.24 [#/sec]
	Throughput: 36413.75 [#/sec]

ToRPC 0.0.1 + PyPy4.0::

	Throughput: 39523.89 [#/sec]
	Throughput: 75819.55 [#/sec]
	Throughput: 90851.17 [#/sec]
	Throughput: 135085.80 [#/sec]

Golang
------
Golang 1.5.1 GOMAXPROCS=1::

	Throughput: 43039.40 [#/sec]
	Throughput: 83893.09 [#/sec]
	Throughput: 98686.66 [#/sec]
	Throughput: 133713.63 [#/sec]

C++epoll
--------
C++ epoll GCC 4.8.2::

	Throughput: 46555.83 [#/sec]
	Throughput: 96960.43 [#/sec]
	Throughput: 127246.68 [#/sec]
	Throughput: 190162.54 [#/sec]

