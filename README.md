# ToRPC

ToRPC(Tornado + RPC) is A simple Async TCP and Duplex RPC framework based on Tornado IOLoop. It's very fast(especially on PyPy) and lightweight.

Notice: ToRPC was only tested on `CPython 2.7+` and `PyPy 2.5+` now.

## Examples
--------

### RPC server
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

### RPC client
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

See more in [examples](https://github.com/yoki123/torpc/tree/master/examples).

### Performance

OS: CentOS 6.6 x64<br/>
CPU: Intel i5-3470 3.20GHz<br/>
Memory: 8 GB 1600 MHz DDR3

environment | call coroutine(qps) | callback(qps)
------------|---------------------|-------------------
Python2.7   | 10162               | 12048
PyPy4.0     | 39645               | 42346

### Document
[中文](https://github.com/yoki123/torpc/blob/master/README-zh.md)