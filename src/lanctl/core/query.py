from __future__ import annotations

import re

QUERY_FIELDS = {
    "ip": "ip",
    "mac": "mac",
    "alias": "alias",
    "name": "name",
    "cnf": "cnf",
    "group": "groups",
    "vendor": "manufacturer",
    "manufacturer": "manufacturer",
    "protocol": "protocols",
    "description": "description",
}


def _values(device, field: str) -> list[str]:
    value = getattr(device, QUERY_FIELDS[field])
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def matches_query(device, active: bool, expression: str | None) -> bool:
    if not expression:
        return True
    terms = [
        term.strip()
        for term in re.split(r"\s+and\s+", expression, flags=re.IGNORECASE)
        if term.strip()
    ]
    if not terms:
        raise ValueError("la consulta --where está vacía")
    for term in terms:
        state = term.casefold()
        if state in ("active", "activo"):
            if not active:
                return False
            continue
        if state in ("inactive", "offline", "inactivo"):
            if active:
                return False
            continue
        match = re.fullmatch(r"([a-zA-Z][\w-]*)\s*(=|!=|~)\s*(.+)", term)
        if not match:
            raise ValueError(f"término --where no válido: {term}")
        field, operator, expected = match.groups()
        field = field.casefold()
        if field not in QUERY_FIELDS:
            raise ValueError(
                f"campo --where no válido: {field}. Disponibles: " + ", ".join(QUERY_FIELDS)
            )
        expected = expected.strip().strip("\"'").casefold()
        values = [value.casefold() for value in _values(device, field)]
        equal = expected in values
        contains = any(expected in value for value in values)
        if operator == "=" and not equal:
            return False
        if operator == "!=" and equal:
            return False
        if operator == "~" and not contains:
            return False
    return True
