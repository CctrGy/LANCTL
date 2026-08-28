"""Editor de campos para el panel lateral de las ventanas virtuales."""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any

from rich.text import Text


@dataclass(frozen=True)
class EditableField:
    label: str
    path: tuple[str | int, ...]
    value: Any

    @property
    def shown_value(self) -> str:
        if isinstance(self.value, list):
            return "/".join(map(str, self.value))
        if self.value is None:
            return ""
        return str(self.value)


def editable_fields(
    record: dict[str, Any], selected_port: str | None = None, selected_endpoint: int = 0
) -> list[EditableField]:
    data = record.get("data") or {}
    fields = [
        EditableField("name", ("name",), data.get("name")),
        EditableField("alias", ("alias",), data.get("alias")),
        EditableField("description", ("description",), data.get("description")),
    ]
    element_type = str(data.get("type", "element"))
    if element_type.startswith("device."):
        fields.extend(
            (
                EditableField("ip", ("ip",), data.get("ip")),
                EditableField("speeds", ("speeds",), data.get("speeds", [])),
            )
        )
        location = data.get("location") or {}
        fields.extend(
            (
                EditableField("rack", ("location", "rack"), location.get("rack")),
                EditableField("unit", ("location", "unit"), location.get("unit")),
            )
        )
        port = (data.get("ports") or {}).get(selected_port or "", {})
        if selected_port is not None:
            fields.extend(
                (
                    EditableField(
                        f"{selected_port}.kind", ("ports", selected_port, "kind"), port.get("kind")
                    ),
                    EditableField(
                        f"{selected_port}.poe",
                        ("ports", selected_port, "poe"),
                        port.get("poe", False),
                    ),
                    EditableField(
                        f"{selected_port}.speeds",
                        ("ports", selected_port, "speeds"),
                        port.get("speeds", []),
                    ),
                )
            )
    elif element_type == "wire":
        fields.extend(
            (
                EditableField("kind", ("kind",), data.get("kind")),
                EditableField("source", ("source",), data.get("source")),
            )
        )
        endpoints = data.get("endpoints", [])
        source_offset = 1 if data.get("source") else 0
        index = selected_endpoint - source_offset
        if 0 <= index < len(endpoints):
            endpoint = endpoints[index]
            fields.extend(
                (
                    EditableField(
                        f"end{index + 1}.device",
                        ("endpoints", index, "device"),
                        endpoint.get("device"),
                    ),
                    EditableField(
                        f"end{index + 1}.port", ("endpoints", index, "port"), endpoint.get("port")
                    ),
                )
            )
    elif element_type == "rack":
        fields.append(EditableField("size_units", ("size_units",), data.get("size_units")))
    else:
        location = data.get("location") or {}
        fields.extend(
            (
                EditableField("rack", ("location", "rack"), location.get("rack")),
                EditableField("unit", ("location", "unit"), location.get("unit")),
            )
        )
    return fields


def editor_view(fields: list[EditableField], selection: int, buffer: str | None = None) -> Text:
    text = Text("EDIT\n", style="bold bright_cyan")
    for index, field in enumerate(fields):
        shown = buffer if buffer is not None and index == selection else field.shown_value
        line = f"{field.label}: {shown}"
        start = len(text)
        text.append(line[:48])
        if index == selection:
            text.stylize("bold black on bright_cyan", start, len(text))
        if index != len(fields) - 1:
            text.append("\n")
    text.append("\n\nEnter: edit/save\nTab: return\nEsc: cancel", style="dim")
    return text


def connector_actions(connected_wire: str | None) -> list[str]:
    return ["Desconectar", "Mover"] if connected_wire else ["Conectar"]


def actions_view(actions: list[str], selection: int, buffer: str | None = None) -> Text:
    text = Text("ACTIONS\n", style="bold bright_cyan")
    for index, action in enumerate(actions):
        suffix = ""
        if buffer is not None and index == selection:
            suffix = f": {buffer}"
        start = len(text)
        text.append(f"{action}{suffix}")
        if index == selection:
            text.stylize("bold black on bright_cyan", start, len(text))
        if index != len(actions) - 1:
            text.append("\n")
    text.append("\n\nEnter: execute", style="dim")
    if buffer is not None:
        text.append("/confirm\nEsc: cancel", style="dim")
    text.append("\nTab: return to view", style="dim")
    return text


def set_field(data: dict[str, Any], field: EditableField, raw_value: str) -> None:
    if field.label == "ip" and raw_value.strip():
        try:
            ip_address(raw_value.strip())
        except ValueError as error:
            raise ValueError("la dirección IP no es válida") from error
    value = _parse_value(raw_value, field.value)
    current: Any = data
    for part in field.path[:-1]:
        if isinstance(part, int):
            while len(current) <= part:
                current.append({})
            current = current[part]
        else:
            if part not in current:
                # Los endpoints son listas; el resto de rutas intermedias son mapas.
                current[part] = [] if part == "endpoints" else {}
            current = current[part]
    final = field.path[-1]
    if isinstance(final, int):
        current[final] = value
    elif value == "" and field.value is None:
        current[final] = None
    else:
        current[final] = value


def _parse_value(raw: str, previous: Any) -> Any:
    stripped = raw.strip()
    if isinstance(previous, bool):
        normalized = stripped.casefold()
        if normalized not in ("true", "false", "yes", "no", "1", "0", "si", "sí"):
            raise ValueError("usa yes/no o true/false")
        return normalized in ("true", "yes", "1", "si", "sí")
    if isinstance(previous, int):
        return int(stripped)
    if isinstance(previous, list):
        return [item.strip() for item in stripped.replace(",", "/").split("/") if item.strip()]
    return stripped


__all__ = [
    "EditableField",
    "actions_view",
    "connector_actions",
    "editable_fields",
    "editor_view",
    "set_field",
]
