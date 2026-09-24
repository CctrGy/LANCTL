"""Editor de campos para el panel lateral de las ventanas virtuales."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from ipaddress import ip_address
from typing import Any

from rich.text import Text

from lanctl.apps.wire.topology import apply_device_preset, build_ports, resize_port_pattern


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
        EditableField("type", ("type",), data.get("type", "element")),
        EditableField("name", ("name",), data.get("name")),
        EditableField("alias", ("alias",), data.get("alias")),
        EditableField("description", ("description",), data.get("description")),
        EditableField("groups", ("groups",), data.get("groups", [])),
        EditableField("lanipDevice", ("lanipDevice",), data.get("lanipDevice")),
    ]
    element_type = str(data.get("type", "element"))
    if element_type.startswith("device."):
        ports = data.get("ports") or {}
        fields.extend(
            (
                EditableField(
                    "portCount",
                    ("portCount",),
                    len([name for name in ports if name != "FIBER"]),
                ),
                EditableField("portNaming", ("portNaming",), data.get("portNaming", "LAN{n}")),
                EditableField(
                    "portTemplate.kind",
                    ("portTemplate", "kind"),
                    (data.get("portTemplate") or {}).get("kind", "wire.copper"),
                ),
                EditableField(
                    "portTemplate.poe",
                    ("portTemplate", "poe"),
                    (data.get("portTemplate") or {}).get("poe", False),
                ),
                EditableField(
                    "portTemplate.speeds",
                    ("portTemplate", "speeds"),
                    (data.get("portTemplate") or {}).get("speeds", []),
                ),
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
        port = ports.get(selected_port or "", {})
        if selected_port is not None:
            fields.extend(
                (
                    EditableField(
                        f"{selected_port}.name", ("ports", selected_port, "name"), selected_port
                    ),
                    EditableField(
                        f"{selected_port}.position",
                        ("ports", selected_port, "position"),
                        list(ports).index(selected_port) + 1,
                    ),
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
                    EditableField(
                        "Eliminar puerto", ("ports", selected_port), "Enter para confirmar"
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
    text = Text("EDITAR DATOS\n", style="bold bright_cyan")
    last_section = ""
    for index, field in enumerate(fields):
        section = _section_for(field)
        if section != last_section:
            if index:
                text.append("\n")
            text.append(f"{section}\n", style="bold bright_white")
            last_section = section
        shown = buffer if buffer is not None and index == selection else field.shown_value
        line = f"{field.label}: {shown}"
        start = len(text)
        text.append(line[:48])
        if index == selection:
            text.stylize("bold black on bright_cyan", start, len(text))
        if index != len(fields) - 1:
            text.append("\n")
    text.append("\n\nEnter: editar/guardar\nEsc/Tab: volver a opciones", style="dim")
    return text


def element_options_view(
    identifier: str, port: str | None, wire: str | None, selection: int, focused: bool
) -> Text:
    """Menú visible de la ficha física con una acción por pulsación de Enter."""
    title = f"OPCIONES · {identifier}" if port is None else f"OPCIONES · {port}"
    text = Text(title + "\n", style="bold bright_cyan")
    choices = [
        "Datos generales del elemento",
        "Datos del puerto",
        "Conectar al puerto",
        "Eliminar elemento",
    ]
    if wire:
        choices.extend((f"Editar cable {wire}", "Desconectar cable", "Mover cable"))
    for index, choice in enumerate(choices):
        start = len(text)
        text.append(f"{'▶' if focused and index == selection else ' '} {choice}")
        if focused and index == selection:
            text.stylize("bold black on bright_cyan", start, len(text))
        text.append("\n")
    text.append(
        "\n↑/↓ opción · Enter abrir · F3 seguir · Esc volver"
        if focused
        else "\n↑/↓ puerto · F3 seguir cable · Tab/Enter opciones · Esc cerrar",
        style="dim",
    )
    return text


def _section_for(field: EditableField) -> str:
    """Agrupa edición global, plantilla y excepción del puerto seleccionado."""
    if field.label in {"portCount", "portNaming"} or field.label.startswith("portTemplate."):
        return "PUERTOS · PLANTILLA COMÚN"
    if len(field.path) >= 2 and field.path[0] == "ports":
        return f"PUERTO · {field.path[1]} · EXCEPCIÓN"
    if field.label.startswith("end"):
        return "EXTREMO DEL CABLE"
    return "DATOS DEL ELEMENTO"


def field_options(field: EditableField) -> tuple[str, ...]:
    """Opciones guiadas para propiedades físicas, sin bloquear edición libre."""
    if field.label == "type":
        return (
            "router-4rj-1fb",
            "switch-12",
            "switch-24",
            "switch-48",
            "pc-1",
            "pc-2",
            "server-2",
            "panel",
            "outlet",
            "rack",
            "wire",
        )
    if field.label == "portCount":
        return ("1", "2", "4", "5", "8", "12", "24", "48")
    if field.label == "portNaming":
        return (
            "LAN{n}",
            "WAN{n}",
            "X{n}",
            "ETH{n}",
            "PORT{n}",
            "X{n}:24,XG{a}:4",
            "LAN{n}:4,FIBER",
        )
    if field.label == "groups":
        return ("WIRE", "SWITCHS", "PC", "LAB", "OFFICE", "RACK")
    if field.label.endswith(".kind") or field.label == "kind":
        return ("RJ45", "Fibra", "SFP/DAC")
    if field.label.endswith(".poe"):
        return ("yes", "no")
    return ()


def options_view(
    field: EditableField,
    selected: int,
    choices: tuple[str, ...] | None = None,
    *,
    filter_text: str | None = None,
) -> Text:
    """Lista contextual renderizada junto al detalle del elemento."""
    options = choices if choices is not None else field_options(field)
    text = Text(f"OPCIONES · {field.label}\n", style="bold bright_cyan")
    if filter_text is not None:
        text.append(f"Filtrar IDF: {filter_text}▌\n", style="bright_white")
        if not options:
            text.append("(sin coincidencias)\n", style="dim")
    for index, option in enumerate(options):
        start = len(text)
        text.append(option or "(vacío)")
        if index == selected:
            text.stylize("bold black on bright_cyan", start, len(text))
        if index < len(options) - 1:
            text.append("\n")
    hint = (
        "↑/↓ seleccionar · Enter conectar · Esc volver"
        if filter_text is not None
        else "↑/↓ seleccionar · Enter aplicar · ← volver"
    )
    text.append(f"\n\n{hint}", style="dim")
    return text


def connector_actions(connected_wire: str | None) -> list[str]:
    return ["Desconectar", "Mover", "Editar cable"] if connected_wire else ["Conectar"]


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


def connection_browser_view(
    cables: tuple[str, ...], selection: int, query: str, *, max_rows: int = 12
) -> Text:
    """Mantiene la acción y los IDF compatibles visibles en paneles contiguos."""
    text = Text("ACTIONS", style="bold bright_cyan")
    text.append(" " * 10 + "│ ", style="bright_cyan")
    text.append(f"CABLES COMPATIBLES · {len(cables)}\n", style="bold bright_cyan")
    text.append("Conectar", style="bold black on bright_cyan")
    text.append(" " * 9 + "│ ", style="bright_cyan")
    text.append(f"Buscar IDF: {query}▌\n", style="bright_white")
    start = max(0, min(selection - max_rows + 1, len(cables) - max_rows))
    visible = cables[start : start + max_rows]
    for index, cable in enumerate(visible, start=start):
        text.append(" " * 17 + "│ ", style="bright_cyan")
        line_start = len(text)
        text.append(f"{'▶ ' if index == selection else '  '}{cable}")
        if index == selection:
            text.stylize("bold black on bright_cyan", line_start, len(text))
        text.append("\n")
    if not cables:
        text.append(" " * 17 + "│ (sin coincidencias)\n", style="dim")
    text.append("\n↑/↓ seleccionar · Enter conectar · Esc volver", style="dim")
    return text


def set_field(data: dict[str, Any], field: EditableField, raw_value: str) -> None:
    if field.label.endswith(".kind") or field.label == "kind":
        raw_value = {
            "rj45": "wire.copper",
            "fibra": "wire.fiber",
            "sfp/dac": "wire.dac",
        }.get(raw_value.strip().casefold(), raw_value)
    if field.label == "type":
        updated = apply_device_preset(data, raw_value)
        updated.pop("subtype", None)
        data.clear()
        data.update(updated)
        return
    if field.label in {"portCount", "portNaming"}:
        count = (
            int(raw_value)
            if field.label == "portCount"
            else len([name for name in (data.get("ports") or {}) if name != "FIBER"])
        )
        pattern = (
            raw_value.strip() if field.label == "portNaming" else data.get("portNaming", "LAN{n}")
        )
        existing = data.get("ports") or {}
        template = data.get("portTemplate") or {}
        if field.label == "portCount":
            if not 1 <= count <= 96:
                raise ValueError("el número de puertos debe estar entre 1 y 96")
            pattern = resize_port_pattern(pattern, count)
            regular = {name: value for name, value in existing.items() if name != "FIBER"}
            if count < len(regular):
                regular = dict(list(regular.items())[:count])
            elif count > len(regular):
                candidates = build_ports(
                    96,
                    pattern,
                    kind=template.get("kind", "wire.copper"),
                    poe=bool(template.get("poe", False)),
                    speeds=template.get("speeds", []),
                )
                for name, value in candidates.items():
                    if len(regular) >= count:
                        break
                    regular.setdefault(name, value)
            if "FIBER" in existing:
                regular["FIBER"] = existing["FIBER"]
            data["ports"] = regular
            data["portNaming"] = pattern
            return
        proposed = build_ports(
            count,
            pattern,
            fiber="FIBER" in existing,
            kind=template.get("kind", "wire.copper"),
            poe=bool(template.get("poe", False)),
            speeds=template.get("speeds", []),
        )
        data["ports"] = {name: existing.get(name, value) for name, value in proposed.items()}
        data["portNaming"] = pattern
        return
    if field.label.startswith("portTemplate."):
        template = dict(data.get("portTemplate") or {})
        key = str(field.path[-1])
        template[key] = _parse_value(raw_value, field.value)
        data["portTemplate"] = template
        for name, port in (data.get("ports") or {}).items():
            if name != "FIBER":
                port[key] = deepcopy(template[key])
        return
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
    "connection_browser_view",
    "connector_actions",
    "editable_fields",
    "editor_view",
    "element_options_view",
    "field_options",
    "options_view",
    "set_field",
]
