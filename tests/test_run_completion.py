"""El completado consulta parsers sin lanzar operaciones de red ni interfaces."""

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "complete_run", Path(__file__).resolve().parents[1] / "tools" / "complete_run.py"
)
completion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(completion)


def test_root_and_nested_launchers():
    assert {"lanip", "lanmon", "--gui", "-version"} <= set(completion.candidates([""]))
    assert "scan" in completion.candidates(["lanip", "sc"])
    assert "--ports" in completion.candidates(["lanip", "scan", "--p"])
    assert "--ports" in completion.candidates(["ip", "scan", "--p"])
    assert "--ports" in completion.candidates(["--foreground", "lanip", "scan", "--p"])


def test_option_values_and_shared_commands():
    assert completion.candidates(["lanip", "scan", "--ports", ""]) == []
    assert "--json" in completion.candidates(["lanip", "scan", "--ports", "80", "--j"])
    assert "list" in completion.candidates(["plugin", "li"])
    assert "--help" in completion.candidates(["backend", "--h"])
