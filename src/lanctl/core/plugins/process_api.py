"""Explicit, transportable subset of the plugin API for isolated RPC v2."""

from types import SimpleNamespace

from lanctl.core.plugins.authorization import _PROCESS_RPC
from lanctl.core.plugins.contracts import FunctionResult


class ProcessPluginApi:
    def __init__(self, peer, plugin_id):
        self._peer, self.plugin_id = peer, plugin_id
        self._callbacks = {}
        self._sequence = 0
        self.events = SimpleNamespace(subscribe=self._subscribe, emit=self._method("events.emit"))
        self.functions = SimpleNamespace(
            register=self._register, call=self._method("functions.call")
        )
        self.extensions = SimpleNamespace(register=self._method("extensions.register"))
        self.inventory = SimpleNamespace(list=self._method("inventory.list"))

    def _method(self, name):
        return lambda *args, **kwargs: self._peer.request(name, *args, **kwargs)

    def require(self, permission):
        return self._peer.request("require", permission)

    @property
    def settings(self):
        return self._peer.request("settings")

    def log(self, action, target="-", result="OK", detail=""):
        return self._peer.request("log", action, target, result, detail)

    def _callback(self, handler):
        if not callable(handler):
            raise TypeError("el callback debe ser ejecutable")
        self._sequence += 1
        identifier = str(self._sequence)
        self._callbacks[identifier] = handler
        return identifier

    def _subscribe(self, event_id, handler, *, version=1, priority=100):
        identifier = self._callback(handler)
        try:
            return self._peer.request(
                "events.subscribe", event_id, identifier, version=version, priority=priority
            )
        except Exception:
            self._callbacks.pop(identifier, None)
            raise

    def _register(self, function_id, handler, return_contract):
        if return_contract is not FunctionResult:
            raise TypeError("RPC v2 admite el contrato FunctionResult para funciones")
        identifier = self._callback(handler)
        try:
            return self._peer.request("functions.register", function_id, identifier)
        except Exception:
            self._callbacks.pop(identifier, None)
            raise

    def _invoke(self, method, args, kwargs):
        if method != "invoke" or not args or not isinstance(args[0], str):
            raise PermissionError("operación del host no permitida por RPC v2")
        try:
            callback = self._callbacks[args[0]]
        except KeyError as error:
            raise ValueError("callback RPC v2 desconocido") from error
        return callback(*args[1:], **kwargs)


def dispatch(runtime, method, args, kwargs):
    token = _PROCESS_RPC.set(True)
    try:
        return _dispatch(runtime, method, args, kwargs)
    finally:
        _PROCESS_RPC.reset(token)


def _dispatch(runtime, method, args, kwargs):
    api = runtime.api
    api._check_current()
    allowed = {
        "require": api.require,
        "settings": lambda: api.settings,
        "log": api.log,
        "functions.call": api.functions.call,
        "events.emit": api.events.emit,
        "extensions.register": api.extensions.register,
        "inventory.list": lambda: [device.to_dict() for device in api.inventory.list()],
    }
    if method in ("functions.register", "events.subscribe"):
        if len(args) != 2 or not all(isinstance(value, str) for value in args):
            raise ValueError("registro de callback RPC v2 no válido")
        name, identifier = args

        def callback(*a, **kw):
            return runtime.invoke(identifier, *a, **kw)

        if method == "functions.register":
            if kwargs:
                raise ValueError("opciones de función RPC v2 no válidas")
            result = api.functions.register(name, callback, FunctionResult)
        else:
            result = api.events.subscribe(name, callback, **kwargs)
    else:
        if method not in allowed:
            raise PermissionError("operación no permitida por el contrato RPC v2")
        result = allowed[method](*args, **kwargs)
    api._check_current()
    return result
