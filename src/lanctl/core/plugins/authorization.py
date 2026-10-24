"""Revocable API leases; legacy trusted code is not an OS security boundary."""

from __future__ import annotations

import threading
import weakref
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps

_PROCESS_RPC = ContextVar("plugin_process_rpc", default=False)


class RuntimeAuthorizations:
    def __init__(self, manager):
        self.manager = weakref.ref(manager)
        self.leases = {}
        self.restart_required = set()
        self.pending = []
        self.cleanups = {}
        self.retiring = {}
        self.cleanup_errors = {}
        self.terminated = {}
        self.stopped = threading.Event()
        self.watcher = None
        self.depth = threading.local()

    @contextmanager
    def transaction(self):
        from lanctl.core.file_transaction import locked_file

        manager = self.manager()
        if manager is None:
            raise PermissionError("El runtime del plugin ya no está disponible")
        self.depth.value = getattr(self.depth, "value", 0) + 1
        try:
            with manager._lock, locked_file(manager.registry_path):
                yield
        finally:
            self.depth.value -= 1
            if not self.depth.value:
                self.drain()

    def begin(self, plugin_id):
        self.ensure_stopped(plugin_id)
        self.cleanups.pop(plugin_id, None)
        self.cleanup_errors.pop(plugin_id, None)
        self.terminated.pop(plugin_id, None)
        self.leases[plugin_id] = object()

    def ensure_stopped(self, plugin_id):
        previous = self.cleanups.get(plugin_id)
        if (
            (previous and (previous.ident is None or previous.is_alive()))
            or plugin_id in self.retiring
            or plugin_id in self.cleanup_errors
        ):
            raise RuntimeError("La desactivación anterior no terminó; reinicia LANCTL")

    def check(self, plugin_id, lease, permission=None):
        manager = self.manager()
        if manager is None:
            raise PermissionError("El runtime del plugin ya no está disponible")
        # Never use a cached permission set as authority for an operation.
        manager.refresh_authorizations()
        with manager._lock:
            if lease is None or self.leases.get(plugin_id) is not lease:
                raise PermissionError(
                    f"La autorización de {plugin_id} fue revocada; recarga el plugin"
                )
            plugin = manager.get(plugin_id)
            if permission is not None and permission not in plugin.granted:
                raise PermissionError(f"{plugin_id} no tiene el permiso {permission}")

    def guarded(self, plugin_id, lease, handler, permission):
        @wraps(handler)
        def invoke(*args, **kwargs):
            self.check(plugin_id, lease, permission)
            if _PROCESS_RPC.get():
                manager = self.manager()
                plugin = manager.get(plugin_id)
                if (
                    plugin.manifest.runtime != "isolated"
                    or plugin.manifest.raw.get("runtimeApiVersion", 1) != 2
                ):
                    raise PermissionError(
                        "RPC v2 no puede ejecutar callbacks de un runtime heredado"
                    )
            result = handler(*args, **kwargs)
            # A call already in progress is not reported as authorized success
            # if its lease changed while external code was executing.
            self.check(plugin_id, lease, permission)
            return result

        return invoke

    def retire(self, plugin):
        plugin_id = plugin.manifest.plugin_id
        self.leases.pop(plugin_id, None)
        module = plugin.module
        runtime = plugin.isolated_runtime or self.retiring.get(plugin_id)
        plugin.module = plugin.isolated_runtime = None
        previous = self.cleanups.get(plugin_id)
        if previous and (previous.ident is None or previous.is_alive()):
            return
        if runtime is not None:
            self.retiring[plugin_id] = runtime
        if module is not None:
            # Even a successful deactivate() cannot prove that arbitrary
            # native threads started by legacy trusted code have stopped.
            plugin.restart_required = True
            self.restart_required.add(plugin_id)
        if module is None and runtime is None:
            return

        def cleanup():
            try:
                if runtime is not None:
                    runtime.stop()
                    process = runtime.process
                    if process is not None and process.is_alive():
                        raise RuntimeError("el proceso del plugin sigue activo tras detenerlo")
                    manager = self.manager()
                    if manager is not None:
                        with manager._lock:
                            self.retiring.pop(plugin_id, None)
                            self.cleanup_errors.pop(plugin_id, None)
                            self.terminated[plugin_id] = True
                deactivate = getattr(module, "deactivate", None)
                if callable(deactivate):
                    deactivate()
            except Exception as error:  # noqa: BLE001 - external teardown
                manager = self.manager()
                if manager is not None:
                    with manager._lock:
                        self.cleanup_errors[plugin_id] = str(error)
                from lanctl.core.errors import errors

                errors.from_exception(
                    error,
                    origin="LANCTL.Plugin.Deactivation",
                    code="PLUGIN.DEACTIVATION.DEGRADED",
                    level=14,
                    details={"pluginId": plugin_id},
                    print_output=False,
                )

        # Reserve the cleanup while the manager lock is still held. Another
        # thread must not activate a new generation before this one starts.
        thread = threading.Thread(target=cleanup, name=f"plugin-close-{plugin_id}", daemon=True)
        thread.process_cleanup = runtime is not None
        self.cleanups[plugin_id] = thread
        self.pending.append(thread)

    def drain(self):
        manager = self.manager()
        if manager is None:
            return
        with manager._lock:
            pending, self.pending = self.pending, []
        for thread in pending:
            thread.start()
            thread.join(2 if thread.process_cleanup else 0.5)

    def start_watch(self):
        if self.watcher and self.watcher.is_alive():
            return
        self.stopped.clear()
        reference = self.manager
        stopped = self.stopped

        def watch():
            while not stopped.wait(0.5):
                manager = reference()
                if manager is None:
                    return
                try:
                    manager.refresh_authorizations()
                except (OSError, ValueError, RuntimeError) as error:
                    from lanctl.core.errors import errors

                    errors.from_exception(
                        error,
                        origin="LANCTL.Plugin.Authorization.Refresh",
                        code="PLUGIN.AUTHORIZATION.REFRESH_FAILED",
                        level=43,
                        print_output=False,
                        once_key="plugin.authorization.refresh",
                    )
                finally:
                    manager = None

        self.watcher = threading.Thread(target=watch, name="plugin-authorizations", daemon=True)
        self.watcher.start()

    def stop_watch(self):
        self.stopped.set()
        if self.watcher and self.watcher is not threading.current_thread():
            self.watcher.join(1)
