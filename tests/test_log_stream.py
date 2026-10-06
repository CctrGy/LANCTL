from unittest.mock import patch

from lanctl.apps.monitor.log_stream import LogFollower, open_log_window
from lanctl.bootstrap.lanmon import build_parser


def test_history_append_duplicates_partial_utf8_and_rotation(tmp_path):
    path = tmp_path / "01-10-2026.log"
    path.write_bytes(b"one\none\ntwo\n")
    follower = LogFollower(tmp_path, limit=2)
    assert [r["message"] for r in follower.poll()] == ["one", "two"]
    assert not follower.poll()
    with path.open("ab") as stream:
        stream.write(b"one\none\ncaf\xc3")
    assert [r["message"] for r in follower.poll()] == ["one", "one"]
    with path.open("ab") as stream:
        stream.write(b"\xa9\n")
    assert follower.poll()[0]["message"] == "café"
    (tmp_path / "02-10-2026.log").write_bytes(b"new day\n")
    assert follower.poll()[0]["message"] == "new day"
    path.write_bytes(b"x\n")
    assert follower.poll()[0]["message"] == "x"


def test_waits_for_directory_and_sanitizes_terminal_content(tmp_path):
    directory = tmp_path / "missing"
    follower = LogFollower(directory)
    assert not follower.poll()
    directory.mkdir()
    (directory / "01-10-2026.log").write_bytes(b"\x1b[31merror\x07\n")
    assert follower.poll()[0]["message"] == "error"


def test_window_passes_arguments_without_shell():
    with (
        patch("lanctl.apps.monitor.log_stream.subprocess.Popen") as launch,
        patch("lanctl.apps.monitor.log_stream.shutil.which", return_value="xterm"),
    ):
        assert open_log_window(limit=42, minimum=20) == 0
    command = launch.call_args.args[0]
    assert command[-8:] == [
        "logs",
        "--follow",
        "--source",
        "program",
        "--limit",
        "42",
        "--level",
        "20",
    ]
    assert not launch.call_args.kwargs.get("shell")


def test_window_parser():
    args = build_parser().parse_args(["logs", "--window", "--level", "30"])
    assert args.window and args.level == 30
