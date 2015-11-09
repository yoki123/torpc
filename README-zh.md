# ToRPC

ToRPC(Tornado + RPC) 是一个的基于Tornado IOLoop的异步TCP和双向通信的RPC的Python实现。ToRPC非常轻量级，性能优秀（尤其是在PyPy环境下）。

注意：目前为止，ToRPC只在`CPython 2.7+` 和 `PyPy 2.5+`上测试过。

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

更多请浏览[examples](https://github.com/yoki123/torpc/tree/master/examples)。

### 性能

系统: CentOS 6.6 x64<br/>
处理器: Intel i5-3470 3.20GHz<br/>
内存: 8 GB 1600 MHz DDR3

<table>
<tr>
    <td>environment</td>
    <td>call coroutine(qps)</td>
    <td>callback(qps)</td>
</tr>
<tr>
    <td>Python2.7.10</td>
    <td>9842</td>
    <td>11614</td>
</tr>
<tr>
    <td>PyPy4.0.0(50W loops)</td>
    <td>40486</td>
    <td>41225</td>
</tr>
</table>

### 文档
[English](https://github.com/yoki123/torpc/blob/master/README.md)