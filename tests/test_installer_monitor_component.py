"""P70: Standard installs the optional service without removing interactive LANMON."""

import re
from pathlib import Path


def test_standard_monitor_selection_and_independent_interactive_binary():
    source = (Path(__file__).resolve().parents[1] / "packaging/inno/LANCTL.iss").read_text(
        encoding="utf-8"
    )
    component = next(
        line
        for line in source.splitlines()
        if line.startswith("Name: monitor;") and "Types:" in line
    )
    assert "Servicio de monitorización en segundo plano (LANMON)" in component
    assert set(re.search(r"Types: ([^;]+)", component).group(1).split()) == {
        "standard",
        "monitor",
        "custom",
    }
    assert "fixed" not in component
    binary = next(
        line
        for line in source.splitlines()
        if line.startswith('Source: "{#BuildRoot}\\lanmon.exe"')
    )
    assert "Components: core" in binary
    install = next(
        line
        for line in source.splitlines()
        if 'Parameters: "monitor service install --yes"' in line
    )
    assert "Components: monitor" in install
    assert "desmarcar el servicio no elimina LANMON" in source
