from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from lanctl.core.resources import bundled_path

ERROR_ID_PATTERN = re.compile(r"^0e[0-9A-F]{8}$", re.IGNORECASE)
CATALOG_KINDS = frozenset({"raise", "diagnostic", "exit", "return-error", "print-error"})


@dataclass(frozen=True, slots=True)
class ErrorCatalogEntry:
    error_id: str
    level: int
    source: str
    line: int
    origin: str
    kind: str

    def to_dict(self) -> dict[str, str | int]:
        return {
            "errorId": self.error_id,
            "level": self.level,
            "source": self.source,
            "line": self.line,
            "origin": self.origin,
            "kind": self.kind,
        }


def load_error_catalog(path: str | Path | None = None) -> tuple[ErrorCatalogEntry, ...]:
    catalog = Path(path) if path is not None else bundled_path("errorList.txt")
    entries: list[ErrorCatalogEntry] = []
    identifiers: set[str] = set()
    for number, raw_line in enumerate(catalog.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line or raw_line.startswith("#"):
            continue
        fields = raw_line.split(" | ")
        if len(fields) != 6:
            raise ValueError(f"catálogo inválido en la línea {number}: se esperaban 6 campos")
        error_id, level_text, source, line_text, origin, kind = fields
        normalized_id = error_id.lower()
        if not ERROR_ID_PATTERN.fullmatch(error_id):
            raise ValueError(f"identificador inválido en la línea {number}: {error_id}")
        if normalized_id in identifiers:
            raise ValueError(f"identificador duplicado en la línea {number}: {error_id}")
        identifiers.add(normalized_id)
        level, source_line = int(level_text), int(line_text)
        if not 1 <= level <= 59:
            raise ValueError(f"nivel fuera del rango 1-59 en la línea {number}: {level}")
        if source_line < 1 or kind not in CATALOG_KINDS:
            raise ValueError(f"metadatos inválidos en la línea {number}")
        entries.append(ErrorCatalogEntry(error_id, level, source, source_line, origin, kind))
    return tuple(entries)


def find_error(error_id: str, path: str | Path | None = None) -> ErrorCatalogEntry | None:
    normalized = error_id.strip().lower()
    if not ERROR_ID_PATTERN.fullmatch(normalized):
        raise ValueError("el identificador debe usar el formato 0eXXXXXXXX hexadecimal")
    return next(
        (entry for entry in load_error_catalog(path) if entry.error_id.lower() == normalized),
        None,
    )
