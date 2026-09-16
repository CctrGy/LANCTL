from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TuiLayout:
    compact: bool
    modal_margin: int
    modal_width: int
    modal_height: int
    body_rows: int


def adaptive_layout(width: int, height: int, *, settings: bool = False) -> TuiLayout:
    width = max(20, width)
    height = max(8, height)
    compact = width < 70 or height < 20
    margin = 2 if compact else 6
    width_limit = 130 if settings else 100
    height_limit = 36 if settings else 30
    modal_width = max(10, min(max(10, width - margin), width_limit))
    modal_height = max(6, min(max(6, height - margin), height_limit))
    return TuiLayout(
        compact=compact,
        modal_margin=margin,
        modal_width=modal_width,
        modal_height=modal_height,
        body_rows=max(1, modal_height - 7),
    )


PANEL_LAYOUTS = ("cli.bottom", "cli.top")
MIN_CLI_PERCENT = 15
MIN_LIST_PERCENT = 25

FIXED_COLUMN_WIDTHS = {"IP": 15, "MAC": 17}
DEFAULT_COLUMN_SPECS = {
    "IP": "15ch",
    "responseMs": "4%",
    "cnf": "2%",
    "ALIAS": "10%",
    "MAC": "17ch",
    "NAME": "12%",
    "GROUP": "12%",
    "description": "33%",
    "manufacturer": "17%",
    "users": "10%",
}
COLUMN_LIMITS = {
    "IP": (15, 15),
    "responseMs": (4, 8),
    "cnf": (3, 3),
    "ALIAS": (4, 28),
    "MAC": (17, 17),
    "NAME": (4, 32),
    "GROUP": (5, 32),
    "description": (6, 120),
    "manufacturer": (8, 36),
    "users": (7, 36),
}

_SPEC_PATTERN = re.compile(r"^(?P<value>\d+(?:\.\d+)?)\s*(?P<unit>%|ch)$", re.IGNORECASE)


def normalize_panel_layout(value: object) -> str:
    normalized = str(value or "cli.bottom").strip().casefold().replace("_", ".")
    aliases = {
        "bottom": "cli.bottom",
        "below": "cli.bottom",
        "abajo": "cli.bottom",
        "cli.abajo": "cli.bottom",
        "top": "cli.top",
        "above": "cli.top",
        "arriba": "cli.top",
        "cli.arriba": "cli.top",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in PANEL_LAYOUTS:
        raise ValueError(
            f"distribución TUI no válida: {value}. Opciones: {', '.join(PANEL_LAYOUTS)}"
        )
    return normalized


def normalize_cli_percent(value: object) -> int:
    try:
        percent = int(str(value).strip().removesuffix("%"))
    except ValueError as error:
        raise ValueError("el porcentaje del CLI debe ser un número entero") from error
    maximum = 100 - MIN_LIST_PERCENT
    if not MIN_CLI_PERCENT <= percent <= maximum:
        raise ValueError(
            f"el CLI debe ocupar entre {MIN_CLI_PERCENT}% y {maximum}% "
            f"para reservar al menos {MIN_LIST_PERCENT}% a ListElement"
        )
    return percent


def normalize_column_specs(value: object) -> dict[str, str]:
    source = value if isinstance(value, Mapping) else {}
    normalized = dict(DEFAULT_COLUMN_SPECS)
    canonical = {name.casefold(): name for name in DEFAULT_COLUMN_SPECS}
    canonical["protocols"] = "users"
    for raw_name, raw_spec in source.items():
        name = canonical.get(str(raw_name).strip().casefold())
        if not name:
            raise ValueError(f"columna TUI desconocida: {raw_name}")
        normalized[name] = normalize_column_spec(name, raw_spec)
    return normalized


def normalize_column_spec(name: str, value: object) -> str:
    match = _SPEC_PATTERN.fullmatch(str(value).strip())
    if not match:
        raise ValueError(f"{name} debe usar un valor como 12% o 15ch")
    number = float(match.group("value"))
    unit = match.group("unit").casefold()
    if number <= 0:
        raise ValueError(f"el tamaño de {name} debe ser mayor que cero")
    if name in FIXED_COLUMN_WIDTHS:
        expected = FIXED_COLUMN_WIDTHS[name]
        if unit != "ch" or number != expected:
            raise ValueError(f"{name} es fija y debe conservar {expected}ch")
        return f"{expected}ch"
    if unit != "%":
        raise ValueError(f"{name} utiliza porcentaje; indica un valor terminado en %")
    return f"{number:g}%"


def panel_rows(height: int, cli_percent: object) -> tuple[int, int]:
    """Devuelve filas de ListElement y CLI; la barra de teclas queda fuera."""

    available = max(8, height - 1)
    percent = normalize_cli_percent(cli_percent)
    cli_rows = round(available * percent / 100)
    cli_rows = max(4, min(cli_rows, available - 4))
    return available - cli_rows, cli_rows


def allocate_column_widths(
    fields: Sequence[str], available: int, gap: int, specs: Mapping[str, str] | None = None
) -> dict[str, int]:
    """Convierte pesos porcentuales en caracteres sin violar límites de columna."""

    configured = normalize_column_specs(specs)
    cell_budget = max(1, available - gap * max(0, len(fields) - 1))
    widths: dict[str, int] = {
        field: FIXED_COLUMN_WIDTHS[field] for field in fields if field in FIXED_COLUMN_WIDTHS
    }
    dynamic = [field for field in fields if field not in FIXED_COLUMN_WIDTHS]
    dynamic_budget = max(0, cell_budget - sum(widths.values()))
    weights = {field: float(configured[field].removesuffix("%")) for field in dynamic}
    total_weight = sum(weights.values()) or 1.0
    for field in dynamic:
        minimum, maximum = COLUMN_LIMITS[field]
        proposed = round(dynamic_budget * weights[field] / total_weight)
        widths[field] = max(minimum, min(maximum, proposed))

    _fit_widths(widths, dynamic, cell_budget, weights)
    return {field: widths[field] for field in fields}


def _fit_widths(
    widths: dict[str, int], dynamic: list[str], budget: int, weights: Mapping[str, float]
) -> None:
    used = sum(widths.values())
    while used > budget:
        candidates = [field for field in dynamic if widths[field] > COLUMN_LIMITS[field][0]]
        if not candidates:
            break
        field = max(candidates, key=lambda item: widths[item] - COLUMN_LIMITS[item][0])
        widths[field] -= 1
        used -= 1
    while used < budget:
        candidates = [field for field in dynamic if widths[field] < COLUMN_LIMITS[field][1]]
        if not candidates:
            break
        field = max(
            candidates,
            key=lambda item: weights[item] / max(1, widths[item]),
        )
        widths[field] += 1
        used += 1


def minimum_terminal_width(fields: Sequence[str], gap: int = 1) -> int:
    return sum(COLUMN_LIMITS[field][0] for field in fields) + gap * max(0, len(fields) - 1) + 2
