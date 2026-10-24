"""Cancelable process runtime; v1 and legacy trusted activation stay compatible."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import multiprocessing
import os
import threading
import time
import uuid
from contextlib import suppress
from pathlib import Path

from lanctl.core.plugins.isolated_runtime import (
    _RUNTIMES,
    IsolatedPluginRuntime,
    _apply_memory_limit,
    _install_security_policy,
    _watch_parent,
    _windows_memory_job,
)
from lanctl.core.plugins.process_api import ProcessPluginApi, dispatch
from lanctl.core.plugins.runtime_protocol import RpcPeer, RpcProtocolError


def _plugin_location(error, entry):
    root = Path(entry).resolve().parent
    location = {"file": Path(entry).name, "line": 0}
    trace = error.__traceback__
    while trace is not None:
        path = Path(trace.tb_frame.f_code.co_filename).resolve()
        if path.is_relative_to(root):
            location = {"file": path.relative_to(root).as_posix(), "line": trace.tb_lineno}
        trace = trace.tb_next
    return location


def _worker(connection, plugin_id, entry, generation, timeout, memory_mb, max_calls):
    _apply_memory_limit(memory_mb)
    _watch_parent()
    api = None
    peer = RpcPeer(
        connection,
        generation,
        lambda *args: api._invoke(*args),
        timeout=timeout,
        max_calls=max_calls,
    )
    api = ProcessPluginApi(peer, plugin_id)
    module = None
    phase = "Load"
    try:
        _install_security_policy(
            connection,
            Path(entry).resolve().parent,
            report=lambda event, detail: peer.state(
                "error",
                error="PermissionError",
                message=f"política aislada: {event}: {detail}",
                phase=phase,
                file=Path(entry).name,
                line=0,
            ),
        )
        peer.state("booted", pid=os.getpid())
        loader = importlib.machinery.SourceFileLoader("lanctl_process_plugin", entry)
        spec = importlib.util.spec_from_loader(loader.name, loader)
        if spec is None:
            raise ImportError("no se pudo cargar el plugin de proceso")
        module = importlib.util.module_from_spec(spec)
        loader.exec_module(module)
        activate = getattr(module, "activate", None)
        if not callable(activate):
            raise ValueError("main.exec debe definir activate(api)")
        phase = "Activate"
        activate(api)
        peer.state("ready", pid=os.getpid())
        phase = "Run"
        while not peer.stopped.is_set():
            peer.pump(0.05)
    except Exception as error:  # noqa: BLE001 - plugin boundary
        if not peer.stopped.is_set():
            with suppress(OSError, EOFError, ValueError, RuntimeError):
                peer.state(
                    "error",
                    error=type(error).__name__,
                    message=str(error)[:2048],
                    phase=phase,
                    **_plugin_location(error, entry),
                )
    finally:
        # Revoked teardown cannot call the Core. Non-cooperating code is killed
        # by the host deadline, including non-daemon Python threads.
        peer.stopped.set()
        deactivate = getattr(module, "deactivate", None)
        if callable(deactivate):
            with suppress(Exception):
                deactivate()
        peer.close()


class ProcessPluginRuntime(IsolatedPluginRuntime):
    def bind_api(self, api):
        self.api = api
        return self

    def start(self):
        if not hasattr(self, "api"):
            raise ValueError("falta la autorización del host para RPC v2")
        self.generation = uuid.uuid4().hex
        self._stopping = threading.Event()
        self._stop_lock = threading.Lock()
        self._booted = self._ready = False
        self.termination_confirmed = False
        context = multiprocessing.get_context("spawn")
        parent, child = context.Pipe()
        self.process = context.Process(
            target=_worker,
            args=(
                child,
                self.plugin_id,
                str(self.entry),
                self.generation,
                self.timeout,
                self.memory_mb,
                self.max_calls,
            ),
            name=f"LANCTL plugin v2 {self.plugin_id}",
            daemon=True,
        )
        self._connection = parent
        self._peer = RpcPeer(
            parent,
            self.generation,
            lambda *a: dispatch(self, *a),
            timeout=self.timeout,
            max_calls=self.max_calls,
            on_state=self._state,
        )
        try:
            self.process.start()
            child.close()
            _RUNTIMES.add(self)
            self._job_handle = _windows_memory_job(self.process.pid, self.memory_mb)
            deadline = time.monotonic() + max(5.0, self.timeout)
            while not self._ready:
                if not self.process.is_alive():
                    raise RuntimeError("el proceso RPC v2 terminó durante la activación")
                if time.monotonic() >= deadline:
                    raise TimeoutError("timeout activando el plugin RPC v2")
                previous = self._booted
                self._peer.pump(0.05)
                if self._booted and not previous:
                    deadline = time.monotonic() + self.timeout + 0.25
            self._watchdog_thread = threading.Thread(
                target=self._watch_runtime, name=f"plugin RPC {self.plugin_id}", daemon=True
            )
            self._watchdog_thread.start()
            return self
        except Exception:
            child.close()
            self.stop()
            raise

    def _state(self, body):
        if (
            body.get("state") == "error"
            and set(body) == {"state", "error", "message", "phase", "file", "line"}
            and isinstance(body["message"], str)
            and body["phase"] in ("Load", "Activate", "Run")
            and isinstance(body["file"], str)
            and type(body["line"]) is int
            and body["line"] >= 0
        ):
            cls = PermissionError if body["error"] == "PermissionError" else RuntimeError
            error = cls(body["message"])
            self._record_failure(
                error, body["phase"], location={"file": body["file"], "line": body["line"]}
            )
            raise error
        if set(body) != {"state", "pid"} or type(body["pid"]) is not int or body["pid"] != self.pid:
            raise ValueError("handshake RPC v2 no válido")
        if body["state"] == "booted" and not self._booted:
            self._booted = True
        elif body["state"] == "ready" and self._booted and not self._ready:
            self._ready = True
        else:
            raise ValueError("estado RPC v2 fuera de secuencia")

    def invoke(self, identifier, *args, **kwargs):
        self.api._check_current()
        if getattr(self.api._authorization.depth, "value", 0):
            # An activation holds registry locks. Re-entering remote code here
            # could wait on another process that needs those same locks.
            raise RuntimeError("callback RPC v2 no permitido durante una mutación del registro")
        try:
            result = self._peer.request("invoke", identifier, *args, **kwargs)
            self.api._check_current()
            return result
        except (TimeoutError, OSError, EOFError, RpcProtocolError) as error:
            self._record_failure(error, "Call")
            self.stop()
            raise

    def _record_failure(self, error, phase, *, location=None):
        from lanctl.core.errors import errors

        errors.from_exception(
            error,
            origin=f"Plugin.{self.plugin_id}.Runtime.{phase}",
            code="PLUGIN.RUNTIME.PROCESS_FAILED",
            level=43,
            details={
                "pluginId": self.plugin_id,
                "generation": self.generation,
                "location": location,
            },
            print_output=False,
        )

    def _watch_runtime(self):
        next_authorization = 0
        while not self._stopping.wait(0.05):
            process = self.process
            if process is None or not process.is_alive():
                return
            try:
                if time.monotonic() >= next_authorization:
                    self.api._check_current()
                    next_authorization = time.monotonic() + 0.5
                if self._peer.lock.acquire(blocking=False):
                    try:
                        self._peer.pump()
                    finally:
                        self._peer.lock.release()
                if (
                    self._job_handle is None
                    and self._resident_memory() > self.memory_mb * 1024 * 1024
                ):
                    raise RuntimeError("límite de memoria RPC v2 superado")
            except Exception as error:  # noqa: BLE001 - runtime boundary
                if not self._stopping.is_set():
                    self._record_failure(error, "Watch")
                    self.audit(self.plugin_id, "PROCESS RUNTIME", "RPC v2", "ERROR", str(error))
                    self.stop()
                return

    def stop(self):
        if not hasattr(self, "_stop_lock"):
            return
        with self._stop_lock:
            process = self.process
            if process is None:
                return
            self._stopping.set()
            # No RPC/registry lock is acquired: a blocked callback or sender
            # must never prevent cancellation. Process death is the proof.
            self._peer.stopped.set()
            if process.pid is not None:
                if process.is_alive():
                    process.terminate()
                process.join(0.5)
                if process.is_alive():
                    process.kill()
                    process.join(0.5)
                if process.is_alive():
                    raise RuntimeError("no se ha confirmado la terminación del plugin")
            self.termination_confirmed = True
            self._peer.close()
            self.process = self._connection = None
            self._close_job()
            _RUNTIMES.discard(self)
