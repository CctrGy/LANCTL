"""Version 2 process RPC: bounded JSON, explicit types and activation identity."""

from __future__ import annotations

import json
import queue
import threading
import time
from dataclasses import fields, is_dataclass
from datetime import datetime

from lanctl.core.plugins import contracts
from lanctl.core.plugins.events import HookDecision
from lanctl.core.plugins.extensions import Extension
from lanctl.core.plugins.isolated_runtime import _MAX_MESSAGE_BYTES, _MessageReader

_TYPES = {
    cls.__name__: cls
    for cls in (
        contracts.FunctionResult,
        contracts.EventMetadata,
        contracts.LifecycleEvent,
        contracts.ProjectFileEvent,
        contracts.NetworkScanEvent,
        contracts.DeviceRemoteEvent,
        contracts.VaultOperationEvent,
        contracts.NetworkLabEvent,
        HookDecision,
        Extension,
    )
}
_ERRORS = {c.__name__: c for c in (PermissionError, ValueError, TypeError, RuntimeError)}


class RpcProtocolError(ValueError):
    """An invalid peer frame must retire the process, not just fail one call."""


def _invalid_constant(value):
    raise RpcProtocolError(f"constante JSON no permitida: {value}")


def _encode(value):
    # Every value is enveloped; a user dictionary cannot impersonate a type tag.
    if value is None or type(value) in (bool, int, float, str):
        return ["value", value]
    if isinstance(value, datetime):
        return ["datetime", value.isoformat()]
    if isinstance(value, (list, tuple)):
        return ["list", [_encode(item) for item in value]]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return ["dict", {key: _encode(item) for key, item in value.items()}]
    if is_dataclass(value) and _TYPES.get(type(value).__name__) is type(value):
        return [
            type(value).__name__,
            {f.name: _encode(getattr(value, f.name)) for f in fields(value)},
        ]
    raise TypeError("tipo no transportable por el contrato RPC v2")


def _decode(value, depth=0):
    if depth > 32 or not isinstance(value, list) or len(value) != 2:
        raise RpcProtocolError("valor RPC v2 no válido")
    tag, body = value
    if tag == "value" and (body is None or type(body) in (bool, int, float, str)):
        return body
    if tag == "datetime" and isinstance(body, str):
        try:
            return datetime.fromisoformat(body)
        except ValueError as error:
            raise RpcProtocolError("fecha RPC v2 no válida") from error
    if tag == "list" and isinstance(body, list):
        return [_decode(item, depth + 1) for item in body]
    if isinstance(body, dict) and isinstance(tag, str):
        decoded = {key: _decode(item, depth + 1) for key, item in body.items()}
        if tag == "dict":
            return decoded
        if tag in _TYPES:
            try:
                return contracts.construct_contract(_TYPES[tag], decoded)
            except (TypeError, ValueError) as error:
                raise RpcProtocolError("campos RPC v2 no válidos") from error
    raise RpcProtocolError("tipo RPC v2 no permitido")


def _receive(connection, generation):
    try:
        message = json.loads(
            connection.recv_bytes(_MAX_MESSAGE_BYTES).decode("utf-8"),
            parse_constant=_invalid_constant,
        )
    except (UnicodeError, ValueError, RecursionError) as error:
        raise RpcProtocolError("frame RPC v2 no válido") from error
    if (
        not isinstance(message, dict)
        or set(message) != {"version", "generation", "id", "kind", "payload"}
        or type(message["version"]) is not int
        or message["version"] != 2
        or message["generation"] != generation
        or type(message["id"]) is not int
        or message["id"] < 0
        or message["kind"] not in ("call", "result", "state", "stop")
        or not isinstance(message["payload"], dict)
    ):
        raise RpcProtocolError("contrato o generación RPC v2 no válidos")
    return message


class RpcPeer:
    """One serialized conversation; nested API calls are pumped by the waiter.

    A bounded writer keeps a blocked pipe out of cancellation/timeout paths.
    No registry lock may be held while waiting for a remote callback.
    """

    def __init__(self, connection, generation, handler, *, timeout, max_calls, on_state=None):
        self.connection, self.generation, self.handler = connection, generation, handler
        self.timeout, self.max_calls = timeout, max_calls
        self.on_state = on_state or (lambda payload: None)
        self.stopped = threading.Event()
        self.lock = threading.RLock()
        self.reader = _MessageReader(connection, lambda pipe: _receive(pipe, generation))
        self.outbox = queue.Queue(maxsize=8)
        self.pending = {}
        self.sequence = self.received = self.depth = 0
        self.writer = threading.Thread(target=self._write, name="plugin RPC writer", daemon=True)
        self.writer.start()

    def _write(self):
        while not self.stopped.is_set():
            try:
                payload, finished, outcome = self.outbox.get(timeout=0.05)
            except queue.Empty:
                continue
            try:
                self.connection.send_bytes(payload)
            except (OSError, EOFError) as error:
                outcome.append(error)
            finally:
                finished.set()

    def _send(self, kind, identifier, payload):
        if self.stopped.is_set():
            raise PermissionError("runtime revocado o cerrado")
        frame = json.dumps(
            dict(version=2, generation=self.generation, id=identifier, kind=kind, payload=payload),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        if len(frame) > _MAX_MESSAGE_BYTES:
            raise ValueError("mensaje RPC v2 demasiado grande")
        finished, outcome = threading.Event(), []
        try:
            self.outbox.put_nowait((frame, finished, outcome))
        except queue.Full as error:
            raise RuntimeError("cola RPC v2 agotada") from error
        deadline = time.monotonic() + self.timeout
        while not finished.wait(0.02):
            if self.stopped.is_set():
                raise PermissionError("runtime revocado o cerrado")
            if time.monotonic() >= deadline:
                raise TimeoutError("timeout escribiendo RPC v2")
        if outcome:
            raise outcome[0]

    def state(self, state, **values):
        self._send("state", 0, dict(state=state, **values))

    def request(self, method, *args, **kwargs):
        deadline = time.monotonic() + self.timeout
        if not self.lock.acquire(timeout=self.timeout):
            raise TimeoutError("runtime ocupado; timeout RPC v2")
        try:
            if self.depth >= 8:
                raise RuntimeError("límite de llamadas RPC anidadas")
            self.depth += 1
            try:
                self.sequence += 1
                identifier = self.sequence
                self.pending[identifier] = None
                self._send(
                    "call",
                    identifier,
                    dict(method=method, args=_encode(args), kwargs=_encode(kwargs)),
                )
                while self.pending[identifier] is None:
                    if self.stopped.is_set():
                        raise PermissionError("runtime revocado o cerrado")
                    if time.monotonic() >= deadline:
                        raise TimeoutError("timeout esperando respuesta RPC v2")
                    self.pump(min(0.05, max(0, deadline - time.monotonic())))
                result = self.pending[identifier]
                if result.get("ok") is True and set(result) == {"ok", "value"}:
                    return _decode(result["value"])
                if (
                    result.get("ok") is False
                    and set(result) == {"ok", "error", "message"}
                    and isinstance(result["message"], str)
                    and isinstance(result["error"], str)
                ):
                    raise _ERRORS.get(result["error"], RuntimeError)(result["message"])
                raise RpcProtocolError("respuesta RPC v2 no válida")
            finally:
                self.depth -= 1
                self.pending.pop(locals().get("identifier"), None)
        finally:
            self.lock.release()

    def pump(self, timeout=0):
        with self.lock:
            if not self.reader.poll(timeout):
                return
            frame = self.reader.receive()
            kind, identifier, body = frame["kind"], frame["id"], frame["payload"]
            if kind == "stop" and identifier == 0 and not body:
                self.stopped.set()
                raise PermissionError("runtime revocado o cerrado")
            if kind == "state" and identifier == 0:
                self.on_state(body)
                return
            if kind == "result" and identifier in self.pending and self.pending[identifier] is None:
                self.pending[identifier] = body
                return
            if kind != "call" or identifier <= self.received or identifier > self.max_calls:
                raise RpcProtocolError("secuencia o presupuesto RPC v2 no válidos")
            self.received = identifier
            if set(body) != {"method", "args", "kwargs"} or not isinstance(body["method"], str):
                raise RpcProtocolError("llamada RPC v2 no válida")
            args, kwargs = _decode(body["args"]), _decode(body["kwargs"])
            if not isinstance(args, list) or not isinstance(kwargs, dict):
                raise RpcProtocolError("argumentos RPC v2 no válidos")
            try:
                value = _encode(self.handler(body["method"], args, kwargs))
                result = dict(ok=True, value=value)
            except Exception as error:  # noqa: BLE001 - explicit remote error envelope
                result = dict(ok=False, error=type(error).__name__, message=str(error)[:2048])
            self._send("result", identifier, result)

    def close(self):
        self.stopped.set()
        self.connection.close()
        self.reader.close()
        self.writer.join(0.2)
