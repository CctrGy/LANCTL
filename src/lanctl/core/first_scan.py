"""One-shot request for a first-scan confirmation; never starts network probes."""

import json
import os
import subprocess
import sys
import time

from lanctl.core.config import load_config
from lanctl.core.coordination import principal_id
from lanctl.core.file_transaction import atomic_write_json, locked_file
from lanctl.core.paths import data_root


def _path():
    import hashlib

    owner = hashlib.sha256(principal_id().encode()).hexdigest()[:24]
    return data_root() / "runtime" / f"first-scan-{owner}.json"


def request_first_scan():
    path = _path()
    with locked_file(path):
        atomic_write_json(path, {"schemaVersion": 1, "requested": True, "created": time.time()})


def _requested(path):
    if not path.exists():
        return False
    value = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(value, dict)
        or type(value.get("schemaVersion")) is not int
        or value["schemaVersion"] != 1
        or type(value.get("requested")) is not bool
        or type(value.get("created")) not in (int, float)
    ):
        raise ValueError("solicitud de primer escaneo no válida")
    return value["requested"] and 0 <= time.time() - value["created"] < 86400


def consume_request():
    path = _path()
    with locked_file(path):
        requested = _requested(path)
        if requested:
            atomic_write_json(
                path, {"schemaVersion": 1, "requested": False, "created": time.time()}
            )
        return requested


def scan_choices():
    requested = _requested(_path())
    networks = []
    notice = "Selecciona interfaz y confirma el rango. Se usarán ICMP/ARP; DNS y descubridores externos se omiten al no garantizar el origen."
    if requested:
        from lanctl.core.errors import errors
        from lanctl.core.network_interfaces import ipv4_interfaces

        try:
            networks = ipv4_interfaces()
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            errors.from_exception(
                error,
                origin="LANCTL.FirstScan.Interfaces",
                code="FIRST_SCAN.INTERFACES.UNAVAILABLE",
                level=23,
                print_output=False,
            )
            notice = "No se pudieron obtener las interfaces locales. Reintenta antes de confirmar el escaneo."
    return {
        "networks": networks,
        "range": load_config().get("range") or "",
        "requested": requested,
        "interfaceSelectionAvailable": bool(networks),
        "routing": "selected-source" if networks else "unavailable",
        "notice": notice,
    }


def launch_installed_gui(*, first_scan=False):
    from lanctl.core.local_permissions import elevated
    from lanctl.core.paths import application_directory

    if elevated():
        raise PermissionError(
            "Abre LANIP desde la sesión del usuario normal; el instalador no pudo recuperar esa identidad"
        )
    if first_scan:
        request_first_scan()
    command = (
        [str(application_directory() / ("lanip.exe" if os.name == "nt" else "lanip"))]
        if getattr(sys, "frozen", False)
        else [sys.executable, str(application_directory() / "lanip.py")]
    )
    subprocess.Popen(
        [*command, "--gui"], creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    )
    return {"opened": True, "scanRequested": first_scan, "scanStarted": False}
