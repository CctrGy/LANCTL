"""Physical rack dimensions, shared validation and non-destructive legacy reads."""

from copy import deepcopy

WIDTHS = (10, 19, 21, 23)
HEIGHT_KEYS = ("units", "size_units", "height")


def validate_height(value):
    if type(value) is not int or not 4 <= value <= 52:
        raise ValueError("La altura del rack debe ser un entero entre 4 y 52 U")
    return value


def validate_width(value):
    if type(value) is not int or value not in WIDTHS:
        raise ValueError("El ancho de montaje debe ser 10, 19, 21 o 23 pulgadas")
    return value


def dimension_status(data):
    height = next((data[k] for k in HEIGHT_KEYS if k in data), None)
    dimensions = data.get("rackDimensions")
    warnings = []
    try:
        validate_height(height)
    except ValueError as exc:
        warnings.append(str(exc))
    if any(data[k] != height for k in HEIGHT_KEYS if k in data):
        warnings.append("Alturas heredadas contradictorias; requiere corrección explícita")
    width = None
    if dimensions is None:
        warnings.append("Ancho de montaje sin especificar")
    elif (
        not isinstance(dimensions, dict)
        or type(dimensions.get("schemaVersion")) is not int
        or dimensions.get("schemaVersion") != 1
    ):
        warnings.append("Esquema de dimensiones no compatible")
    else:
        width = dimensions.get("widthInches")
        try:
            validate_width(width)
        except ValueError as exc:
            warnings.append(str(exc))
    return {
        "schemaVersion": 1,
        "heightU": height,
        "widthInches": width,
        "needsReview": bool(warnings),
        "warnings": warnings,
    }


def with_dimensions(data, height, width):
    height, width = validate_height(height), validate_width(width)
    result = deepcopy(data)
    # Preserve old field consumers while maintaining one consistent height.
    for key in HEIGHT_KEYS:
        if key == "units" or key in result:
            result[key] = height
    result["rackDimensions"] = {"schemaVersion": 1, "widthInches": width}
    return result


def new_rack_dimensions(data):
    height = next((data[k] for k in HEIGHT_KEYS if k in data), 42)
    dimensions = data.get("rackDimensions", {"schemaVersion": 1, "widthInches": 19})
    if (
        not isinstance(dimensions, dict)
        or type(dimensions.get("schemaVersion")) is not int
        or dimensions.get("schemaVersion") != 1
    ):
        raise ValueError("Esquema de dimensiones no compatible")
    return with_dimensions(data, height, dimensions.get("widthInches"))


def validate_dimension_change(previous, updated, occupants):
    keys = (*HEIGHT_KEYS, "rackDimensions")
    if all(previous.get(key) == updated.get(key) for key in keys):
        return  # Editing a name must not destroy or silently repair legacy dimensions.
    current = dimension_status(updated)
    if current["needsReview"]:
        raise ValueError("; ".join(current["warnings"]))
    height = current["heightU"]
    for unit, span in occupants:
        if unit is not None and (type(unit) is not int or unit < 1 or unit + span - 1 > height):
            raise ValueError("La altura deja equipos fuera del rack")
