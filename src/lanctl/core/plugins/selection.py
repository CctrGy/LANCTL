"""Persistent bootstrap selection; omission never grants or revokes runtime permissions."""

import json
from pathlib import Path

from lanctl.core.file_transaction import atomic_write_json, locked_file

OPTIONAL_PLUGINS = (
    "lanctl.example.network-summary",
    "lanctl.analysis.mac-vendor",
    "lanctl.discovery.mdns-ssdp",
    "lanctl.discovery.windows-smb",
    "lanctl.network.wol",
    "lanctl.lab.network-emulator",
)


def selected_plugins(root):
    path = Path(root) / "bundled-selection.json"
    if not path.exists():
        return set(OPTIONAL_PLUGINS)  # Compatible with existing installations.
    document = json.loads(path.read_text(encoding="utf-8"))
    if (
        not isinstance(document, dict)
        or type(document.get("schemaVersion")) is not int
        or document["schemaVersion"] != 1
    ):
        raise ValueError("selección de plugins no compatible")
    selected = document.get("selected")
    if (
        not isinstance(selected, list)
        or not all(isinstance(x, str) and x in OPTIONAL_PLUGINS for x in selected)
        or len(selected) != len(set(selected))
    ):
        raise ValueError("selección de plugins no válida")
    return set(selected)


def initialize_selection(root, selected):
    if not isinstance(selected, (list, tuple, set)) or not all(
        isinstance(x, str) and x in OPTIONAL_PLUGINS for x in selected
    ):
        raise ValueError("plugins opcionales desconocidos")
    path = Path(root) / "bundled-selection.json"
    with locked_file(path):
        if path.exists():
            return selected_plugins(root)
        atomic_write_json(path, {"schemaVersion": 1, "selected": sorted(set(selected))})
    return set(selected)
