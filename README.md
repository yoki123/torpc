# ToRPC

ToRPC(Tornado + RPC) is A simple Async TCP and Duplex RPC framework based on Tornado IOLoop. It's very fast(especially on PyPy) and lightweight.

Notice: ToRPC was only tested on `CPython 2.7+` and `PyPy 1.5+` now.

## Examples
--------

### RPC server
```python
from torpc import RPCServer

server = RPCServer(('127.0.0.1', 5000))


@server.service.register()
def echo(x):
    return x


server.start()
```
See more in `examples` dir.
