"""Vista gráfica ASCII/Rich de la topología física de LANWIRE."""

from __future__ import annotations

from typing import Any

from rich.text import Text

from lanctl.apps.wire.topology import connection_medium


def topology_lines(records: list[dict[str, Any]]) -> list[str]:
    """Representación lineal estable, reutilizable también desde el CLI."""
    devices = {
        record["id"] for record in records if (record.get("data") or {}).get("type") != "wire"
    }
    linked: set[str] = set()
    lines: list[str] = []
    for record in sorted(records, key=lambda item: item["id"]):
        data = record.get("data") or {}
        if data.get("type") != "wire":
            continue
        endpoints = list(data.get("endpoints", []))
        labels = [f"{item.get('device', '?')}.{item.get('port', '?')}" for item in endpoints]
        linked.update(str(item.get("device")) for item in endpoints)
        left, right = [*labels, "(libre)", "(libre)"][:2]
        medium = connection_medium(data.get("kind")).removeprefix("connection.").upper()
        lines.append(f"{left:<18} ──[{record['id']} · {medium}]── {right}")
    isolated = sorted(devices - linked)
    if isolated:
        lines.extend(f"{identifier:<18} · sin cable" for identifier in isolated)
    return lines or ["(No hay conexiones físicas registradas.)"]


def topology_text(records: list[dict[str, Any]], selected_id: str | None = None) -> Text:
    text = Text("  TOPOLOGÍA FÍSICA\n", style="bold bright_cyan")
    text.append(f"  {len(records)} elementos · conexiones y extremos libres\n\n", style="dim")
    lines = topology_lines(records)
    for index, line in enumerate(lines):
        style = "bold black on bright_cyan" if selected_id and selected_id in line else "white"
        text.append("  " + line, style=style)
        if index < len(lines) - 1:
            text.append("\n")
    text.append("\n\n  graph actualiza esta vista · Esc cerrar", style="dim")
    return text
