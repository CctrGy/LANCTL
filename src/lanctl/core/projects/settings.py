"""Transactional editing of VLF configuration documents."""

from __future__ import annotations

import ipaddress
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from lanctl.core.file_transaction import transactional_path_argument
from lanctl.core.projects import vlf
from lanctl.core.settings_catalog import validate_value

PROJECT_SETTINGS_ENTRIES = {
    "identity": "project.info",
    "lan": "lan/lanIdentifier.info",
    "network": "lan/network.config",
    "vlan": "lan/vlan.config",
}
PROJECT_EDITABLE = {
    "identity": {"name", "description", "author"},
    "lan": {"name", "description", "location", "company", "responsible"},
    "network": {
        "cidr",
        "gateway",
        "dns",
        "dhcpRange",
        "discovery",
        "scanProfile",
        "scanOrder",
        "saveMode",
        "saveIntervalMinutes",
    },
    "vlan": {"vlans", "nativeVlan", "managementVlan"},
}
NETWORK_PATHS = {
    "cidr": "network.range",
    "gateway": "network.gateway",
    "dns": "network.dnsServers",
    "dhcpRange": "network.dhcpRange",
    "discovery": "ip.discovery",
    "scanProfile": "ip.scanProfile",
    "scanOrder": "ip.scanOrder",
    "saveMode": "projects.saveMode",
    "saveIntervalMinutes": "projects.saveIntervalMinutes",
}


@transactional_path_argument("path", transform=lambda value: vlf._vlf_path(value))
def project_settings(path):
    source = vlf._existing_vlf(path)
    vlf.verify_project(source)
    with vlf._safe_archive(source) as archive:
        return {
            category: vlf._read_json_entry(archive, entry)
            for category, entry in PROJECT_SETTINGS_ENTRIES.items()
        }


@transactional_path_argument("path", transform=lambda value: vlf._vlf_path(value))
def update_project_setting(path, category, key, value):
    if key not in PROJECT_EDITABLE.get(category, set()):
        raise ValueError(f"Campo de proyecto de solo lectura: {category}.{key}")
    source = vlf._existing_vlf(path)
    with (
        vlf._VLF_WRITE_LOCK,
        tempfile.TemporaryDirectory(prefix="lanctl-vlf-settings-") as temporary,
    ):
        documents = project_settings(source)
        previous = documents[category][key]
        if category == "network":
            # Null DHCP/range fields still have a known schema type.
            defaults = {
                "cidr": "",
                "gateway": "",
                "dns": [],
                "dhcpRange": None,
                "discovery": "hybrid",
                "scanProfile": "normal",
                "scanOrder": "ascending",
                "saveMode": "manual",
                "saveIntervalMinutes": 5.0,
            }
            value = validate_value(NETWORK_PATHS[key], value, defaults[key])
        elif category == "vlan":
            if (
                key in {"nativeVlan", "managementVlan"}
                and value is not None
                and (type(value) is not int or not 1 <= value <= 4094)
            ):
                raise ValueError("El identificador VLAN debe estar entre 1 y 4094 o null")
            if key == "vlans" and (
                not isinstance(value, list) or any(not isinstance(item, dict) for item in value)
            ):
                raise ValueError("vlans requiere una lista de objetos VLAN")
        elif not isinstance(value, str):
            raise ValueError(f"{category}.{key} requiere texto")
        if category == "identity" and key == "name" and not value.strip():
            raise ValueError("El nombre del proyecto no puede estar vacío")
        if value == previous:
            return documents
        documents[category][key] = value
        if category == "network" and key == "cidr":
            network = ipaddress.ip_network(value, strict=False) if value else None
            documents[category].update(
                network=str(network.network_address) if network else "",
                netmask=str(network.netmask) if network else "",
                prefixLength=network.prefixlen if network else None,
            )
        root = Path(temporary)
        with vlf._safe_archive(source) as archive:
            archive.extractall(root)
        if category == "network":
            override_path = root / "lan/settings.override.json"
            overrides = (
                json.loads(override_path.read_text(encoding="utf-8"))
                if override_path.exists()
                else {"schemaVersion": 1, "network": {}}
            )
            if overrides.get("schemaVersion") != 1 or not isinstance(
                overrides.get("network"), dict
            ):
                raise ValueError("Configuración de proyecto incompatible")
            overrides["network"][key] = value
            if key == "cidr":
                for derived in ("network", "netmask", "prefixLength"):
                    overrides["network"][derived] = documents[category][derived]
            vlf._write_json(override_path, overrides)
        vlf._write_json(root / PROJECT_SETTINGS_ENTRIES[category], documents[category])
        info = documents["identity"]
        info["updated"] = datetime.now().astimezone().isoformat(timespec="seconds")
        info["contentHash"] = vlf._hash_directory(root, {"project.info", "meta/checksum"})
        vlf._write_json(root / "project.info", info)
        vlf._write_json(
            root / "meta/checksum",
            {
                "algorithm": "SHA-256",
                "hash": vlf._hash_directory(root, {"meta/checksum"}),
                "scope": "all files except meta/checksum",
                "contentHash": info["contentHash"],
            },
        )
        backup_directory = source.parent / ".lanctl-backups"
        backup_directory.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            source,
            backup_directory / f"{source.stem}-{datetime.now().astimezone():%Y%m%d-%H%M%S-%f}.vlf",
        )
        vlf._write_archive(root, source)
    if category == "network":
        from lanctl.core.config import load_config, update_config

        def apply(current):
            if current.get("activeProject") and vlf._vlf_path(current["activeProject"]) == source:
                current.update(project_network_overrides(source))

        active = load_config().get("activeProject")
        if active and vlf._vlf_path(active) == source:
            update_config(apply)
    return project_settings(source)


NETWORK_LEGACY_KEYS = {
    "cidr": "range",
    "gateway": "gateway",
    "dns": "dnsServers",
    "dhcpRange": "dhcpRange",
    "discovery": "discovery",
    "scanProfile": "scanProfile",
    "scanOrder": "scanOrder",
    "saveMode": "projectSaveMode",
    "saveIntervalMinutes": "projectSaveIntervalMinutes",
}


def project_network_overrides(path):
    """Return only explicit project preferences, never authentication or inventory."""
    with vlf._safe_archive(Path(path)) as archive:
        if "lan/settings.override.json" not in archive.namelist():
            return {}
        document = vlf._read_json_entry(archive, "lan/settings.override.json")
    if document.get("schemaVersion") != 1 or not isinstance(document.get("network"), dict):
        raise ValueError("Configuración de proyecto incompatible")
    from lanctl.core.config import DOCUMENT_DEFAULTS
    from lanctl.core.settings_catalog import leaves

    defaults = dict(leaves(DOCUMENT_DEFAULTS))
    return {
        NETWORK_LEGACY_KEYS[key]: validate_value(
            NETWORK_PATHS[key], value, defaults[NETWORK_PATHS[key]]
        )
        for key, value in document["network"].items()
        if key in NETWORK_LEGACY_KEYS
    }
