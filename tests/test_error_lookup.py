from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from lanctl.apps.ip.interfaces.cli.commands.error import run_error
from lanctl.core.error_catalog import find_error, load_error_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "errorList.txt"


def test_catalog_loader_and_lookup_are_case_insensitive():
    entries = load_error_catalog(CATALOG)
    assert len(entries) >= 700
    assert find_error(entries[0].error_id.lower(), CATALOG) == entries[0]


@pytest.mark.parametrize(
    "row",
    [
        "0e12345678 | 00 | source.py | 1 | LANCTL.Test.Point | raise\n",
        "0e12345678 | 60 | source.py | 1 | LANCTL.Test.Point | raise\n",
        "0e12345678 | 40 | source.py | 0 | LANCTL.Test.Point | raise\n",
        "0e12345678 | 40 | source.py | 1 | LANCTL.Test.Point | unknown\n",
    ],
)
def test_catalog_loader_rejects_invalid_levels_and_metadata(tmp_path, row):
    path = tmp_path / "errors.txt"
    path.write_text(row, encoding="utf-8")
    with pytest.raises(ValueError):
        load_error_catalog(path)


def test_catalog_loader_rejects_duplicate_identifiers(tmp_path):
    row = "0e12345678 | 40 | source.py | 1 | LANCTL.Test.Point | raise\n"
    path = tmp_path / "errors.txt"
    path.write_text(row + row, encoding="utf-8")
    with pytest.raises(ValueError, match="duplicado"):
        load_error_catalog(path)


def test_error_command_emits_machine_readable_result(capsys):
    entry = load_error_catalog(CATALOG)[0]
    result = run_error(argparse.Namespace(error_id=entry.error_id, json=True))
    payload = json.loads(capsys.readouterr().out)
    assert result == 0
    assert payload["errorId"] == entry.error_id


def test_error_command_rejects_unknown_identifier():
    with pytest.raises(ValueError, match="no catalogado"):
        run_error(argparse.Namespace(error_id="0eFFFFFFFF", json=False))
