# ToRPC

ToRPC(Tornado + RPC) is A simple Async TCP and Duplex RPC framework based on Tornado IOLoop. It's very fast and lightweight.
## Examples
--------

### RPC server
```python
service = Services()

@service.route()
def echo(x):
    return x
    
server = RPCServer(('127.0.0.1', 5000), service)
server.start()
```
See more in `examples`
