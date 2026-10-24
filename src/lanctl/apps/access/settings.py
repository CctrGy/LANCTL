"""Local remote-access settings: preflight before creating stores or keys."""

import json

from lanctl.core.paths import application_path, scoped_data_paths


def validate_remote_settings(previous, candidate):
    from types import SimpleNamespace

    from lanctl.core.config import DOCUMENT_DEFAULTS, canonical_config
    from lanctl.core.local_permissions import require_admin
    from lanctl.core.settings_catalog import validate_value

    from . import runtime_state as state
    from .network import port_available, validate_endpoint
    from .service import AccessService

    values = canonical_config(candidate)["access"]["remote"]
    for key, default in DOCUMENT_DEFAULTS["access"]["remote"].items():
        validate_value(f"access.remote.{key}", values[key], default)
    if values["backend"] == "service" or (
        previous.get("remoteAccessBackend") == "service" and previous.get("remoteAccessEnabled")
    ):
        require_admin()
    bind, cidr, port = values["bind"].strip(), values["cidr"].strip(), values["port"]
    if values["enabled"] or bind or cidr:
        if not bind or not cidr:
            raise ValueError("Remote Access requiere conjuntamente IP de enlace y CIDR permitido")
        validate_endpoint(bind, cidr, port)
    owners = []
    sources = (previous, candidate) if previous.get("remoteAccessEnabled") else (candidate,)
    for source in sources:
        with scoped_data_paths(source["remoteAccessBackend"]):
            source_path = application_path(source["accessConfig"])
        source_config = AccessService._merged(
            json.loads(source_path.read_text(encoding="utf-8")) if source_path.exists() else {}
        )
        ssh = source_config["ssh"]
        record = state._read(SimpleNamespace(config_path=source_path), "ssh")
        if state._alive(ssh) or (record.get("state") == "running" and state._alive(record)):
            if record.get("backend") == "service":
                require_admin()
            owners.append((ssh["bind"], ssh["port"]))
        elif ssh["enabled"] and ssh["bind"] and not port_available(ssh["bind"], ssh["port"]):
            raise RuntimeError("Listener remoto activo sin propietario verificable; no se modifica")
    with scoped_data_paths(values["backend"]):
        path = application_path(candidate["accessConfig"])
        # Do not construct AccessStore here: its legacy migration writes files.
        stored = AccessService._merged(
            json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        )
        other = stored["https"]
        if bind and other["enabled"] and other["bind"] == bind and other["port"] == port:
            raise ValueError("El puerto colisiona con el otro servicio remoto")
        current = stored["ssh"]
        if values["enabled"]:
            host_key = current.get("hostKey")
            if host_key and not application_path(host_key).is_file():
                raise ValueError("SSH requiere una host key válida")
            owns_port = (bind, port) in owners
            if not owns_port and not port_available(bind, port):
                raise ValueError("El puerto configurado no está disponible")


def apply_remote_settings(config):
    from lanctl.core.config import load_config

    from .settings_lifecycle import remote_settings_transaction

    with remote_settings_transaction(load_config(), config, persist_program=False):
        pass
