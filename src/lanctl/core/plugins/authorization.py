"""Revocable API leases; legacy trusted code is not an OS security boundary."""

from __future__ import annotations

import threading
import weakref
from functools import wraps


class RuntimeAuthorizations:
    def __init__(self, manager):
        self.manager = weakref.ref(manager)
        self.leases = {}
        self.restart_required = set()
        self.pending = []
        self.cleanups = {}
        self.stopped = threading.Event()
        self.watcher = None
        self.depth = threading.local()

    def begin(self, plugin_id):
        previous = self.cleanups.get(plugin_id)
        if previous and (previous.ident is None or previous.is_alive()):
            raise RuntimeError("La desactivación anterior no terminó; reinicia LANCTL")
        self.cleanups.pop(plugin_id, None)
        self.leases[plugin_id] = object()

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
            result = handler(*args, **kwargs)
            # A call already in progress is not reported as authorized success
            # if its lease changed while external code was executing.
            self.check(plugin_id, lease, permission)
            return result

        return invoke

    def retire(self, plugin):
        plugin_id = plugin.manifest.plugin_id
        self.leases.pop(plugin_id, None)
        module, runtime = plugin.module, plugin.isolated_runtime
        plugin.module = plugin.isolated_runtime = None
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
                deactivate = getattr(module, "deactivate", None)
                if callable(deactivate):
                    deactivate()
            except Exception as error:  # noqa: BLE001 - external teardown
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
            thread.join(0.5)

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
