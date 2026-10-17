import json
from unittest.mock import patch

import pytest

from lanctl.apps.monitor.log_stream import open_log_window
from lanctl.apps.monitor.log_tui import LogViewModel
from lanctl.bootstrap.lanmon import _main


def row(message, level=None):
    return {"source": "program", "file": "17-10-2026.log", "level": level, "message": message}


def test_pause_preserves_view_while_bounded_history_keeps_polling():
    view = LogViewModel(limit=3)
    view.ingest([row("a"), row("b")])
    view.key("p")
    view.ingest([row("c"), row("d"), row("e")])
    assert [r["message"] for r in view.rows(10)] == ["b", "a"]
    view.key("p")
    assert [r["message"] for r in view.rows(10)] == ["e", "d", "c"]
    assert view.key("q") is False


def test_level_text_filter_and_history():
    view = LogViewModel()
    view.ingest([row("error alpha", 42), row("notice beta", 10), row("error beta", 50)])
    view.key("f")
    assert len(view.rows(10)) == 2
    view.key("/")
    for key in "alpha\r":
        view.key(key)
    assert [r["message"] for r in view.rows(10)] == ["error alpha"]
    view.key("/")
    view.key("\r")
    view.key("up")
    assert view.paused
    assert [r["message"] for r in view.rows(10)] == ["error alpha"]


def test_cli_routes_log_tui_without_monitor_operations():
    with patch("lanctl.apps.monitor.log_tui.follow_log_tui", return_value=0) as follow:
        assert _main(["logs", "--tui", "--limit", "30"]) == 0
    follow.assert_called_once_with(limit=30, minimum=1)


def test_new_terminal_tui_flag_and_no_shell():
    with (
        patch("lanctl.apps.monitor.log_stream.subprocess.Popen") as popen,
        patch("lanctl.apps.monitor.log_stream.shutil.which", return_value="xterm"),
    ):
        assert open_log_window(tui=True) == 0
    assert popen.call_args.args[0][-1] == "--tui"
    assert not popen.call_args.kwargs.get("shell")


def test_log_follower_bounded_batches_without_losing_appended_lines(tmp_path):
    from lanctl.apps.monitor.log_stream import LogFollower

    path = tmp_path / "17-10-2026.log"
    path.write_text("initial\n", encoding="utf-8")
    follower = LogFollower(tmp_path)
    follower.poll()
    with path.open("a", encoding="utf-8") as stream:
        stream.write("".join(f"line-{i}\n" for i in range(2200)))
    batches = [follower.poll() for _ in range(3)]
    assert [len(batch) for batch in batches] == [1000, 1000, 200]
    assert [r["message"] for batch in batches for r in batch] == [f"line-{i}" for i in range(2200)]
    assert follower.poll() == []


def test_gui_activity_levels_reach_real_log_follower_and_tui_filter(tmp_path):
    from lanctl.apps.monitor.event_view import read_events
    from lanctl.apps.monitor.log_stream import LogFollower
    from lanctl.core.logger import write_log

    follower = LogFollower(tmp_path)
    assert follower.poll() == []
    messages = [
        "GUI_ACTIVITY "
        + json.dumps(
            {
                "schemaVersion": 1,
                "level": 20,
                "message": "Proyecto guardado; texto literal ERROR_EVENT sin error",
                "origin": "LANCTL.lanip.GUI",
            }
        ),
        'ERROR_EVENT {"level":43,"message":"fallo","origin":"LANCTL.Tests.Error"}',
        'GUI_ACTIVITY {"schemaVersion":1,"level":43,"message":"aviso","origin":"LANCTL.lanwire.GUI"}',
    ]
    for message in messages:
        write_log(message, directory=tmp_path)
    rows = follower.poll()
    assert [item["level"] for item in rows] == [20, 43, 43]
    assert all(item["message"].endswith(message) for item, message in zip(rows, messages))
    assert follower.poll() == []
    view = LogViewModel(minimum=40)
    view.ingest(rows)
    assert [item["level"] for item in view.rows(10)] == [43, 43]
    assert all("Proyecto guardado" not in item["message"] for item in view.rows(10))
    view.minimum = 20
    assert len(view.rows(10)) == 3
    assert len(read_events({"programLog": str(tmp_path)}, source="program", minimum=40)) == 2


@pytest.mark.parametrize(
    "payload",
    [
        "broken",
        "null",
        "[]",
        '{"schemaVersion":2,"level":20}',
        '{"schemaVersion":true,"level":20}',
        '{"schemaVersion":1,"level":true}',
        '{"schemaVersion":1,"level":"20"}',
        '{"schemaVersion":1,"level":60}',
    ],
)
def test_invalid_gui_activity_remains_visible_without_assigning_a_level(payload):
    from lanctl.apps.monitor.event_view import _rows

    text = "10:00:00 GUI_ACTIVITY " + payload
    assert _rows(text, "program", "17-10-2026.log", 1) == [row(text)]
