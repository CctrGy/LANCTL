"""Exercise the actual TTY/TextIO boundary, including batched arrow keys."""

import os
import select
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

import pytest

from lanctl.apps.ip.domain.models import Device
from lanctl.apps.ip.interfaces.tui.keyboard import (
    posix_key_available,
    read_posix_key,
)
from lanctl.apps.ip.interfaces.tui.main import LanctlTui

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX pseudoterminal")


@contextmanager
def terminal_input(payload):
    import pty
    import tty

    master, slave = pty.openpty()
    try:
        tty.setcbreak(slave)
        with os.fdopen(os.dup(slave), "r", encoding="utf-8", newline="") as stream:
            os.write(master, payload)
            yield stream
    finally:
        os.close(master)
        os.close(slave)


def test_repeated_navigation_moves_inventory_without_requesting_exit():
    tui = LanctlTui.__new__(LanctlTui)
    tui.devices = [Device(ip=f"192.0.2.{i}") for i in range(1, 41)]
    tui.index = 0
    tui.modal = None
    tui.detail_lines = []
    tui.output_focus = False
    tui.command_suggestions = []
    tui.key_bindings = {}
    tui._begin_close = Mock()

    with terminal_input(b"\x1b[B\x1b[B\x1b[6~\x1b[A\x1b[5~") as stream:
        for expected in (1, 2, 12, 11, 1):
            assert posix_key_available(stream)
            tui.handle_key(read_posix_key(stream))
            assert tui.index == expected
        assert not posix_key_available(stream)
    tui._begin_close.assert_not_called()


def test_unicode_and_next_key_remain_available_without_text_read_ahead():
    with terminal_input("ñ界\x1b[B".encode()) as stream:
        for expected in ("ñ", "界", "DOWN"):
            assert posix_key_available(stream)
            assert read_posix_key(stream) == expected
        assert not posix_key_available(stream)


@pytest.mark.parametrize("sequence", [b"\x1b[1;5A", b"\x1b[<64;20;10M", b"\x1b[99~"])
def test_unsupported_terminal_reports_do_not_close_or_leak_into_prompt(sequence):
    with terminal_input(sequence + b"\x1b[B") as stream:
        assert read_posix_key(stream) == "UNKNOWN"
        assert posix_key_available(stream)
        assert read_posix_key(stream) == "DOWN"
        assert not posix_key_available(stream)


def test_incomplete_escape_sequence_is_not_an_escape_key():
    with terminal_input(b"\x1b[") as stream:
        assert read_posix_key(stream, escape_timeout=0.01) == "UNKNOWN"


def test_standalone_escape_still_closes_the_inventory():
    with terminal_input(b"\x1b") as stream:
        assert read_posix_key(stream, escape_timeout=0.01) == "ESC"


def test_full_tui_scrolls_and_stays_open_until_explicit_escape(tmp_path):
    import pty
    import termios

    code = """
import ipaddress
from unittest.mock import patch
from lanctl.apps.ip.domain.models import Device
from lanctl.apps.ip.interfaces.tui.main import LanctlTui
rows = [Device(ip=f"192.0.2.{i}", mac=f"00:11:22:33:44:{i:02X}") for i in range(1, 41)]
with (
    patch("lanctl.apps.ip.interfaces.tui.main.local_ipv4",
          return_value=ipaddress.IPv4Address("192.0.2.254")),
    patch("lanctl.apps.ip.interfaces.tui.main.DeviceDatabase.load", return_value=rows),
    patch.object(LanctlTui, "refresh", return_value=None),
):
    raise SystemExit(LanctlTui().run())
"""
    master, slave = pty.openpty()
    environment = {key: value for key, value in os.environ.items() if not key.startswith("LANCTL_")}
    environment.update(
        LANCTL_DATA_DIR=str(tmp_path),
        PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"),
        TERM="xterm-256color",
    )
    process = None
    captured = bytearray()

    def wait_for(predicate):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if predicate():
                return
            if select.select([master], [], [], 0.02)[0]:
                try:
                    captured.extend(os.read(master, 65536))
                except OSError:
                    break
            if process.poll() is not None:
                break
        if predicate():
            return
        pytest.fail(f"TUI did not reach expected state (exit={process.poll()})")

    try:
        process = subprocess.Popen(
            [sys.executable, "-B", "-c", code],
            stdin=slave,
            stdout=slave,
            stderr=slave,
            env=environment,
        )
        # The first frame precedes entering cbreak; wait for both conditions
        # so the injected keys are not queued as canonical line input.
        wait_for(lambda: b"1/40" in captured and not termios.tcgetattr(slave)[3] & termios.ICANON)
        os.write(master, b"\x1b[B" * 15 + b"\x1b[6~")
        wait_for(lambda: b"26/40" in captured)
        os.write(master, b"\x1b[5~\x1b[A")
        wait_for(lambda: b"15/40" in captured)
        assert process.poll() is None
        os.write(master, b"\x1b")
        wait_for(lambda: process.poll() is not None)
        assert process.wait(timeout=2) == 0
        assert termios.tcgetattr(slave)[3] & termios.ICANON
        assert b"\x1b[?1049l" in captured
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        os.close(master)
        os.close(slave)
