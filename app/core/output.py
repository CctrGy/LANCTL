from __future__ import annotations

import csv
import html
import io
import ipaddress
import json
import os
import sys
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Mapping
from pathlib import Path

from colorama import Fore, Style, just_fix_windows_console

from app.core.layout import fit_text, shrink_widths, terminal_columns, wrapped_lines
from app.models import Device

FIELDS = (
    "IP",
    "cnf",
    "ALIAS",
    "MAC",
    "NAME",
    "GROUP",
    "description",
    "manufacturer",
    "defaultName",
    "discovery",
    "discoveryMethods",
    "lastDiscovery",
    "lastSeen",
    "responseMs",
)
TABLE_COLUMNS = (
    ("IP", "IP"),
    ("cnf", "cnf"),
    ("alias", "ALIAS"),
    ("mac", "MAC"),
    ("name", "NAME"),
    ("group", "GROUP"),
    ("description", "description"),
)
TABLE_MIN_WIDTHS = {
    "IP": 13,
    "cnf": 3,
    "ALIAS": 13,
    "MAC": 19,
    "NAME": 17,
    "GROUP": 8,
    "description": 42,
}
TABLE_HARD_MIN_WIDTHS = {
    "IP": 13,
    "cnf": 3,
    "ALIAS": 5,
    "MAC": 17,
    "NAME": 5,
    "GROUP": 5,
    "description": 8,
    "manufacturer": 8,
    "deviceId": 8,
    "protocols": 7,
    "discovery": 8,
    "discoveryMethods": 8,
    "lastDiscovery": 8,
    "lastSeen": 12,
    "responseMs": 7,
}
SHRINK_PRIORITY = (
    "description",
    "manufacturer",
    "NAME",
    "ALIAS",
    "GROUP",
    "lastSeen",
    "lastDiscovery",
    "discoveryMethods",
    "discovery",
    "protocols",
    "deviceId",
    "IP",
    "MAC",
    "responseMs",
)
MANUFACTURER_COLUMN = ("manufacturer", "manufacturer")
EXTRA_COLUMNS = (
    ("device-id", "deviceId"),
    ("protocols", "protocols"),
    ("discovery", "discovery"),
    ("detected-by", "discoveryMethods"),
    ("last-discovery", "lastDiscovery"),
    ("last-seen", "lastSeen"),
    ("ms", "responseMs"),
)
AVAILABLE_COLUMNS = {
    label.casefold(): key for label, key in (*TABLE_COLUMNS, MANUFACTURER_COLUMN, *EXTRA_COLUMNS)
}
FIELD_COLORS = {
    "IP": Fore.LIGHTBLUE_EX,
    "cnf": Fore.BLUE,
    "ALIAS": Fore.LIGHTYELLOW_EX,
    "MAC": Fore.LIGHTMAGENTA_EX,
    "NAME": Fore.LIGHTGREEN_EX,
    "GROUP": Fore.LIGHTYELLOW_EX,
    "description": Fore.LIGHTWHITE_EX,
    "manufacturer": Fore.LIGHTWHITE_EX,
    "deviceId": Fore.LIGHTWHITE_EX,
    "protocols": Fore.LIGHTCYAN_EX,
    "discovery": Fore.LIGHTCYAN_EX,
    "discoveryMethods": Fore.LIGHTCYAN_EX,
    "lastDiscovery": Fore.LIGHTCYAN_EX,
    "lastSeen": Fore.LIGHTBLACK_EX,
    "responseMs": Fore.LIGHTCYAN_EX,
}
DARK_FIELD_COLORS = {
    "IP": Fore.BLUE,
    "cnf": Fore.BLUE,
    "ALIAS": Fore.YELLOW,
    "MAC": Fore.MAGENTA,
    "NAME": Fore.GREEN,
    "GROUP": Fore.YELLOW,
    "description": Fore.LIGHTBLACK_EX,
    "manufacturer": Fore.LIGHTBLACK_EX,
    "deviceId": Fore.LIGHTBLACK_EX,
    "protocols": Fore.CYAN,
    "discovery": Fore.CYAN,
    "discoveryMethods": Fore.CYAN,
    "lastDiscovery": Fore.CYAN,
    "lastSeen": Fore.LIGHTBLACK_EX,
    "responseMs": Fore.CYAN,
}
# Constante conservada para extensiones externas que aún puedan importarla; las
# filas inactivas ya no utilizan el efecto de tachado.
STRIKETHROUGH = "\x1b[9m"
CNF_COLORS = {
    "O": Fore.LIGHTGREEN_EX,
    "X": Fore.LIGHTRED_EX,
    "-": Fore.LIGHTYELLOW_EX,
    "S": Fore.LIGHTCYAN_EX,
    "F": Fore.LIGHTMAGENTA_EX,
    "@": Fore.LIGHTMAGENTA_EX,
}
DARK_CNF_COLORS = {
    "O": Fore.GREEN,
    "X": Fore.RED,
    "-": Fore.YELLOW,
    "S": Fore.CYAN,
    "F": Fore.MAGENTA,
    "@": Fore.MAGENTA,
}

just_fix_windows_console()


def _export_value(row: Mapping[str, object], key: str) -> str:
    value = row.get(key, "")
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


def _render_json(rows, fields):
    output_rows = (
        [{field: row.get(field, "") for field in fields} for row in rows]
        if fields is not None
        else rows
    )
    return json.dumps(output_rows, indent=2, ensure_ascii=False) + "\n"


def _render_csv(rows, fields):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=fields or FIELDS,
        lineterminator="\n",
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def _render_html(rows, fields):
    header_cells = "".join(f"<th>{html.escape(field)}</th>" for field in fields)
    body_rows = "".join(
        "<tr>"
        + "".join(f"<td>{html.escape(_export_value(row, field))}</td>" for field in fields)
        + "</tr>"
        for row in rows
    )
    return (
        '<!doctype html>\n<html><head><meta charset="utf-8">'
        "<title>LANCTL</title></head><body><table><thead><tr>"
        f"{header_cells}</tr></thead><tbody>{body_rows}</tbody></table></body></html>\n"
    )


def _render_xml(rows, fields):
    root = ET.Element("lanctl")
    for row in rows:
        item = ET.SubElement(root, "element")
        for field in fields:
            ET.SubElement(item, field).text = _export_value(row, field)
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


def _display_value(row: Mapping[str, object], key: str) -> str:
    value = row.get(key, "")
    if key == "responseMs":
        return "-" if value in (None, "") else f"{float(value):.1f}"
    if key in ("GROUP", "protocols", "discoveryMethods") and isinstance(value, list):
        return ",".join(str(item) for item in value) or "-"
    if key == "cnf":
        if isinstance(value, bool):
            return "O" if value else "X"
        return str(value or "X").upper()
    return str(value)


def _table_columns(selected_columns, include_manufacturer):
    if selected_columns is not None:
        return tuple((column, AVAILABLE_COLUMNS[column]) for column in selected_columns)
    return (*TABLE_COLUMNS, MANUFACTURER_COLUMN) if include_manufacturer else TABLE_COLUMNS


def _table_widths(rows, fields, labels, max_width):
    widths = {
        field: max(
            TABLE_MIN_WIDTHS.get(field, 0),
            len(labels[field]),
            *(len(_display_value(row, field)) for row in rows),
        )
        for field in fields
    }
    return shrink_widths(widths, TABLE_HARD_MIN_WIDTHS, fields, max_width, SHRINK_PRIORITY)


def _range_boundaries(rows, section_ip_range):
    if not section_ip_range:
        return None, None
    try:
        raw_start, raw_end = section_ip_range.split("-", 1)
        start = ipaddress.IPv4Address(raw_start.strip())
        end = ipaddress.IPv4Address(raw_end.strip())
    except ValueError:
        return None, None

    indexes = set()
    for index, row in enumerate(rows):
        try:
            address = ipaddress.IPv4Address(str(row.get("IP", "")))
        except ipaddress.AddressValueError:
            continue
        if start <= address <= end:
            indexes.add(index)
    return (min(indexes), max(indexes)) if indexes else (None, None)


def _padded_value(row, field, widths):
    value = fit_text(_display_value(row, field), widths[field])
    if field == "cnf":
        return value.center(widths[field])
    if field == "responseMs":
        # Todos los valores tienen un decimal; el punto queda alineado.
        return value.rjust(widths[field])
    return value.ljust(widths[field])


def _row_color(field, row, index, inactive, color_rows):
    color_code = DARK_FIELD_COLORS[field] if inactive else FIELD_COLORS[field]
    named_colors = {"blue": Fore.BLUE, "white": Fore.WHITE, "red": Fore.RED}
    if not inactive and index < len(color_rows) and field in color_rows[index]:
        return named_colors[color_rows[index][field]]
    if field == "cnf":
        state = _display_value(row, field)
        return (DARK_CNF_COLORS if inactive else CNF_COLORS).get(
            state, Fore.RED if inactive else Fore.LIGHTRED_EX
        )
    return color_code


def _render_stacked(rows, fields, labels, activity, color, max_width):
    label_width = min(max(len(labels[field]) for field in fields), max(3, (max_width or 40) // 3))
    value_width = max(1, (max_width or 40) - label_width - 3)
    separator = "-" * (max_width or 40)
    output = []
    for index, row in enumerate(rows):
        if index:
            output.append(separator)
        inactive = index < len(activity) and not activity[index]
        style = Style.DIM if inactive else Style.BRIGHT
        for field in fields:
            parts = wrapped_lines(_display_value(row, field), value_width)
            label = fit_text(labels[field], label_width).ljust(label_width)
            color_code = DARK_FIELD_COLORS[field] if inactive else FIELD_COLORS[field]
            if field == "cnf":
                color_code = (DARK_CNF_COLORS if inactive else CNF_COLORS).get(
                    _display_value(row, field), color_code
                )
            for part_index, part in enumerate(parts):
                prefix = f"{label} : " if part_index == 0 else " " * (label_width + 3)
                output.append(
                    f"{Style.BRIGHT}{Fore.CYAN}{prefix}{Style.RESET_ALL}"
                    f"{style}{color_code}{part}{Style.RESET_ALL}"
                    if color
                    else prefix + part
                )
    return "\n".join(output) + ("\n" if output else "")


def _render_color_table(
    rows, fields, labels, widths, activity, color_rows, first_range_index, last_range_index
):
    header = "  ".join(
        f"{Style.BRIGHT}{Fore.CYAN}"
        f"{fit_text(labels[field], widths[field]).ljust(widths[field])}"
        f"{Style.RESET_ALL}"
        for field in fields
    )
    separator = Style.DIM + "  ".join("-" * widths[field] for field in fields) + Style.RESET_ALL
    body = []
    for index, row in enumerate(rows):
        if index == first_range_index:
            body.append(separator)
        inactive = index < len(activity) and not activity[index]
        style = Style.DIM if inactive else Style.BRIGHT
        cells = [
            f"{style}{_row_color(field, row, index, inactive, color_rows)}"
            f"{_padded_value(row, field, widths)}{Style.RESET_ALL}"
            for field in fields
        ]
        body.append("  ".join(cells))
        if index == last_range_index:
            body.append(separator)
    return header, separator, body


def _render_plain_table(rows, fields, labels, widths, first_range_index, last_range_index):
    header = "  ".join(
        fit_text(labels[field], widths[field]).ljust(widths[field]) for field in fields
    )
    separator = "  ".join("-" * widths[field] for field in fields)
    body = []
    for index, row in enumerate(rows):
        if index == first_range_index:
            body.append(separator)
        body.append("  ".join(_padded_value(row, field, widths) for field in fields))
        if index == last_range_index:
            body.append(separator)
    return header, separator, body


def render_records(
    records: Iterable[Mapping[str, str]],
    output_format: str,
    color: bool = False,
    cell_colors: Iterable[Mapping[str, str]] | None = None,
    include_manufacturer: bool = False,
    columns: Iterable[str] | None = None,
    active_rows: Iterable[bool] | None = None,
    section_ip_range: str | None = None,
    max_width: int | None = None,
) -> str:
    rows = [record.to_dict() if isinstance(record, Device) else dict(record) for record in records]
    color_rows = list(cell_colors) if cell_colors is not None else []
    activity = list(active_rows) if active_rows is not None else []
    selected_columns = normalize_columns(columns) if columns is not None else None
    selected_fields = (
        [AVAILABLE_COLUMNS[column] for column in selected_columns]
        if selected_columns is not None
        else None
    )

    if output_format == "json":
        return _render_json(rows, selected_fields)

    if output_format == "csv":
        return _render_csv(rows, selected_fields)

    if output_format in ("html", "xml"):
        export_fields = selected_fields or list(FIELDS)
        return (
            _render_html(rows, export_fields)
            if output_format == "html"
            else _render_xml(rows, export_fields)
        )

    visible_columns = _table_columns(selected_columns, include_manufacturer)
    fields = [key for _, key in visible_columns]
    labels = {key: label for label, key in visible_columns}
    widths, stacked = _table_widths(rows, fields, labels, max_width)
    first_range_index, last_range_index = _range_boundaries(rows, section_ip_range)

    if stacked:
        return _render_stacked(rows, fields, labels, activity, color, max_width)

    if color:
        header, separator, body = _render_color_table(
            rows,
            fields,
            labels,
            widths,
            activity,
            color_rows,
            first_range_index,
            last_range_index,
        )
    else:
        header, separator, body = _render_plain_table(
            rows, fields, labels, widths, first_range_index, last_range_index
        )
    return "\n".join((header, separator, *body)) + "\n"


def write_records(
    records: Iterable[Mapping[str, str]],
    output_format: str,
    destination: str | None = None,
    include_manufacturer: bool = False,
    columns: Iterable[str] | None = None,
    active_rows: Iterable[bool] | None = None,
    section_ip_range: str | None = None,
) -> None:
    use_color = (
        output_format == "table"
        and destination is None
        and sys.stdout.isatty()
        and "NO_COLOR" not in os.environ
    )
    content = render_records(
        records,
        output_format,
        color=use_color,
        include_manufacturer=include_manufacturer,
        columns=columns,
        active_rows=active_rows,
        section_ip_range=section_ip_range,
        max_width=terminal_columns(sys.stdout)
        if output_format == "table" and destination is None
        else None,
    )
    if destination:
        Path(destination).expanduser().write_text(content, encoding="utf-8")
    else:
        print(content, end="", flush=True)


def normalize_columns(columns: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for raw in columns:
        for value in str(raw).split(","):
            name = value.strip().casefold()
            if not name:
                continue
            if name not in AVAILABLE_COLUMNS:
                allowed = ", ".join(AVAILABLE_COLUMNS)
                raise ValueError(f"columna no válida: {value}. Disponibles: {allowed}")
            if name not in normalized:
                normalized.append(name)
    if not normalized:
        raise ValueError("debe configurarse al menos una columna")
    return normalized
