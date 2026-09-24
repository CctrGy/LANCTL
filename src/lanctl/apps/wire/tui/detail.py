"""Vistas de elementos desde la perspectiva de sus puertos físicos."""

from __future__ import annotations

from typing import Any

from rich.text import Text

from lanctl.apps.wire.topology import groups_for


def port_connections(records: list[dict[str, Any]]) -> dict[tuple[str, str], str]:
    connections: dict[tuple[str, str], str] = {}
    for record in records:
        data = record.get("data") or {}
        if data.get("type") != "wire":
            continue
        for endpoint in data.get("endpoints", []):
            connections[(str(endpoint.get("device")), str(endpoint.get("port")))] = record["id"]
    return connections


def element_detail(
    record: dict[str, Any],
    records: list[dict[str, Any]],
    width: int,
    *,
    selected_port: str | None = None,
    selected_endpoint: int = 0,
) -> Text:
    data = record.get("data") or {}
    element_type = str(data.get("type", "element"))
    if element_type == "wire":
        lines = _wire_lines(record)
    elif element_type == "rack":
        lines = _rack_lines(record, records, width)
    elif element_type == "device.panel":
        lines = _panel_link_lines(record, records)
    elif element_type == "device.outlet":
        lines = _outlet_link_lines(record, records)
    elif element_type == "device.switch":
        lines = _switch_lines(record, port_connections(records), width)
    elif element_type.startswith("device."):
        lines = _device_lines(record, port_connections(records))
    else:
        lines = _generic_lines(record)
    text = Text()
    for index, line in enumerate(lines):
        text.append(line, style="white")
        if index != len(lines) - 1:
            text.append("\n")
    selected_label = None
    if element_type.startswith("device.") and selected_port is not None:
        port = data.get("ports", {}).get(selected_port, {})
        selected_label = _endpoint(
            record["id"],
            selected_port,
            _special_port(port),
            reserve_marker=element_type == "device.switch",
        )
    elif element_type == "wire":
        sides = cable_sides(record)
        side = sides[min(selected_endpoint, 1)]
        selected_label = _side_label(side)
    elif element_type == "rack" and selected_port is not None:
        selected_label = f"U{int(selected_port):02}"
    if selected_label:
        start = (
            text.plain.rfind(selected_label)
            if element_type == "wire" and selected_endpoint == 1
            else text.plain.find(selected_label)
        )
        if start >= 0:
            if element_type == "wire":
                text.stylize("bold black on bright_cyan", start, start + len(selected_label))
            else:
                row_start = text.plain.rfind("\n", 0, start) + 1
                row_end = text.plain.find("\n", start)
                row_end = len(text.plain) if row_end < 0 else row_end
                row = text.plain[row_start:row_end]
                separator = row.find("]  [")
                if element_type == "device.switch" and separator >= 0:
                    second_start = row_start + separator + 3
                    selection_start, selection_end = (
                        (row_start, row_start + separator + 1)
                        if start < second_start
                        else (second_start, row_end)
                    )
                    text.stylize("bold black on bright_cyan", selection_start, selection_end)
                else:
                    text.stylize("bold black on bright_cyan", row_start, row_end)
    return text


def _heading(record: dict[str, Any]) -> str:
    data = record.get("data") or {}
    name = data.get("name") or data.get("alias") or "Sin nombre"
    return f"{record['id']}  {name}  [{data.get('type', 'element')}]"


def _device_lines(record: dict[str, Any], connections: dict[tuple[str, str], str]) -> list[str]:
    data = record["data"]
    ports = data.get("ports", {})
    endpoints = {
        name: _endpoint(record["id"], name, _special_port(port)) for name, port in ports.items()
    }
    endpoint_width = max((len(endpoint) for endpoint in endpoints.values()), default=0)
    return [
        _right_connection(
            endpoints[name].ljust(endpoint_width),
            connections.get((record["id"], name), "-"),
        )
        for name in ports
    ]


def _switch_lines(
    record: dict[str, Any], connections: dict[tuple[str, str], str], width: int
) -> list[str]:
    ports = record["data"].get("ports", {})
    names = list(ports)
    if len(names) <= 8:
        return [
            _right_connection(
                _endpoint(record["id"], name, _special_port(ports[name]), reserve_marker=True),
                connections.get((record["id"], name), "-"),
            )
            for name in names
        ]
    pairs = [names[index : index + 2] for index in range(0, len(names), 2)]
    paired_lines: list[str] = []
    for pair in pairs:
        left_name = pair[0]
        left = _left_connection(
            connections.get((record["id"], left_name), "-"),
            _endpoint(
                record["id"], left_name, _special_port(ports[left_name]), reserve_marker=True
            ),
        )
        if len(pair) == 1:
            paired_lines.append(left)
            continue
        right_name = pair[1]
        right = _right_connection(
            _endpoint(
                record["id"], right_name, _special_port(ports[right_name]), reserve_marker=True
            ),
            connections.get((record["id"], right_name), "-"),
        )
        paired_lines.append(f"{left}  {right}")
    if not paired_lines or max(map(len, paired_lines)) <= width:
        return paired_lines

    # En terminales estrechas cada puerto ocupa una fila, conservando la
    # orientación izquierda/derecha del frontal físico.
    lines: list[str] = []
    for index, name in enumerate(names):
        endpoint = _endpoint(record["id"], name, _special_port(ports[name]), reserve_marker=True)
        wire = connections.get((record["id"], name), "-")
        lines.append(
            _left_connection(wire, endpoint)
            if index % 2 == 0
            else _right_connection(endpoint, wire)
        )
    return lines


def _wire_lines(record: dict[str, Any]) -> list[str]:
    left, right = (_side_label(side) for side in cable_sides(record))
    return [f"[ {left} ) --- < {record['id']} > --- ( {right} ]"]


def _panel_link_lines(record: dict[str, Any], records: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for port, data in (record.get("data") or {}).get("ports", {}).items():
        outlet_id = data.get("outlet")
        outlet = next((item for item in records if item["id"] == outlet_id), None)
        lines.append(
            _structured_link_line(record, port, outlet, records, str(data.get("mark") or "-"))
        )
    return lines


def _outlet_link_lines(record: dict[str, Any], records: list[dict[str, Any]]) -> list[str]:
    panel_endpoint = (record.get("data") or {}).get("panel_endpoint") or {}
    panel = next((item for item in records if item["id"] == panel_endpoint.get("device")), None)
    if panel is None:
        return [f"[ ? ) --- < {record['id']} > --- ( {record['id']}.ROOM ]"]
    return [
        _structured_link_line(
            panel,
            str(panel_endpoint.get("port")),
            record,
            records,
            str((record.get("data") or {}).get("mark") or "-"),
        )
    ]


def _structured_link_line(
    panel: dict[str, Any],
    panel_port: str,
    outlet: dict[str, Any] | None,
    records: list[dict[str, Any]],
    mark: str,
) -> str:
    outlet_id = outlet["id"] if outlet else "?"
    panel_wire, panel_other = _external_connection(panel["id"], panel_port, records)
    room_wire, room_other = (
        _external_connection(outlet_id, "ROOM", records) if outlet else ("-", "?")
    )
    return (
        f"[ {panel_other} ) --- < {_wire(panel_wire).strip()} > --- ( {panel['id']}.{panel_port} ) "
        f"--- < {mark} > --- ( {outlet_id}.ROOM ) --- < {_wire(room_wire).strip()} > --- ( {room_other} ]"
    )


def _external_connection(
    device_id: str, port: str, records: list[dict[str, Any]]
) -> tuple[str, str]:
    wire_id = port_connections(records).get((device_id, port))
    if not wire_id:
        return "-", "?"
    wire = next((item for item in records if item["id"] == wire_id), None)
    if wire is None:
        return wire_id, "?"
    other = next(
        (
            side
            for side in cable_sides(wire)
            if side and not (side.get("device") == device_id and str(side.get("port")) == port)
        ),
        None,
    )
    return wire_id, _side_label(other)


def _endpoint(
    identifier: str, port: str, special: bool = False, *, reserve_marker: bool = False
) -> str:
    shown_port = port.zfill(2) if port.isdigit() else port
    marker = "*" if special else " " if reserve_marker else ""
    return f"{identifier}.{shown_port}{marker}"


def _wire(value: str) -> str:
    return f"{value:^7}"


def _left_connection(wire: str, endpoint: str) -> str:
    return f"[ {_wire(wire)} > --- ( {endpoint} ]"


def _right_connection(endpoint: str, wire: str) -> str:
    return f"[ {endpoint} ) --- < {_wire(wire)} ]"


def _special_port(port: dict[str, Any]) -> bool:
    return port.get("kind") in ("wire.fiber", "wire.dac")


def selectable_ports(record: dict[str, Any]) -> list[str]:
    data = record.get("data") or {}
    if data.get("type") == "rack":
        return [str(unit) for unit in range(1, max(0, int(data.get("size_units", 0))) + 1)]
    return list(data.get("ports", {}))


def rack_occupant(
    record: dict[str, Any], records: list[dict[str, Any]], unit: str | int
) -> dict[str, Any] | None:
    target_unit = int(unit)
    layout = _rack_layout_item(record, target_unit)
    if layout and layout.get("idf"):
        linked = next(
            (candidate for candidate in records if candidate["id"] == layout["idf"]), None
        )
        if linked is not None:
            return linked
    return next(
        (
            candidate
            for candidate in records
            if (candidate.get("data") or {}).get("location", {}).get("rack") == record["id"]
            and int((candidate.get("data") or {}).get("location", {}).get("unit", -1))
            == target_unit
        ),
        None,
    )


def _rack_layout_item(record: dict[str, Any], unit: int) -> dict[str, Any] | None:
    for item in (record.get("data") or {}).get("layout", []):
        start = int(item.get("unit", 0))
        height = max(1, int(item.get("height", 1)))
        if start <= unit < start + height:
            return item
    return None


def wire_for_port(record: dict[str, Any], records: list[dict[str, Any]], port: str) -> str | None:
    return port_connections(records).get((record["id"], port))


def cable_endpoints(record: dict[str, Any]) -> list[dict[str, str]]:
    if (record.get("data") or {}).get("type") != "wire":
        return []
    return list(record["data"].get("endpoints", []))


def cable_sides(record: dict[str, Any]) -> list[dict[str, Any] | None]:
    """Devuelve siempre los dos lados físicos, incluidos los que estén libres."""
    data = record.get("data") or {}
    if data.get("type") != "wire":
        return [None, None]
    endpoints = list(data.get("endpoints", []))
    source = data.get("source")
    if source:
        sides: list[dict[str, Any] | None] = [
            {"device": str(source), "port": None, "external": True}
        ]
        sides.append(endpoints[0] if endpoints else None)
        return sides
    return [*endpoints, None, None][:2]


def _side_label(side: dict[str, Any] | None) -> str:
    if side is None:
        return "?"
    if side.get("port") in (None, ""):
        return str(side.get("device", "?"))
    return f"{side['device']}.{side['port']}"


def element_sidebar(
    record: dict[str, Any],
    records: list[dict[str, Any]],
    *,
    selected_port: str | None = None,
    selected_endpoint: int = 0,
    general_selected: bool = False,
) -> Text:
    data = record.get("data") or {}
    element_type = str(data.get("type", "element"))
    lines = [element_type.removeprefix("device.").replace("_", " ").title()]
    if data.get("subtype"):
        lines.append(f"profile: {data['subtype']}")
    if general_selected:
        lines.extend(("> DATOS DEL ELEMENTO", "Enter: editar datos generales", ""))
    if data.get("name"):
        lines.append(str(data["name"]))
    if data.get("ip"):
        lines.append(f"ip: {data['ip']}")
    if data.get("lanipDevice"):
        lines.append(f"LANIP: {data['lanipDevice']}")
    groups = sorted(groups_for(record))
    if groups:
        lines.append(f"groups: {'/'.join(groups)}")
    if element_type == "rack":
        units = max(0, int(data.get("size_units", 0)))
        # En los racks esta columna funciona como leyenda física: cada línea
        # queda enfrentada a su U correspondiente en lugar de ser una ficha
        # genérica separada del dibujo.
        lines = []
        for unit in range(1, units + 1):
            layout = _rack_layout_item(record, unit)
            if layout:
                relative = unit - int(layout.get("unit", unit))
                labels = layout.get("label_lines")
                if isinstance(labels, list):
                    lines.append(str(labels[relative]) if relative < len(labels) else "")
                    continue
                lines.append(
                    str(layout.get("label") or layout.get("idf") or "") if relative == 0 else ""
                )
                continue
            occupant = rack_occupant(record, records, unit)
            if occupant:
                occupant_data = occupant.get("data") or {}
                label = occupant_data.get("rack_label") or occupant["id"]
                lines.append(str(label))
            else:
                lines.append("")
    elif element_type.startswith("device."):
        ports = data.get("ports", {})
        connected = port_connections(records)
        lines.extend(
            (
                f"ports: {len(ports)}",
                f"connected: {sum((record['id'], name) in connected for name in ports)}",
            )
        )
        location = data.get("location") or {}
        if location.get("rack"):
            lines.append(f"rack: {location['rack']} / U{location.get('unit', '-')}")
        selected_data = ports.get(selected_port, {}) if selected_port in ports else {}
        speeds = selected_data.get("speeds") or data.get("speeds") or ["10M", "100M", "1G"]
        lines.extend(("", "speeds:", "  " + "/".join(map(str, speeds))))
        if selected_port in ports:
            port = ports[selected_port]
            wire = wire_for_port(record, records, selected_port) or "-"
            connector = (
                "SFP/DAC"
                if port.get("kind") == "wire.dac"
                else "Fibra"
                if port.get("kind") == "wire.fiber"
                else "RJ45"
            )
            lines.extend(
                (
                    "",
                    f"PORT {selected_port}{'*' if _special_port(port) else ''}",
                    f"connector: {connector}",
                    f"medium: {port.get('kind', '-')}",
                )
            )
            if port.get("poe"):
                lines.append("POE")
            lines.append(f"wire: {wire}")
            lines.extend(("", "Enter: open cable"))
    elif element_type == "wire":
        sides = cable_sides(record)
        lines.extend(
            (
                f"medium: {data.get('kind', '-')}",
                f"endpoints: {sum(side is not None for side in sides)}/2",
                "",
            )
        )
        for index, side in enumerate(sides):
            marker = ">" if index == selected_endpoint else " "
            lines.append(f"{marker} {_side_label(side) if side else '(free)'}")
        lines.extend(("", "←/→: select side", "F3/Enter: open device", "Backspace: back"))
    return Text("\n".join(lines), style="white")


def combine_with_sidebar(main: Text, sidebar: Text, available_width: int) -> Text:
    """Compone dos columnas o apila INFO si la terminal es estrecha."""
    main_rows = list(main.split("\n"))
    side_rows = list(sidebar.split("\n"))
    main_width = max((row.cell_len for row in main_rows), default=0)
    side_width = max((row.cell_len for row in side_rows), default=0)
    if main_width + side_width + 5 > available_width:
        result = main.copy()
        result.append("\n\n--- INFO ---\n", style="bright_cyan")
        result.append_text(sidebar)
        return result
    result = Text()
    row_count = max(len(main_rows), len(side_rows))
    for index in range(row_count):
        left = main_rows[index].copy() if index < len(main_rows) else Text()
        left.truncate(main_width, pad=True)
        result.append_text(left)
        result.append("  │  ", style="bright_cyan")
        if index < len(side_rows):
            result.append_text(side_rows[index])
        if index != row_count - 1:
            result.append("\n")
    return result


def _generic_lines(record: dict[str, Any]) -> list[str]:
    data = record.get("data") or {}
    lines = [_heading(record), ""]
    for key, value in data.items():
        if key not in ("name", "type"):
            lines.append(f"{key}: {value}")
    return lines


def _rack_lines(record: dict[str, Any], records: list[dict[str, Any]], width: int) -> list[str]:
    """Dibuja una fila por unidad; el recorte vertical lo gestiona el modal."""
    units = max(0, int((record.get("data") or {}).get("size_units", 0)))
    # Reserva los dos indicadores Uxx y deja que el cuerpo aproveche el ancho.
    body_width = max(24, min(54, width - 12))
    lines: list[str] = []
    for unit in range(1, units + 1):
        label = f"U{unit:02}"
        layout = _rack_layout_item(record, unit)
        occupant = rack_occupant(record, records, unit)
        body = (
            _rack_layout_visual(layout, unit, body_width)
            if layout
            else _rack_element_visual(occupant, body_width)
            if occupant
            else " " * body_width
        )
        lines.append(f"{label}  {body}  {label}")
    return lines or ["(rack sin unidades)"]


def _rack_element_visual(record: dict[str, Any], width: int) -> str:
    data = record.get("data") or {}
    identifier = record["id"]
    element_type = str(data.get("type", "element"))
    if element_type == "panel":
        # Agrupa visualmente las tomas como los bloques de un patch panel.
        available = max(1, width - 2)
        group = "[][][][][][]"
        motif = (group + " ") * max(1, available // (len(group) + 1))
        return motif[:width].center(width)
    elif element_type == "device.switch":
        motif = "8888 8888 8888"
        return f"[ {motif:^{width - 4}} ]"
    else:
        motif = str(
            data.get("name") or data.get("alias") or element_type.removeprefix("device.")
        ).title()
    content = f"{identifier}  {motif}"
    if len(content) > width - 4:
        content = content[: max(1, width - 7)] + "..."
    return f"[ {content:^{width - 4}} ]"


def _rack_layout_visual(item: dict[str, Any] | None, unit: int, width: int) -> str:
    if not item:
        return " " * width
    kind = str(item.get("kind", "element"))
    start = int(item.get("unit", unit))
    height = max(1, int(item.get("height", 1)))
    relative = unit - start
    if kind in ("tray", "case") and height > 1:
        if relative == 0:
            if kind == "tray":
                return "│" + " " * (width - 2) + "│"
            return "┌" + "─" * (width - 2) + "┐"
        if relative == height - 1:
            return "└" + "─" * (width - 2) + "┘"
        return "│" + " " * (width - 2) + "│"
    if kind == "panel":
        group = "[][][][][][]"
        return ((group + " ") * max(1, width // (len(group) + 1)))[:width].ljust(width)
    if kind == "switch":
        return f"[ {'8888 8888 8888':^{width - 4}} ]"
    if kind == "pdu":
        sockets = "     ".join("O" for _ in range(8))
        return f"[ {sockets:^{width - 4}} ]"
    return " " * width


__all__ = [
    "cable_endpoints",
    "cable_sides",
    "combine_with_sidebar",
    "element_detail",
    "element_sidebar",
    "port_connections",
    "rack_occupant",
    "selectable_ports",
    "wire_for_port",
]
