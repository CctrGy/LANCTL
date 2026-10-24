"""Secret findings identify a file and category, never the matched secret."""

import importlib.util
from pathlib import Path


def test_repository_secret_guard_does_not_echo_matches(tmp_path, monkeypatch, capsys):
    path = Path(__file__).resolve().parents[1] / "tools/check_repository_hygiene.py"
    spec = importlib.util.spec_from_file_location("hygiene_output_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    candidate = tmp_path / "candidate.txt"
    secret = "ghp_" + "A" * 40
    candidate.write_text(secret, encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "repository_files", lambda: [candidate])
    assert module.main() == 1
    captured = capsys.readouterr()
    assert "candidate.txt: posible token GitHub" in captured.err
    assert secret not in captured.out + captured.err
