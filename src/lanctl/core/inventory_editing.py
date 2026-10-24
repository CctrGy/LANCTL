"""Shared inventory edits; interfaces retain their own commands and history."""

import hashlib
import json

from lanctl.core.file_transaction import locked_files


def editable_values(device):
    return {
        "alias": device.alias,
        "name": device.name,
        "description": device.description,
        "icon": device.icon_id,
        "cnf": device.cnf,
        "ip": device.ip,
        "idf": device.idf,
    }


def edit_revision(device):
    return hashlib.sha256(json.dumps(editable_values(device), sort_keys=True).encode()).hexdigest()


def require_revision(device, expected):
    if expected is not None and expected != edit_revision(device):
        raise ValueError(
            "El elemento cambió en otra sesión. Recarga y revisa los cambios antes de aplicar la edición."
        )


def edit_inventory_device(database, groups, selector, values, expected=None):
    if not isinstance(values, dict) or set(values) - {
        "alias",
        "name",
        "description",
        "cnf",
        "icon",
        "ip",
        "idf",
    }:
        raise ValueError("Campos de edición no válidos.")
    with locked_files((database.path, groups.path)):
        device = database.resolve(selector)
        require_revision(device, expected)
        before = editable_values(device)
        edits = [
            (key, str(value).strip())
            for key, value in values.items()
            if str(value).strip() != before[key]
        ]
        if edits:
            device = groups.edit_device_fields(device.device_id, edits)
        return device, before, edits
