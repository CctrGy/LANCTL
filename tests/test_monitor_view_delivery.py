"""Monitor requests reach an existing session without dropping their source."""

import json
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_project_sync import projects

from lanctl.core.coordination import Coordinator
from lanctl.core.gui_instance import GuiInstance, focus_gui
from lanctl.core.session import Session


def test_frontend_serializes_requests_and_preserves_draft_without_browser():
    executable = os.environ.get("LANCTL_NODE_EXECUTABLE") or shutil.which("node")
    if not executable:
        pytest.skip("Optional Node.js frontend behavior check")
    script = Path(__file__).parent / "js/monitor_view_delivery.cjs"
    completed = subprocess.run(
        [executable, str(script)], capture_output=True, text=True, timeout=10
    )
    assert completed.returncode == 0, completed.stderr


def test_existing_monitor_receives_requested_view_and_source(tmp_path):
    coordinator = Coordinator(tmp_path / "coordinator.db")
    source = coordinator.register("lanip", "gui", "project-A")
    target = Session("lanmon", "gui", {}, coordinator=coordinator)
    received = []
    target.handler = received.append
    coordinator.heartbeat(target.id, controls=True)
    try:
        focus_gui(coordinator, "lanmon", timeout=3, monitor_view="report", source_session=source)
        command = next(item for item in received if item["action"] == "monitor-view")
        assert json.loads(command["value"]) == {"view": "report", "sourceSession": source}
    finally:
        target.close()
        coordinator.close(source)


def test_monitor_view_commands_reject_foreign_source_and_wrong_target(tmp_path):
    coordinator = Coordinator(tmp_path / "coordinator.db")
    target = coordinator.register("lanmon", "gui")
    coordinator.heartbeat(target, controls=True)
    wrong_target = coordinator.register("lanip", "gui")
    coordinator.heartbeat(wrong_target, controls=True)
    foreign = coordinator.register("lanwire", "gui")
    with coordinator.connection() as db:
        db.execute("UPDATE sessions SET owner='other-principal' WHERE id=?", (foreign,))
    for destination, view, source in (
        (wrong_target, "report", ""),
        (target, "arbitrary", ""),
        (target, "report", foreign),
        (target, "report", "unknown-session"),
    ):
        with pytest.raises(ValueError):
            coordinator.enqueue_monitor_view(destination, view, source)
    assert coordinator.claim(target) == []


def test_duplicate_monitor_launch_forwards_environment_request(tmp_path, monkeypatch):
    coordinator = Coordinator(tmp_path / "coordinator.db")
    focus = Mock()
    monkeypatch.setattr("lanctl.core.gui_instance.focus_gui", focus)
    monkeypatch.setenv("LANCTL_GUI_VIEW", "report")
    monkeypatch.setenv("LANCTL_GUI_SOURCE_SESSION", "source-session")
    with GuiInstance("lanmon", coordinator=coordinator) as first:
        assert first
        with GuiInstance("lanmon", coordinator=coordinator) as duplicate:
            assert not duplicate
    focus.assert_called_once_with(
        coordinator, "lanmon", timeout=30, monitor_view="report", source_session="source-session"
    )


@pytest.mark.parametrize("fails", [False, True])
def test_open_monitor_reuses_ready_instance_and_surfaces_delivery_failure(
    workspace, monkeypatch, fails
):
    from lanctl.apps.suite.gui import SuiteApi
    from lanctl.core.session import bind_session

    coordinator = Coordinator()
    source = Session("lanctl", "gui", workspace, coordinator=coordinator)
    target = Session("lanmon", "gui", workspace, coordinator=coordinator)
    requests = []

    def receive(command):
        if command["action"] == "monitor-view":
            requests.append(json.loads(command["value"]))
            if fails:
                raise RuntimeError("synthetic-view-delivery-failure")

    target.handler = receive
    coordinator.heartbeat(target.id, controls=True)
    spawn = Mock()
    monkeypatch.setattr("lanctl.apps.suite.gui_support.subprocess.Popen", spawn)
    try:
        with bind_session(source):
            result = SuiteApi().open_monitor("report")
        assert result["ok"] is not fails, result
        assert requests == [{"view": "report", "sourceSession": source.id}]
        spawn.assert_not_called()
        if fails:
            assert result.get("errorId")
    finally:
        target.close()
        source.close()


@pytest.mark.parametrize("recent_noise", [False, True])
def test_report_reads_selected_source_before_limit_and_across_projects(
    workspace, tmp_path, recent_noise
):
    from lanctl.core.activity import ActivityStore
    from lanctl.core.projects.workspace import activate_project_workspace

    first, second = projects(workspace, tmp_path)
    coordinator = Coordinator()
    source = coordinator.register("lanip", "gui", first)
    store = ActivityStore()
    store.append(
        json.dumps(
            {
                "message": "source failure",
                "error": {"origin": "LANIP.Scan", "code": "TEST", "errorId": "0eTest"},
            }
        ),
        launcher="lanip",
        session=source,
        project=first,
        level=43,
    )
    if recent_noise:
        with store._connection() as db:
            db.executemany(
                "INSERT INTO activity(owner,created,message,launcher,session,project,level) VALUES(?,?,?,?,?,?,?)",
                [
                    (store.owner, index + 1, "noise", "lanmon", "other-session", second, 20)
                    for index in range(501)
                ],
            )
    activate_project_workspace(second)
    monitor = api("lanmon")
    try:
        activity = monitor.monitor_activity(source)
        assert activity["ok"] and len(activity["records"]) == 1
        assert activity["project"] == first
        if recent_noise:
            assert "other-session" in activity["sessions"]
        result = monitor.prepare_report(
            {"session": source, "description": "Source error", "anonymize": False}
        )
        assert result["ok"], result
        report = result["report"]
        assert report["application"] == "lanip"
        assert report["context"]["project"] == first
        assert report["errors"][0]["origin"] == "LANIP.Scan"
    finally:
        coordinator.close(source)
