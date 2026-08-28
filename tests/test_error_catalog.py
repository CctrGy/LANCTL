from __future__ import annotations

from collections import Counter
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "errorList.txt"


def _rows():
    return [
        line.split(" | ")
        for line in CATALOG.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    ]


def test_catalog_ids_levels_sources_and_kinds_are_valid():
    rows = _rows()
    identifiers = [row[0] for row in rows]
    assert len(rows) >= 650
    assert len(identifiers) == len(set(identifiers))
    assert all(identifier.startswith("0e") and len(identifier) == 10 for identifier in identifiers)
    assert all(1 <= int(row[1]) <= 59 for row in rows)
    assert all((CATALOG.parent / row[2]).is_file() for row in rows)
    assert {row[5] for row in rows} <= {
        "raise",
        "diagnostic",
        "exit",
        "return-error",
        "print-error",
    }


def test_catalog_severity_is_not_concentrated_in_one_bucket():
    rows = _rows()
    distribution = Counter(int(row[1]) for row in rows)
    assert max(distribution.values()) / len(rows) < 0.30


def test_catalog_contains_low_level_and_non_raise_control_points():
    rows = _rows()
    assert any(int(row[1]) < 20 for row in rows)
    kinds = {row[5] for row in rows}
    assert {"diagnostic", "return-error", "print-error", "exit"} <= kinds
