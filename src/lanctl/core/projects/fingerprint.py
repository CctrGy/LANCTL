from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Any


def _canonical_groups(groups: Sequence[Any]) -> list[Any]:
    """Normaliza solo la relación de pertenencia, cuyo orden no es semántico."""

    canonical: list[Any] = []
    for value in groups:
        if not isinstance(value, Mapping):
            canonical.append(value)
            continue
        group = dict(value)
        members = group.get("members")
        if isinstance(members, list):
            # SQLite modela esta colección como una relación con clave primaria;
            # el orden de lectura no forma parte del contrato de Group. No se
            # eliminan duplicados para no ocultar una pérdida real de datos.
            group["members"] = sorted(members, key=lambda item: str(item).casefold())
        canonical.append(group)
    return canonical


def inventory_fingerprint(devices: Sequence[Any], groups: Sequence[Any]) -> str:
    """Devuelve el hash semántico del inventario de un workspace."""

    value = {"devices": list(devices), "groups": _canonical_groups(groups)}
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()
