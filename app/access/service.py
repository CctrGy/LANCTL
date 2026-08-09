from __future__ import annotations

import json
from contextlib import suppress
from copy import deepcopy
from pathlib import Path

from app.core.file_transaction import atomic_write_json, locked_file, update_json
from app.core.history import HistoryEvent, HistoryService

from .auth import AuthenticationService, AuthorizationService
from .models import aware
from .network import port_available, validate_endpoint
from .store import AccessStore

DEFAULT_CONFIG = {
    "schemaVersion": 1,
    "ssh": {
        "enabled": False,
        "bind": None,
        "cidr": None,
        "port": 2222,
        "passwordAuthentication": False,
        "hostKey": None,
    },
    "https": {
        "enabled": False,
        "bind": None,
        "cidr": None,
        "port": 8443,
        "certificate": None,
        "privateKey": None,
    },
    "firewall": {"managed": False},
}


def access_process_running(settings):
    """Valida PID y tiempo de creacion para evitar reutilizaciones de PID."""
    pid = settings.get("processId")
    identity = settings.get("processIdentity")
    if not pid or not identity:
        return False
    try:
        from app.monitor.lifecycle import _process_identity

        return _process_identity(int(pid)) == identity
    except (OSError, ValueError):
        return False


class AccessService:
    def __init__(self, config_path, user_store):
        self.config_path = Path(config_path)
        self.store = AccessStore(user_store)
        self.auth = AuthenticationService(self.store, self._audit)
        self.authorization = AuthorizationService(self.store)

    @staticmethod
    def _merged(value):
        defaults = deepcopy(DEFAULT_CONFIG)
        return {
            **defaults,
            **value,
            "ssh": {**defaults["ssh"], **value.get("ssh", {})},
            "https": {**defaults["https"], **value.get("https", {})},
        }

    def config(self):
        if not self.config_path.exists():
            return deepcopy(DEFAULT_CONFIG)
        return self._merged(json.loads(self.config_path.read_text(encoding="utf-8")))

    def save_config(self, value):
        with locked_file(self.config_path):
            atomic_write_json(self.config_path, self._merged(value))

    def update_config(self, mutator):
        def operation(value):
            merged = self._merged(value)
            replacement = mutator(merged)
            return replacement if replacement is not None else merged

        value = update_json(
            self.config_path,
            lambda: deepcopy(DEFAULT_CONFIG),
            operation,
        )
        return self._merged(value)

    def initialize(self):
        if not self.config_path.exists():
            self.update_config(lambda value: value)
        if not self.store.path.exists():
            self.store.update(lambda value: None)
        self._audit("access.config.initialized", None, "success")
        return self.status()

    def configure(
        self,
        protocol,
        *,
        bind,
        cidr,
        port,
        password_authentication=None,
        interfaces=None,
    ):
        if protocol not in {"ssh", "https"}:
            raise ValueError("protocolo de acceso no valido")
        bind, cidr, port = validate_endpoint(bind, cidr, port, interfaces=interfaces)
        other = "https" if protocol == "ssh" else "ssh"

        def operation(config):
            if (
                config[other]["enabled"]
                and config[other]["bind"] == bind
                and config[other]["port"] == port
            ):
                raise ValueError("el puerto colisiona con el otro servicio remoto")
            config[protocol].update({"bind": bind, "cidr": cidr, "port": port})
            if protocol == "ssh" and password_authentication is not None:
                config[protocol]["passwordAuthentication"] = bool(password_authentication)

        config = self.update_config(operation)
        self._audit("access.config.changed", None, "success")
        return config[protocol]

    def enable(self, protocol):
        if protocol not in {"ssh", "https"}:
            raise ValueError("protocolo de acceso no valido")

        def operation(config):
            settings = config[protocol]
            validate_endpoint(settings["bind"], settings["cidr"], settings["port"])
            if protocol == "https" and (
                not settings.get("certificate")
                or not settings.get("privateKey")
                or not Path(settings["certificate"]).is_file()
                or not Path(settings["privateKey"]).is_file()
            ):
                raise RuntimeError("HTTPS requiere certificado TLS y clave privada validos")
            if protocol == "ssh" and (
                not settings.get("hostKey") or not Path(settings["hostKey"]).is_file()
            ):
                raise RuntimeError("SSH requiere una host key valida")
            if not port_available(settings["bind"], settings["port"]):
                raise RuntimeError("el puerto configurado no esta disponible")
            settings["enabled"] = True

        config = self.update_config(operation)
        self._audit(f"access.{protocol}.enabled", None, "success")
        return config[protocol]

    def disable(self, protocol):
        if protocol not in {"ssh", "https"}:
            raise ValueError("protocolo de acceso no valido")
        config = self.update_config(lambda value: value[protocol].update(enabled=False))
        self._audit(f"access.{protocol}.disabled", None, "success")
        return config[protocol]

    def status(self):
        config = self.config()
        access_data = self.store.load()
        current = self.auth.clock()
        result = {
            "ssh": {k: v for k, v in config["ssh"].items() if k != "hostKey"},
            "https": {k: v for k, v in config["https"].items() if k != "privateKey"},
            "users": len(access_data["users"]),
            "sessions": sum(
                not item.get("revokedAt") and current < aware(item["expiresAt"])
                for item in access_data["sessions"]
            ),
        }
        for protocol in ("ssh", "https"):
            result[protocol]["running"] = access_process_running(config[protocol])
        return result

    def _audit(self, event_type, user, result, source_ip=""):
        # El historial es auxiliar: un fallo de disco no debe invalidar una
        # autenticación que ya ha terminado correctamente.
        with suppress(ValueError, OSError):
            HistoryService().write(
                HistoryEvent(
                    event_type,
                    "lanctl.access",
                    "local",
                    result,
                    event_type,
                    details={
                        "userId": user.userId if user else None,
                        "sourceIp": source_ip,
                    },
                )
            )
