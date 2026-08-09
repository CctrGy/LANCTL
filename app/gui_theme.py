from __future__ import annotations

import re
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.plugins.extensions import Extension


COMPONENT_IDS = frozenset(
    {
        "lanctl.app-shell",
        "lanctl.topbar",
        "lanctl.content",
        "lanctl.status-cards",
        "lanctl.device-table",
        "lanctl.device-inspector",
        "lanctl.primary-action",
        "lanctl.secondary-action",
        "lanctl.danger-action",
    }
)

DEFAULT_TOKENS = {
    "color.background": "#071522",
    "color.surface": "#0d2031",
    "color.surface-raised": "#122a3e",
    "color.border": "#244157",
    "color.text": "#edf6ff",
    "color.text-muted": "#91a8ba",
    "color.accent": "#25a9e8",
    "color.success": "#55c879",
    "color.warning": "#f5a623",
    "color.danger": "#ef5350",
    "radius.panel": "10px",
    "radius.control": "7px",
    "space.unit": "8px",
}
TOKEN_TO_CSS = {key: "--" + key.replace(".", "-") for key in DEFAULT_TOKENS}
_COLOR = re.compile(r"^#[0-9a-fA-F]{6}(?:[0-9a-fA-F]{2})?$")
_LENGTH = re.compile(r"^(?:0|[1-9][0-9]{0,2})(?:px|rem)$")


def validate_theme_specification(specification: Any) -> dict[str, Any]:
    if not isinstance(specification, dict):
        raise ValueError("la especificación del tema debe ser un objeto")
    tokens, components = specification.get("tokens", {}), specification.get("components", {})
    if not isinstance(tokens, dict) or not isinstance(components, dict):
        raise ValueError("tokens y components deben ser objetos")
    unknown_tokens = sorted(set(tokens) - set(DEFAULT_TOKENS))
    if unknown_tokens:
        raise ValueError(f"tokens de tema desconocidos: {', '.join(unknown_tokens)}")
    for key, value in tokens.items():
        _validate_value(key, value)
    unknown_components = sorted(set(components) - COMPONENT_IDS)
    if unknown_components:
        raise ValueError(f"identificadores GUI desconocidos: {', '.join(unknown_components)}")
    cleaned_components = {}
    for component_id, overrides in components.items():
        if not isinstance(overrides, dict):
            raise ValueError(f"el componente {component_id} debe contener tokens")
        unknown = sorted(set(overrides) - set(DEFAULT_TOKENS))
        if unknown:
            raise ValueError(f"tokens desconocidos en {component_id}: {', '.join(unknown)}")
        for key, value in overrides.items():
            _validate_value(key, value)
        cleaned_components[component_id] = dict(overrides)
    return {"tokens": dict(tokens), "components": cleaned_components}


def resolve_theme(extensions: Iterable[Extension]) -> dict[str, Any]:
    tokens, components = dict(DEFAULT_TOKENS), {}
    active_id = "lanctl.core.fallback"
    for extension in extensions:
        validated = validate_theme_specification(extension.specification)
        tokens.update(validated["tokens"])
        for component_id, values in validated["components"].items():
            components.setdefault(component_id, {}).update(values)
        active_id = extension.extension_id
    return {
        "id": active_id,
        "tokens": {TOKEN_TO_CSS[key]: value for key, value in tokens.items()},
        "components": {
            component_id: {TOKEN_TO_CSS[key]: value for key, value in values.items()}
            for component_id, values in components.items()
        },
    }


def _validate_value(key: str, value: Any) -> None:
    if not isinstance(value, str):
        raise ValueError(f"el token {key} debe ser texto")
    valid = _COLOR.fullmatch(value) if key.startswith("color.") else _LENGTH.fullmatch(value)
    if not valid:
        raise ValueError(f"valor no válido para el token {key}: {value}")
