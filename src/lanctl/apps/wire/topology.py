"""Vocabulario físico, presets y compatibilidad de conexiones de LANWIRE."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

RJ45 = "connection.rj45"
FIBER = "connection.fiber"
DAC = "connection.dac"
UNKNOWN = "connection.unknown"

BUILTIN_GROUPS = {
    "WIRE": "Cables de cualquier medio.",
    "SWITCHS": "Switches, routers y equipos de distribución.",
    "PC": "Ordenadores, estaciones y servidores de la red.",
}

WIRE_PREFIX_KINDS = {
    "FB": "wire.fiber",
    "WL": "wire.copper",
    "WE": "wire.copper",
}

NEW_IDF_PROFILES = {
    "wire.coper": ("wire.copper", None),
    "wire.copper": ("wire.copper", None),
    "wire.fiber": ("wire.fiber", None),
    "wire.dac": ("wire.dac", None),
    "router.otg": ("router.otg", "router.otg"),
    "router.gateway": ("router.gateway", "router"),
    "switch.5ports": ("switch.5Ports", "switch-5"),
    "switch.12ports": ("switch.12Ports", "switch-12"),
    "switch.24ports": ("switch.24Ports", "switch-24"),
    "switch.48ports": ("switch.48Ports", "switch-48"),
    "pc.1port": ("pc.1Port", "pc-1"),
    "pc.2ports": ("pc.2Ports", "pc-2"),
    "server.2ports": ("server.2Ports", "server-2"),
}


def build_new_idf_data(
    requested_type: str, *, alias: str = "", description: str = ""
) -> dict[str, Any]:
    """Construye los datos de `idf add` a partir del perfil del prefijo."""
    normalized = requested_type.strip().casefold()
    profile = NEW_IDF_PROFILES.get(normalized)
    if profile is None:
        available = ", ".join(value[0] for value in dict.fromkeys(NEW_IDF_PROFILES.values()))
        raise ValueError(f"tipo de IDF desconocido: {requested_type}. Disponibles: {available}")
    subtype, preset = profile
    if preset is None:
        data: dict[str, Any] = {
            "type": "wire",
            "subtype": subtype,
            "kind": subtype,
            "endpoints": [],
        }
    else:
        data = apply_device_preset({}, preset)
        data["subtype"] = subtype
    if alias.strip():
        data["alias"] = alias.strip()
    if description.strip():
        data["description"] = description.strip()
    return data


def apply_prefix_defaults(prefix: str, data: dict[str, Any] | None) -> dict[str, Any]:
    """Clasifica los prefijos de cable sin pisar un tipo explícito distinto."""
    result = deepcopy(data or {})
    kind = WIRE_PREFIX_KINDS.get(prefix.strip().upper())
    if kind is None or result.get("type") not in (None, "", "element", "wire"):
        return result
    result["type"] = "wire"
    result.setdefault("kind", kind)
    result.setdefault("endpoints", [])
    return result


def connection_medium(value: str | None) -> str:
    """Normaliza los nombres nuevos y los `kind` heredados de la topología."""
    normalized = str(value or "").casefold()
    if normalized in {"connection.rj45", "wire.copper", "rj45", "copper"}:
        return RJ45
    if normalized in {"connection.fiber", "wire.fiber", "fiber", "fibra"}:
        return FIBER
    if normalized in {"connection.dac", "wire.dac", "dac", "sfp", "sfp/dac"}:
        return DAC
    return UNKNOWN


def connector_gender(value: str | None) -> str | None:
    normalized = str(value or "").casefold()
    if normalized in {"male", "macho"}:
        return "male"
    if normalized in {"female", "hembra"}:
        return "female"
    return None


def compatible_connection(
    wire: dict[str, Any], port: dict[str, Any], *, wire_end: int | None = None
) -> tuple[bool, str]:
    """Comprueba el medio con la polaridad física fija de LANWIRE.

    Un cable siempre aporta un conector macho y los puertos de equipos son
    siempre hembra. Los campos antiguos de género se ignoran para que una
    importación heredada no pueda alterar esa regla.
    """
    wire_medium = connection_medium(wire.get("kind") or wire.get("medium"))
    port_medium = connection_medium(port.get("kind") or port.get("medium"))
    if UNKNOWN in {wire_medium, port_medium}:
        return False, "el medio del cable o del puerto no está definido"
    if wire_medium != port_medium:
        return (
            False,
            f"el cable usa {wire_medium.removeprefix('connection.')} y el puerto {port_medium.removeprefix('connection.')}",
        )
    port_gender = connector_gender(port.get("connectorGender"))
    if port_gender == "male":
        return False, "el puerto debe ser hembra; los cables LANWIRE son siempre macho"
    return True, "compatible"


def apply_device_preset(data: dict[str, Any], requested_type: str) -> dict[str, Any]:
    """Aplica un punto de partida seguro para los tipos físicos más frecuentes."""
    normalized = requested_type.strip().casefold().removeprefix("device.")
    result = deepcopy(data)
    if normalized == "router.otg":
        result["type"] = "device.router"
        result["portNaming"] = "FIBER,WLAN"
        result["portTemplate"] = {"kind": "wire.copper", "poe": False, "speeds": []}
        result["ports"] = build_ports(2, "FIBER,WLAN")
        return result
    presets = {
        "router": ("device.router", 5, "LAN{n}", True),
        "router-4rj-1fb": ("device.router", 4, "LAN{n}", True),
        "switch-5": ("device.switch", 5, "X{n}", False),
        "switch-12": ("device.switch", 12, "X{n}", False),
        "switch-24": ("device.switch", 24, "X{n}", False),
        "switch-48": ("device.switch", 48, "X{n}", False),
        "pc-1": ("device.pc", 1, "LAN{n}", False),
        "pc-2": ("device.pc", 2, "LAN{n}", False),
        "server-2": ("device.server", 2, "LAN{n}", False),
    }
    if normalized in presets:
        element_type, count, pattern, fiber = presets[normalized]
        result["type"] = element_type
        result["portNaming"] = pattern
        template = {"kind": "wire.copper", "poe": False, "speeds": []}
        result["portTemplate"] = template
        result["ports"] = build_ports(count, pattern, fiber=fiber, **template)
    elif normalized == "router":
        result["type"] = "device.router"
        result.setdefault(
            "ports",
            {
                **{
                    f"LAN{index}": {"kind": RJ45, "connectorGender": "female", "poe": False}
                    for index in range(1, 6)
                },
                "FIBER": {"kind": FIBER, "connectorGender": "female", "poe": False},
            },
        )
    elif normalized in {"switch", "pc", "server", "outlet", "panel"}:
        result["type"] = f"device.{normalized}"
        result.setdefault("ports", {})
    else:
        result["type"] = requested_type.strip()
    return result


def build_ports(
    count: int,
    pattern: str,
    *,
    fiber: bool = False,
    kind: str = "wire.copper",
    poe: bool = False,
    speeds: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    """Genera series independientes (`X{n}:24, XG{a}:4`) y nombres fijos."""
    tokens = [part.strip() for part in pattern.split(",")]
    if not tokens or any(not token for token in tokens):
        raise ValueError("la plantilla de puertos no puede tener entradas vacías")
    if not 0 <= count <= 96:
        raise ValueError("el número de puertos debe estar entre 0 y 96")
    ports: dict[str, dict[str, Any]] = {}
    for token in tokens:
        match = re.fullmatch(r"([A-Za-z]+)\{([a-z])\}(?::(\d+))?", token)
        if match:
            prefix, _variable, amount_text = match.groups()
            if len(tokens) > 1 and amount_text is None:
                raise ValueError("cada serie mixta necesita cantidad; por ejemplo X{n}:24")
            amount = int(amount_text) if amount_text is not None else count
            if amount < 1 or amount > 96:
                raise ValueError("cada serie debe contener entre 1 y 96 puertos")
            names = (f"{prefix}{index}" for index in range(1, amount + 1))
        elif re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", token):
            names = (token,)
        else:
            raise ValueError("usa LAN{n}, X{n}:24, XG{a}:4 o FIBER")
        for name in names:
            if name in ports:
                raise ValueError(f"nombre de puerto duplicado: {name}")
            is_fiber = name.upper() == "FIBER"
            ports[name] = {
                "kind": FIBER if is_fiber else kind,
                "connectorGender": "female",
                "poe": False if is_fiber else poe,
                "speeds": list(speeds or []),
            }
            if len(ports) > 96:
                raise ValueError("una plantilla no puede superar 96 puertos")
    if fiber and "FIBER" not in ports:
        ports["FIBER"] = {
            "kind": FIBER,
            "connectorGender": "female",
            "poe": False,
            "speeds": list(speeds or []),
        }
    return ports


def resize_port_pattern(pattern: str, count: int) -> str:
    """Ajusta las series del final sin alterar los prefijos ni sus contadores."""
    if "," not in pattern:
        return pattern
    tokens = [part.strip() for part in pattern.split(",")]
    series = []
    fixed = 0
    for index, token in enumerate(tokens):
        match = re.fullmatch(r"([A-Za-z]+\{[a-z]\}):(\d+)", token)
        if match:
            series.append((index, match.group(1), int(match.group(2))))
        elif token.upper() != "FIBER":
            fixed += 1
    current = fixed + sum(amount for _, _, amount in series)
    change = count - current
    if not series and change:
        raise ValueError("la plantilla no tiene una serie numerada que redimensionar")
    replacements: dict[int, str | None] = {}
    if change > 0:
        index, prefix, amount = series[-1]
        replacements[index] = f"{prefix}:{amount + change}"
    elif change < 0:
        remaining = -change
        for index, prefix, amount in reversed(series):
            removed = min(remaining, amount)
            replacements[index] = f"{prefix}:{amount - removed}" if amount > removed else None
            remaining -= removed
            if not remaining:
                break
        if remaining:
            raise ValueError("no se pueden quitar los nombres fijos de la plantilla")
    return ",".join(
        replacements.get(index, token)
        for index, token in enumerate(tokens)
        if replacements.get(index, token) is not None
    )


def groups_for(record: dict[str, Any]) -> set[str]:
    data = record.get("data") or {}
    groups = {str(value).upper() for value in data.get("groups", []) if str(value).strip()}
    element_type = str(data.get("type", ""))
    if element_type == "wire":
        groups.add("WIRE")
    if element_type in {"device.switch", "device.router", "device.gateway"}:
        groups.add("SWITCHS")
    if element_type in {"device.pc", "device.workstation", "device.server"}:
        groups.add("PC")
    return groups
