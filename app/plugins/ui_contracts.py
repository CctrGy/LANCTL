from __future__ import annotations

import re
from copy import deepcopy

PANEL_LAYOUTS = {
    "table",
    "cards",
    "master-detail",
    "resource-browser",
    "dashboard",
    "form",
    "timeline",
}
FIELD_TYPES = {"device", "text", "badge", "status", "path", "date"}
PLACEMENTS = {"panel-toolbar", "item", "detail"}
FORM_TYPES = {"text", "password", "secret", "checkbox", "select"}
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*(?:\.[A-Za-z][A-Za-z0-9_-]*)+$")


def validate_ui_panel(specification: dict) -> dict:
    spec = deepcopy(specification)
    required = ("title", "location", "dataProvider", "layout")
    if not isinstance(spec, dict) or any(not str(spec.get(key, "")).strip() for key in required):
        raise ValueError("ui-panel requiere title, location, dataProvider y layout")
    if spec["location"] not in {"main"} or spec["layout"] not in PANEL_LAYOUTS:
        raise ValueError("ubicación o plantilla ui-panel no permitida")
    if not _ID.fullmatch(str(spec["dataProvider"])):
        raise ValueError("dataProvider ui-panel no válido")
    spec["order"] = int(spec.get("order", 1000))
    for column in spec.get("columns", []):
        if not isinstance(column, dict) or not str(column.get("field", "")).strip():
            raise ValueError("columna ui-panel no válida")
        if column.get("type", "text") not in FIELD_TYPES:
            raise ValueError("tipo visual ui-panel no permitido")
    empty = spec.get("emptyState", {})
    if empty and (not isinstance(empty, dict) or not str(empty.get("title", "")).strip()):
        raise ValueError("emptyState ui-panel no válido")
    return spec


def validate_ui_action(specification: dict) -> dict:
    spec = deepcopy(specification)
    function_id = str(spec.get("function", ""))
    if not str(spec.get("label", "")).strip() or not _ID.fullmatch(function_id):
        raise ValueError("ui-action requiere label y function válida")
    if spec.get("placement", "detail") not in PLACEMENTS:
        raise ValueError("placement ui-action no permitido")
    spec["placement"] = spec.get("placement", "detail")
    spec["requiresSelection"] = bool(spec.get("requiresSelection", False))
    spec["confirmation"] = str(spec.get("confirmation", ""))
    return spec


def validate_form_schema(schema: dict) -> dict:
    form = deepcopy(schema)
    if not isinstance(form, dict) or not isinstance(form.get("fields"), list):
        raise ValueError("formulario declarativo no válido")
    names = set()
    for field in form["fields"]:
        if not isinstance(field, dict) or not re.fullmatch(
            r"[A-Za-z][A-Za-z0-9_-]*", str(field.get("name", ""))
        ):
            raise ValueError("campo de formulario no válido")
        if field.get("type", "text") not in FORM_TYPES or field["name"] in names:
            raise ValueError("tipo o nombre de formulario no permitido")
        names.add(field["name"])
        if field.get("type") in {"secret", "password"} and any(
            key in field for key in ("default", "value", "persist")
        ):
            raise ValueError("un secreto no puede declararse persistente ni llevar valor inicial")
    return form
