"""Validated global display preferences; no GUI toolkit dependency."""

from __future__ import annotations

import math

from lanctl.core.config import load_config, update_config
from lanctl.core.plugins.manager import active_theme_extensions
from lanctl.core.plugins.theme import DEFAULT_TOKENS, TOKEN_TO_CSS, validate_theme_specification

_PRESETS = (
    ("graphite", "Grafito", "#15181c", "#20272c", "#b2ef26", "#e9eff4", "#a7b5bf"),
    ("midnight", "Azul noche", "#071522", "#0d2031", "#25a9e8", "#edf6ff", "#91a8ba"),
    ("forest", "Bosque", "#101b18", "#1b2b24", "#8cdb81", "#e9f5ed", "#a5c0ad"),
    ("violet", "Violeta", "#191622", "#282235", "#bc9cff", "#f0eafa", "#b7abc7"),
    ("light", "Claro", "#f2f5f8", "#ffffff", "#477300", "#18212b", "#52616f"),
)
_DEFAULT = {"theme": "graphite", "density": "comfortable", "fontScale": 1.0, "reducedMotion": False}


def validate_preferences(values):
    if not isinstance(values, dict) or set(values) != set(_DEFAULT):
        raise ValueError("preferencias GUI desconocidas o incompletas")
    if not isinstance(values["theme"], str) or values["theme"] not in {p[0] for p in _PRESETS}:
        raise ValueError("tema GUI desconocido")
    if not isinstance(values["density"], str) or values["density"] not in {
        "comfortable",
        "compact",
    }:
        raise ValueError("densidad GUI no válida")
    scale = values["fontScale"]
    if type(scale) not in (float, int) or not math.isfinite(scale) or not 0.9 <= scale <= 1.3:
        raise ValueError("escala GUI debe estar entre 0.9 y 1.3")
    if type(values["reducedMotion"]) is not bool:
        raise ValueError("reducedMotion debe ser booleano")
    return {**values, "fontScale": float(scale)}


def _payload(values):
    preferences = validate_preferences(values)
    themes = []
    for identifier, name, background, surface, accent, text, muted in _PRESETS:
        tokens = {
            **DEFAULT_TOKENS,
            "color.background": background,
            "color.surface": surface,
            "color.surface-raised": "#252d33" if identifier == "graphite" else surface,
            "color.accent": accent,
            "color.text": text,
            "color.text-muted": muted,
            "color.border": {
                "graphite": "#343e46",
                "midnight": "#244157",
                "forest": "#344b3c",
                "violet": "#4b405d",
                "light": "#c7d0d9",
            }[identifier],
        }
        validate_theme_specification({"tokens": tokens})
        themes.append(
            {
                "id": identifier,
                "name": name,
                "tokens": {TOKEN_TO_CSS[k]: v for k, v in tokens.items()},
            }
        )
    active = next(t for t in themes if t["id"] == preferences["theme"])
    theme = {"id": active["id"], "tokens": dict(active["tokens"]), "components": {}}
    plugin_tokens = {}
    effective = []
    for extension in active_theme_extensions():
        # The bundled palette is the legacy base, not a user overlay: applying it
        # here would turn all five explicit presets back into the same blue theme.
        if (
            extension.owner == "lanctl.theme.default"
            and extension.extension_id == "lanctl.theme.default.palette"
        ):
            continue
        overrides = validate_theme_specification(extension.specification)
        theme["tokens"].update({TOKEN_TO_CSS[k]: v for k, v in overrides["tokens"].items()})
        plugin_tokens.update({TOKEN_TO_CSS[k]: v for k, v in overrides["tokens"].items()})
        for component, tokens in overrides["components"].items():
            theme["components"].setdefault(component, {}).update(
                {TOKEN_TO_CSS[k]: v for k, v in tokens.items()}
            )
        effective.append(extension.extension_id)
    theme["effectivePlugin"] = effective[-1] if effective else None
    theme["pluginTokens"] = plugin_tokens
    theme["pluginComponents"] = {k: dict(v) for k, v in theme["components"].items()}
    return {
        "preferences": preferences,
        "themes": themes,
        "theme": theme,
        "effectivePlugin": theme["effectivePlugin"],
    }


def preferences_payload() -> dict:
    stored = load_config().get("guiPreferences", {"schemaVersion": 1, **_DEFAULT})
    if (
        not isinstance(stored, dict)
        or type(stored.get("schemaVersion")) is not int
        or stored["schemaVersion"] != 1
    ):
        raise ValueError("versión de preferencias GUI no compatible")
    return _payload({key: value for key, value in stored.items() if key != "schemaVersion"})


def save_preferences(values: dict) -> dict:
    cleaned = validate_preferences(values)

    def update(config):
        config["guiPreferences"] = {"schemaVersion": 1, **cleaned}

    update_config(update)
    return _payload(cleaned)
