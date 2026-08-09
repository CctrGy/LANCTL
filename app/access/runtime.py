from __future__ import annotations

import threading
from pathlib import Path

from app.core.config import load_config
from app.core.paths import application_path

from .service import AccessService, access_process_running


class AccessRuntime:
    """Mantiene SSH/HTTPS habilitados dentro del proceso de servicio permanente."""

    def __init__(self, service=None, poll_interval=2.0):
        if service is None:
            config = load_config()
            service = AccessService(
                application_path(config["accessConfig"]),
                application_path(config["accessUsers"]),
            )
        self.service = service
        self.poll_interval = max(0.5, float(poll_interval))
        self.stop_event = threading.Event()
        self.thread = None
        self.instances = {}
        self.lock = threading.RLock()
        self.errors = {}

    @staticmethod
    def _file_version(value):
        if not value:
            return None
        try:
            stat = Path(value).stat()
            return str(Path(value)), stat.st_mtime_ns, stat.st_size
        except OSError:
            return str(value), None, None

    def _signature(self, protocol, settings):
        common = (settings.get("bind"), settings.get("port"), settings.get("cidr"))
        if protocol == "ssh":
            return (
                *common,
                bool(settings.get("passwordAuthentication")),
                self._file_version(settings.get("hostKey")),
            )
        return (
            *common,
            self._file_version(settings.get("certificate")),
            self._file_version(settings.get("privateKey")),
        )

    def _build(self, protocol, settings):
        if protocol == "ssh":
            from .ssh_server import SshAccessServer

            server = SshAccessServer(
                settings["bind"],
                settings["port"],
                settings["cidr"],
                settings["hostKey"],
                self.service.auth,
                self.service.authorization,
                settings.get("passwordAuthentication", False),
            )
            server.prepare()
            return server
        from .https_server import HttpsAccessServer

        return HttpsAccessServer(
            settings["bind"],
            settings["port"],
            settings["cidr"],
            settings["certificate"],
            settings["privateKey"],
            self.service.auth,
            self.service.authorization,
            self.status,
        )

    def status(self):
        result = self.service.status()
        with self.lock:
            for protocol, (_signature, _server, thread) in self.instances.items():
                result[protocol]["running"] = thread.is_alive()
                result[protocol]["runtime"] = "monitor-service"
            if self.errors:
                result["runtimeErrors"] = dict(self.errors)
        return result

    def _serve(self, protocol, server):
        try:
            server.serve_forever()
        # Esta frontera de hilo conserva el diagnóstico incluso ante fallos
        # inesperados del servidor remoto.
        except Exception as error:  # noqa: BLE001
            self.errors[protocol] = f"{type(error).__name__}: {error}"
            self.service._audit(f"access.{protocol}.runtime.failed", None, "error")

    def _stop_protocol(self, protocol):
        current = self.instances.pop(protocol, None)
        if not current:
            return
        _signature, server, thread = current
        server.stop()
        thread.join(3)

    def reconcile(self):
        config = self.service.config()
        with self.lock:
            for protocol in ("ssh", "https"):
                settings = config[protocol]
                signature = self._signature(protocol, settings)
                current = self.instances.get(protocol)
                wanted = bool(settings.get("enabled"))
                external = access_process_running(settings)
                if current and (
                    not wanted or external or current[0] != signature or not current[2].is_alive()
                ):
                    self._stop_protocol(protocol)
                    current = None
                if wanted and not external and current is None:
                    try:
                        server = self._build(protocol, settings)
                    except (OSError, RuntimeError, ValueError) as error:
                        self.errors[protocol] = f"{type(error).__name__}: {error}"
                        continue
                    thread = threading.Thread(
                        target=self._serve,
                        args=(protocol, server),
                        name=f"lanctl-access-{protocol}",
                        daemon=True,
                    )
                    self.instances[protocol] = (signature, server, thread)
                    self.errors.pop(protocol, None)
                    thread.start()
        return {name: item[2].is_alive() for name, item in self.instances.items()}

    def start(self):
        self.reconcile()
        if self.thread and self.thread.is_alive():
            return self
        self.stop_event.clear()
        self.thread = threading.Thread(
            target=self._supervise, name="lanctl-access-supervisor", daemon=True
        )
        self.thread.start()
        return self

    def _supervise(self):
        while not self.stop_event.wait(self.poll_interval):
            try:
                self.reconcile()
            except (OSError, RuntimeError, ValueError):
                continue

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(self.poll_interval + 1)
        with self.lock:
            for protocol in tuple(self.instances):
                self._stop_protocol(protocol)
