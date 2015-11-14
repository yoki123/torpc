ToRPC
=====

ToRPC(Tornado + RPC) 是一个的基于Tornado
IOLoop的异步TCP和双向通信的RPC的Python实现。ToRPC非常轻量级，性能优秀（尤其是在PyPy环境下）。

注意：目前为止，ToRPC只在\ ``CPython 2.7+`` 和 ``PyPy 2.5+``\ 上测试过。

示例
-------

RPC 服务器
~~~~~~~~~~

.. code:: python

    from tornado import ioloop
    from torpc import RPCServer
    server = RPCServer(('127.0.0.1', 5000))

    @server.service.register()
    def echo(x):
        return x

    server.start()
    ioloop.IOLoop.instance().start()

RPC 客户端
~~~~~~~~~~

.. code:: python

    from tornado import ioloop, gen
    from torpc import RPCClient

    def result_callback(f):
        print(f.result())

    @gen.coroutine
    def using_gen_style():
        want_to_say = 'way to explore'
        ret = yield rc.call('echo', want_to_say)
        assert ret == want_to_say
        print('gen_style complete')

    rc = RPCClient(('127.0.0.1', 5000))
    rc.call('echo', 'hello world', callback=result_callback)
    future = rc.call('echo', 'code for fun')
    future.add_done_callback(result_callback)
    using_gen_style()
    ioloop.IOLoop.instance().start()

更多请浏览\ `examples`_\ 。

Performance
~~~~~~~~~~~

系统: CentOS 6.6 x64
处理器: Intel i5-3470 3.20GHz
内存: 8 GB 1600 MHz DDR3
Python: 2.7.10
PyPy: 4.0.0

+----------------------+---------------------+---------------+
| environment          | call coroutine(qps) | callback(qps) |
+======================+=====================+===============+
| Python(with timeout) | 9842                | 11614         |
+----------------------+---------------------+---------------+
| Python               | 13192               | 16638         |
+----------------------+---------------------+---------------+
| PyPy(with timeout)   | 40486               | 41225         |
+----------------------+---------------------+---------------+
| PyPy                 | 53252               | 59151         |
+----------------------+---------------------+---------------+
| PyPy(unix domain)    | 67100               | 74362         |
+----------------------+---------------------+---------------+

这个基准测试中，Python循环10w次，PyPy循环50w次，然后运行3次, 结果在
`gist:benchmark\_result.txt`_

文档
~~~~

`English`_

.. _examples: https://github.com/yoki123/torpc/tree/master/examples
.. _`gist:benchmark\_result.txt`: https://gist.github.com/yoki123/c6f8a9c4f375f61359e2
.. _English: https://github.com/yoki123/torpc/blob/master/README.rst