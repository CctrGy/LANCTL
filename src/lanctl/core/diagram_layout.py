"""Bounded, versioned diagram views inside the project's physical JSON."""

import hashlib
import json
import math

from lanctl.shared.i18n import t


def invalid():
    return ValueError(t("LANCTL.DIAGRAM.INVALID"))


def validate_view(key, value):
    try:
        scope = json.loads(key)
    except (TypeError, ValueError) as error:
        raise invalid() from error
    if (
        not isinstance(scope, list)
        or len(scope) != 3
        or scope[0] not in {"inside", "outside"}
        or any(not isinstance(v, str) or len(v) > 256 for v in scope)
    ):
        raise invalid()
    if (
        not isinstance(value, dict)
        or type(value.get("schemaVersion")) is not int
        or value["schemaVersion"] != 1
    ):
        raise invalid()
    positions = value.get("positions")
    camera = value.get("camera")
    if not isinstance(positions, dict) or len(positions) > 5000 or not isinstance(camera, dict):
        raise invalid()

    def number(v):
        return type(v) in (int, float) and math.isfinite(v) and abs(v) <= 10_000_000

    for identifier, point in positions.items():
        if (
            not isinstance(identifier, str)
            or len(identifier) > 256
            or not isinstance(point, dict)
            or not all(number(point.get(axis)) for axis in ("x", "y"))
        ):
            raise invalid()
    if (
        not all(number(camera.get(axis)) for axis in ("x", "y", "z"))
        or not 0.02 <= camera["z"] <= 3
    ):
        raise invalid()
    regions = value.get("regions", {})
    if not isinstance(regions, dict) or len(regions) > 512:
        raise invalid()
    for identifier, bounds in regions.items():
        if (
            not isinstance(identifier, str)
            or len(identifier) > 256
            or not isinstance(bounds, dict)
            or not all(number(bounds.get(axis)) for axis in ("x", "y", "w", "h"))
            or bounds["w"] <= 0
            or bounds["h"] <= 0
        ):
            raise invalid()
    return {
        "schemaVersion": 1,
        **(
            {
                "regions": {
                    key: {axis: bounds[axis] for axis in ("x", "y", "w", "h")}
                    for key, bounds in regions.items()
                }
            }
            if "regions" in value
            else {}
        ),
        "positions": {k: {"x": v["x"], "y": v["y"]} for k, v in positions.items()},
        "camera": {axis: camera[axis] for axis in ("x", "y", "z")},
    }


def layouts(document):
    value = document.get("diagramLayouts", {"schemaVersion": 1, "views": {}})
    if (
        not isinstance(value, dict)
        or type(value.get("schemaVersion")) is not int
        or value["schemaVersion"] != 1
        or not isinstance(value.get("views"), dict)
        or len(value["views"]) > 64
    ):
        raise invalid()
    views = {key: validate_view(key, view) for key, view in value["views"].items()}
    if sum(len(view["positions"]) for view in views.values()) > 20000:
        raise invalid()
    return {"schemaVersion": 1, "views": views}


def revision(view):
    return (
        hashlib.sha256(json.dumps(view, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if view is not None
        else None
    )
