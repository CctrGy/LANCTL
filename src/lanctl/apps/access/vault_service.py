"""Credential transport and repair, independent of presentation."""

from __future__ import annotations

from copy import deepcopy

from lanctl.core.credentials import CredentialStore
from lanctl.core.file_transaction import locked_files


def transfer(source: CredentialStore, target: CredentialStore, *, move=False) -> int:
    """Copy first, verify, then optionally remove. Conflicts never overwrite secrets."""
    if source.path.resolve() == target.path.resolve():
        raise ValueError("origen y destino deben ser diferentes")
    with locked_files([source.path, target.path]):
        incoming, current = source._load(), target._load()
        merged = deepcopy(current)
        for identifier, entry in incoming["entries"].items():
            if identifier in merged["entries"] and merged["entries"][identifier] != entry:
                raise ValueError(f"conflicto de credencial: {identifier}; destino intacto")
            merged["entries"][identifier] = entry
        target._save(merged)
        if target._load() != merged:
            raise OSError("la verificación del destino ha fallado; origen conservado")
        if move:
            source._save({"version": 1, "entries": {}})
        return len(incoming["entries"])


def audit_bindings(manager, *, repair=False):
    with locked_files([manager.store.path, manager.database.path]):
        entries = manager.store._load()["entries"]
        devices = {device.device_id: device for device in manager.database.load()}
        result = {"unbound": [], "missingSecrets": [], "unknownDevices": [], "repaired": 0}
        for identifier, entry in entries.items():
            device = devices.get(entry["deviceId"])
            if device is None:
                result["unknownDevices"].append(identifier)
            elif device.credentials.get(entry["protocol"]) != identifier:
                result["unbound"].append(identifier)
                if repair and not device.credentials.get(entry["protocol"]):
                    manager.database.bind_credential(
                        device.device_id, entry["protocol"], identifier
                    )
                    result["repaired"] += 1
        for device in devices.values():
            for reference in device.credentials.values():
                if reference not in entries:
                    result["missingSecrets"].append(reference)
        return result
