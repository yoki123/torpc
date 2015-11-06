# ToRPC

ToRPC(Tornado + RPC) 是一个简介的基于Tornado IOLoop的异步TCP和双向RPC框架。ToRPC速度非常快（尤其是在PyPy环境下）和轻量级。

注意：现在ToRPC只在`CPython 2.7+` 和 `PyPy 1.5+`测试过。

## 示例
--------

### RPC 服务器
```python
from tornado import ioloop

from torpc import RPCServer

server = RPCServer(('127.0.0.1', 5000))


@server.service.register()
def echo(x):
    return x


server.start()

ioloop.IOLoop.instance().start()
```

### RPC 客户端
```python
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
```

更多请浏览 `examples` 文件夹。


### 性能

系统: CentOS 6.6 x64

处理器: Intel i5-3470 3.20GHz

内存: 8 GB 1600 MHz DDR3

environment | call coroutine(qps) | callback(qps)
------------|---------------------|-------------------
Python2.7   | 39645               | 42346
PyPy4.0     | 10162               | 12048

### 文档
[English](https://github.com/yoki123/torpc/blob/master/README.md)