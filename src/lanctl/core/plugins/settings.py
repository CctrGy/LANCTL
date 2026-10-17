"""Versioned, non-secret preferences declared by an installed LCP manifest."""

from __future__ import annotations

import json
import re

from lanctl.core.file_transaction import update_json


class PluginSettings:
    def __init__(self, plugin):
        self.plugin = plugin
        self.path = plugin.path.parent / ".settings" / f"{plugin.manifest.plugin_id}.json"
        # The running manager may retain a module loaded before an external LCP
        # update. Preferences describe the current package, not that cached module.
        self.raw = plugin.manifest.raw
        manifest_path = plugin.path / "plugin.info"
        if manifest_path.is_file():
            from lanctl.core.plugins.models import PluginManifest

            with manifest_path.open("rb") as stream:
                content = stream.read(512 * 1024 + 1)
            if len(content) > 512 * 1024:
                raise ValueError("manifiesto de configuración de plugin demasiado grande")
            document = json.loads(content)
            if not isinstance(document, dict):
                raise ValueError("el manifiesto de configuración debe ser un objeto JSON")
            manifest = PluginManifest.from_dict(document)
            if manifest.plugin_id != plugin.manifest.plugin_id:
                raise ValueError("el manifiesto de configuración pertenece a otro plugin")
            self.raw = manifest.raw

    def fields(self) -> list[dict]:
        schema = self.raw.get("settingsSchema")
        if schema is None and self.plugin.manifest.plugin_id == "lanctl.network.wol":
            # Existing WOL commands already consume these shared defaults.
            return [
                {
                    "name": "port",
                    "label": "Puerto UDP",
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 65535,
                    "default": 9,
                },
                {
                    "name": "repeat",
                    "label": "Repeticiones",
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 3,
                },
                {
                    "name": "wait",
                    "label": "Espera de arranque (segundos)",
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 3600,
                    "default": 60,
                },
            ]
        if schema is None:
            return []
        if not isinstance(schema, dict) or schema.get("schemaVersion") != 1:
            raise ValueError("versión de configuración de plugin no compatible")
        fields = schema.get("fields")
        if not isinstance(fields, list) or len(fields) > 50:
            raise ValueError("campos de configuración de plugin no válidos")
        names = set()
        for field in fields:
            if not isinstance(field, dict):
                raise ValueError("campo de configuración de plugin no válido")
            name = field.get("name", "")
            if not isinstance(name, str) or not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,63}", name):
                raise ValueError("nombre de configuración de plugin no válido")
            if name in names or field.get("type") not in {"text", "integer", "boolean", "select"}:
                raise ValueError("tipo de configuración de plugin no permitido")
            names.add(name)
            self._value(field, field.get("default"))
        return fields

    @staticmethod
    def _value(field, value):
        kind = field["type"]
        if kind == "boolean":
            valid = type(value) is bool
        elif kind == "integer":
            valid = type(value) is int and field.get("minimum", -(2**31)) <= value <= field.get(
                "maximum", 2**31 - 1
            )
        else:
            valid = isinstance(value, str) and len(value) <= 4096
            if kind == "select":
                choices = field.get("choices")
                valid = valid and isinstance(choices, list) and value in choices
        if not valid:
            raise ValueError(f"valor no válido para la opción {field['name']}")
        return value

    def _document(self, value):
        if (
            not isinstance(value, dict)
            or value.get("schemaVersion") != 1
            or not isinstance(value.get("values"), dict)
        ):
            raise ValueError("archivo de configuración de plugin no válido")
        return value

    def load(self) -> dict:
        if self._uses_wol_defaults():
            from lanctl.core.config import load_config

            values = load_config().get("wol", {})
            return {
                field["name"]: self._value(field, values.get(field["name"], field["default"]))
                for field in self.fields()
            }
        document = (
            self._document(json.loads(self.path.read_text(encoding="utf-8")))
            if self.path.exists()
            else {"schemaVersion": 1, "values": {}}
        )
        return {
            field["name"]: self._value(
                field, document["values"].get(field["name"], field.get("default"))
            )
            for field in self.fields()
        }

    def save(self, values: dict) -> dict:
        fields = {field["name"]: field for field in self.fields()}
        if not isinstance(values, dict) or set(values) != set(fields):
            raise ValueError("opciones de plugin desconocidas o incompletas")
        cleaned = {name: self._value(fields[name], value) for name, value in values.items()}
        if self._uses_wol_defaults():
            from lanctl.core.config import update_config

            def update(config):
                config.setdefault("wol", {}).update(cleaned)

            update_config(update)
            return cleaned

        def replace(document):
            self._document(document)
            return {"schemaVersion": 1, "values": cleaned}

        update_json(self.path, lambda: {"schemaVersion": 1, "values": {}}, replace)
        return cleaned

    def _uses_wol_defaults(self):
        return (
            self.plugin.manifest.plugin_id == "lanctl.network.wol"
            and "settingsSchema" not in self.raw
        )
