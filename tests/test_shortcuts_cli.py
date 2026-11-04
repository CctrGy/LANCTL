"""P118: public parser and CLI adapter use temporary distributions only."""

import sys
from unittest.mock import patch

import pytest

from lanctl.apps.suite.shortcuts_cli import run_shortcut
from lanctl.bootstrap.lanctl import build_parser

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="Linux desktop shortcut fixtures"
)


def arguments(tmp_path, *extra):
    executable = tmp_path / "lanctl"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    return build_parser().parse_args(
        [
            "shortcut",
            "--mode",
            "tui",
            "--name",
            "Prueba",
            "--distribution",
            str(tmp_path),
            *extra,
        ]
    )


def test_preview_does_not_write(tmp_path, capsys):
    assert run_shortcut(arguments(tmp_path)) == 0
    assert not (tmp_path / "Prueba.desktop").exists()
    output = capsys.readouterr().out
    assert '"arguments": ["--tui"]' in output
    assert '"terminal": true' in output


def test_create_and_collision(tmp_path):
    args = arguments(tmp_path, "--create")
    assert run_shortcut(args) == 0
    target = tmp_path / "Prueba.desktop"
    original = target.read_bytes()
    with patch("lanctl.core.errors.errors.from_exception") as report:
        assert run_shortcut(args) == 2
    assert target.read_bytes() == original
    assert isinstance(report.call_args.args[0], FileExistsError)
    assert report.call_args.kwargs["origin"] == "LANCTL.Suite.Shortcut.Create"


def test_source_requires_explicit_distribution(tmp_path):
    args = arguments(tmp_path)
    args.distribution = None
    with patch("lanctl.core.errors.errors.from_exception") as report:
        assert run_shortcut(args) == 2
    assert str(report.call_args.args[0]) == "SHORTCUT.DISTRIBUTION_REQUIRED"


def test_unsupported_platform(tmp_path):
    with (
        patch("lanctl.apps.suite.shortcuts_cli.sys.platform", "darwin"),
        patch("lanctl.core.errors.errors.from_exception") as report,
    ):
        assert run_shortcut(arguments(tmp_path)) == 2
    assert str(report.call_args.args[0]) == "SHORTCUT.UNSUPPORTED_PLATFORM"


def test_gui_missing(tmp_path):
    args = arguments(tmp_path)
    args.mode = "gui"
    with (
        patch("lanctl.apps.suite.shortcuts_cli.importlib.util.find_spec", return_value=None),
        patch("lanctl.core.errors.errors.from_exception") as report,
    ):
        assert run_shortcut(args) == 2
    assert str(report.call_args.args[0]) == "SHORTCUT.GUI_UNAVAILABLE"


def test_unknown_arguments_rejected(tmp_path):
    with pytest.raises(SystemExit):
        arguments(tmp_path, "--password", "secret")


def test_root_dispatch(tmp_path):
    from lanctl.bootstrap.lanctl import main

    args = arguments(tmp_path)
    with (
        patch("lanctl.bootstrap.lanctl.initialize_language"),
        patch("lanctl.bootstrap.lanctl.configure_utf8_stdio"),
        patch("lanctl.apps.suite.shortcuts_cli.run_shortcut", return_value=0) as run,
    ):
        assert (
            main.__wrapped__(
                [
                    "shortcut",
                    "--mode",
                    "tui",
                    "--name",
                    args.name,
                    "--distribution",
                    str(tmp_path),
                ]
            )
            == 0
        )
    assert run.call_args.args[0].distribution == tmp_path


def test_frozen_uses_executable_directory(tmp_path):
    args = arguments(tmp_path)
    args.distribution = None
    with (
        patch("lanctl.apps.suite.shortcuts_cli.sys.frozen", True, create=True),
        patch("lanctl.core.paths.application_directory", return_value=tmp_path),
    ):
        assert run_shortcut(args) == 0
    assert not (tmp_path / "Prueba.desktop").exists()
