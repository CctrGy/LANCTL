"""Versioned physical placement, independent of applications and interfaces.

Legacy locations are interpreted without rewriting ambiguous data. Hosted devices
store only a tray reference: their effective rack is derived, never duplicated.
"""

from copy import deepcopy

from lanctl.core.rack_dimensions import dimension_status


def appearance(values):
    if not isinstance(values, dict):
        raise ValueError("Apariencia de equipo inválida")
    kind = values.get("kind")
    if kind not in {"auto", "switch", "panel", "server", "ups", "router", "shelf", "blank"}:
        raise ValueError("Selecciona un tipo de frente válido")
    result = {"schemaVersion": 1, "kind": kind}
    for key, minimum, maximum in [("rj45", 0, 96), ("sfp", 0, 32), ("units", 1, 52)]:
        value = values.get(key)
        if type(value) is not int or not minimum <= value <= maximum:
            raise ValueError(f"{key} debe estar entre {minimum} y {maximum}")
        result[key] = value
    if type(values.get("rackmount")) is not bool:
        raise ValueError("Selecciona el formato de montaje")
    result["rackmount"] = values["rackmount"]
    return result


def span(data):
    value = data.get("rackAppearance")
    if value is None:
        return 1
    if (
        not isinstance(value, dict)
        or type(value.get("schemaVersion")) is not int
        or value["schemaVersion"] != 1
    ):
        raise ValueError("Esquema de apariencia no compatible")
    return appearance(value)["units"]


def is_rack(record):
    return record.get("prefix") == "RK" or record.get("data", {}).get("type") == "rack"


def is_tray(data):
    return data.get("type") in {"tray", "device.tray"}


def location_status(data, records=(), seen=()):
    """Return a read-only projection, preserving unresolved legacy locations."""
    index = records if isinstance(records, dict) else {r["id"]: r for r in records}
    loc = data.get("location") or {}
    result = {"kind": "review", "rack": None, "unit": None, "tray": None, "needsReview": True}
    if not isinstance(loc, dict):
        return result
    result.update(rack=loc.get("rack"), unit=loc.get("unit"), tray=loc.get("tray"))
    if any(loc.get(k) is not None and not isinstance(loc[k], str) for k in ("rack", "tray")):
        return result
    if "schemaVersion" in loc and (
        type(loc["schemaVersion"]) is not int or loc["schemaVersion"] != 1
    ):
        return result
    tray = loc.get("tray")
    if tray:
        parent = index.get(tray)
        if tray in seen or not parent or not is_tray(parent["data"]):
            return result
        if loc.get("rack") is not None or loc.get("unit") != 0 or loc.get("in_rack") is not False:
            return result
        effective = location_status(parent["data"], index, (*seen, tray))
        return {**effective, "kind": "hosted", "tray": tray}
    rack, unit = loc.get("rack"), loc.get("unit")
    if rack and index and (rack not in index or not is_rack(index[rack])):
        return result
    inside = loc.get("in_rack")
    if "in_rack" in loc and type(inside) is not bool:
        return result
    if rack and type(unit) is int and unit >= 1 and inside is not False:
        kind = "inside"
    elif rack and inside is False and type(unit) is int and unit == 0:
        kind = "environment"
    elif not rack and inside is not True and (unit is None or (type(unit) is int and unit == 0)):
        kind = "independent"
    else:
        return result
    if kind == "inside" and records:
        parent = index[rack]
        height = dimension_status(parent["data"])["heightU"]
        if type(height) is not int or unit + span(data) - 1 > height:
            return result
    return {**result, "kind": kind, "unit": unit or 0, "needsReview": False}


def with_location(data, *, rack=None, in_rack=False, unit=0, tray=None):
    result = deepcopy(data)
    old = result.get("location") or {}
    result["location"] = {
        **old,
        "schemaVersion": 1,
        "rack": rack or None,
        "in_rack": in_rack,
        "unit": unit,
        "tray": tray or None,
    }
    return result


def apply_placement(data, values):
    result = deepcopy(data)
    if "unit" in values and values["unit"] is not None and type(values["unit"]) is not int:
        raise ValueError("La unidad debe ser un entero")
    if any(k in values for k in ("rack", "unit", "in_rack", "tray")):
        old = result.get("location") or {}
        rack = values.get("rack", old.get("rack")) or None
        tray = values.get("tray", old.get("tray")) or None
        unit = values.get("unit", old.get("unit"))
        inside = values.get("in_rack", bool(rack and unit))
        if tray:
            if (
                values.get("rack")
                or values.get("in_rack") is True
                or values.get("unit", 0) not in (None, 0)
            ):
                raise ValueError("Un dispositivo alojado no tiene montaje directo en U")
            rack, inside, unit = None, False, 0
        elif not rack:
            if values.get("in_rack") is True or values.get("unit", 0) not in (None, 0):
                raise ValueError("Una unidad de montaje requiere un rack")
            inside, unit = False, 0
        elif inside is False:
            if values.get("unit", 0) not in (None, 0):
                raise ValueError("Los elementos del entorno usan unidad 0")
            if "in_rack" not in values and not unit and not old.get("schemaVersion"):
                # Historical API: association without a position stays unresolved.
                result["location"] = {**old, "rack": rack, "unit": unit}
                return result
            unit = 0
        result = with_location(result, rack=rack, in_rack=inside, unit=unit, tray=tray)
    if "heightU" in values:
        visual = result.get("rackAppearance") or {
            "kind": "auto",
            "rj45": 0,
            "sfp": 0,
            "rackmount": True,
        }
        result["rackAppearance"] = appearance({**visual, "units": values["heightU"]})
    return result


def validate_location(records, identifier, data):
    if data.get("type") in {"rack", "wire"}:
        if (data.get("location") or {}).get("tray"):
            raise ValueError("Un rack o cable no puede alojarse en una bandeja")
        return
    index = records if isinstance(records, dict) else {r["id"]: r for r in records}
    loc = data.get("location") or {}
    status = location_status(data, index, (identifier,))
    if status["needsReview"]:
        raise ValueError(
            "Ubicación ambigua o inválida; revisa rack, clasificación, unidad y bandeja"
        )
    if loc.get("rack") and (loc["rack"] not in index or not is_rack(index[loc["rack"]])):
        raise ValueError("El rack asignado ya no existe")
    if "schemaVersion" in loc:
        if any(
            loc.get(key) is not None and not isinstance(loc[key], str) for key in ("rack", "tray")
        ):
            raise ValueError("Las referencias de rack y bandeja deben ser identificadores")
        if type(loc.get("in_rack")) is not bool or type(loc.get("unit")) is not int:
            raise ValueError("La ubicación requiere in_rack booleano y unidad entera")
        if status["kind"] != "inside" and loc["unit"] != 0:
            raise ValueError("Los elementos sin montaje directo deben usar unidad 0")
    if status["kind"] == "hosted":
        if is_tray(data):
            raise ValueError("Una bandeja no puede alojarse dentro de otra bandeja")
        parent = index[status["tray"]]
        if location_status(parent["data"], index)["kind"] != "inside":
            raise ValueError("La bandeja debe estar montada en un rack")
        return
    if status["kind"] != "inside":
        return
    rack = index.get(status["rack"])
    if rack is None or not is_rack(rack):
        raise ValueError("El rack asignado ya no existe")
    dimensions = dimension_status(rack["data"])
    height = dimensions["heightU"]
    if type(height) is not int or not 4 <= height <= 52:
        raise ValueError("Revisa primero las dimensiones del rack")
    start, size = status["unit"], span(data)
    if start + size - 1 > height:
        raise ValueError("El equipo sobrepasa la altura del armario")
    for unit, occupied in legacy_layout_spans(rack["data"]):
        if start < unit + occupied and unit < start + size:
            raise ValueError("Las unidades están reservadas por el diseño heredado del rack")
    for other in index.values():
        if other["id"] == identifier or is_rack(other) or other["data"].get("type") == "wire":
            continue
        position = location_status(other["data"], index)
        if position["kind"] != "inside" or position["rack"] != status["rack"]:
            continue
        if start < position["unit"] + span(other["data"]) and position["unit"] < start + size:
            raise ValueError(f"Las unidades están ocupadas por {other['id']}")


def legacy_layout_spans(data):
    """Unlinked legacy furniture remains reserved until explicitly converted."""
    for item in data.get("layout", []):
        if not isinstance(item, dict) or item.get("idf"):
            continue
        unit, height = item.get("unit"), item.get("height", 1)
        if type(unit) is not int or unit < 1 or type(height) is not int or height < 1:
            raise ValueError("Revisa las posiciones del diseño heredado del rack")
        yield unit, height


def validate_change(records, identifier, data, previous=None):
    """Validate changed physical state at the storage boundary, for every UI."""
    if previous is not None and all(
        previous.get(k) == data.get(k) for k in ("location", "rackAppearance", "type")
    ):
        return
    span(data)
    loc = data.get("location") or {}
    # Legacy imports without an explicit position remain reviewable, not guessed.
    if (
        previous is None
        and isinstance(loc, dict)
        and "schemaVersion" not in loc
        and "in_rack" not in loc
        and loc.get("rack")
        and (loc.get("unit") is None or (type(loc["unit"]) is int and loc["unit"] == 0))
        and location_status(data, records)["needsReview"]
    ):
        return
    validate_location(records, identifier, data)
    children = [r for r in records if (r["data"].get("location") or {}).get("tray") == identifier]
    if children and (not is_tray(data) or location_status(data, records)["kind"] != "inside"):
        raise ValueError("Reubica explícitamente los dispositivos antes de retirar la bandeja")
