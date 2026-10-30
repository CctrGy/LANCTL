"""Terminal-native read-only views: scrolling, restoration and real PTY help."""

import os
import re
import sys
from contextlib import nullcontext
from unittest.mock import Mock, patch

import pytest

from lanctl.core.terminal_ui import ManagementScreen


def test_help_view_scrolls_to_end_and_home_without_suspending():
    screen = ManagementScreen()
    screen.active = True
    screen.draw = Mock()
    keys = Mock(side_effect=["END", "HOME", "PGDN", "UP", "CLOSE"])
    with (
        patch("lanctl.core.terminal_ui._viewer_keyboard", return_value=nullcontext(keys)),
        patch("lanctl.core.terminal_ui.shutil.get_terminal_size", return_value=(80, 20)),
        patch.object(screen, "suspended") as suspended,
    ):
        screen.show_text("\n".join(f"Line {i}" for i in range(100)), title="Help")
    panels = [call.args[0] for call in screen.draw.call_args_list]
    assert panels[0].renderable.plain.startswith("Line 0\n")
    assert panels[1].renderable.plain.endswith("Line 99")
    assert panels[2].renderable.plain.startswith("Line 0\n")
    assert panels[3].renderable.plain.startswith("Line 11\n")
    assert panels[4].renderable.plain.startswith("Line 10\n")
    suspended.assert_not_called()


@pytest.mark.skipif(os.name == "nt", reason="POSIX pseudo-terminal regression")
@pytest.mark.parametrize("command", [b"help\n", b"help settings\n"])
def test_root_tui_help_uses_same_alternate_screen_and_restores_terminal(tmp_path, command):
    import fcntl
    import pty
    import select
    import struct
    import subprocess
    import termios
    import time
    from pathlib import Path

    marker = tmp_path / "data/config/migration-v2.complete"
    marker.parent.mkdir(parents=True)
    marker.write_text("LANCTL-DATA-V2\n", encoding="utf-8")
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 120, 0, 0))
    original = termios.tcgetattr(slave)
    process = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve().parents[1] / "lanctl.py"), "--tui"],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        env={**os.environ, "LANCTL_DATA_DIR": str(tmp_path / "data"), "TERM": "xterm-256color"},
    )

    def read_until(needle):
        output = b""
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if select.select([master], [], [], 0.1)[0]:
                output += os.read(master, 65536)
                plain = re.sub(rb"\x1b\[[0-?]*[ -/]*[@-~]", b"", output)
                if needle in plain:
                    return output
        raise AssertionError(f"Missing {needle!r}: {output[-2000:]!r}")

    try:
        read_until(b"LANCTL> ")
        os.write(master, command)
        help_output = read_until(b"Esc/Enter back")
        assert b"\x1b[?1049l" not in help_output
        assert b"help" in help_output
        os.write(master, b"\x1b[F")
        end_output = read_until(b"Esc/Enter back")
        assert b"\x1b[?1049l" not in end_output
        os.write(master, b"\x1b")
        returned = read_until(b"LANCTL> ")
        assert b"\x1b[?1049l" not in returned
        assert termios.tcgetattr(slave) == original
        os.write(master, b"exit\n")
        assert process.wait(timeout=10) == 0
        assert termios.tcgetattr(slave) == original
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
        os.close(master)
        os.close(slave)


@pytest.mark.skipif(os.name == "nt", reason="POSIX terminal mode regression")
def test_help_render_failure_restores_original_keyboard_mode():
    import pty
    import termios

    master, slave = pty.openpty()
    original = termios.tcgetattr(slave)
    screen = ManagementScreen()
    screen.active = True
    screen.draw = Mock(side_effect=OSError("display failed"))
    try:
        with (
            os.fdopen(os.dup(slave), "r") as stream,
            patch("sys.stdin", stream),
            pytest.raises(OSError, match="display failed"),
        ):
            screen.show_text("Help")
        assert termios.tcgetattr(slave) == original
    finally:
        os.close(master)
        os.close(slave)


def test_help_reflows_and_clamps_scroll_after_terminal_resize():
    screen = ManagementScreen()
    screen.active = True
    screen.draw = Mock()
    keys = Mock(side_effect=["END", "END", "CLOSE"])
    with (
        patch("lanctl.core.terminal_ui._viewer_keyboard", return_value=nullcontext(keys)),
        patch(
            "lanctl.core.terminal_ui.shutil.get_terminal_size",
            side_effect=[(80, 20), (40, 12), (160, 50)],
        ),
    ):
        screen.show_text("\n".join(f"Line {i}" for i in range(100)))
    panels = [call.args[0] for call in screen.draw.call_args_list]
    assert len(panels[0].renderable.plain.splitlines()) == 11
    assert len(panels[1].renderable.plain.splitlines()) == 3
    assert len(panels[2].renderable.plain.splitlines()) == 41
    assert panels[2].renderable.plain.endswith("Line 99")
