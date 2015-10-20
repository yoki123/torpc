# ToRPC
ToRPC(Tornado + RPC) 是一个简介的基于Tornado IOLoop的异步TCP和双休RPC框架。ToRPC速度非常快（尤其是在PyPy环境下）和轻量级。

注意：现在ToRPC只在`CPython 2.7+` 和 `PyPy 1.5+`测试过。
## 示例
--------

### RPC 服务器
```python
from torpc import RPCServer

server = RPCServer(('127.0.0.1', 5000))


@server.service.register()
def echo(x):
    return x


server.start()
```

### RPC 客户端
```python
from torpc import RPCClient


def cb(f):
    print(f.result())

rc = RPCClient(('127.0.0.1', 5000))

future = rc.call('echo', 'hello world', callback=cb)
# future.add_done_callback(cb)
# 同样支持 tornado.gen.coroutine
```

更多请浏览 `examples` 文件夹。
