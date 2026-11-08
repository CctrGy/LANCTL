"""Native close receipt must drain its RPC and preserve project guards/errors."""

from contextlib import nullcontext
from threading import RLock
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from lanctl.apps.suite import native_close


class State:
    def __init__(self):
        self.listeners = []

    def __iadd__(self, handler):
        self.listeners.append(handler)
        return self

    def __isub__(self, handler):
        self.listeners.remove(handler)
        return self


class Closed:
    def __init__(self):
        self.listeners = []
        self.done = False

    def __iadd__(self, handler):
        self.listeners.append(handler)
        return self

    def is_set(self):
        return self.done

    def wait(self, timeout):
        return self.done

    def fire(self):
        self.done = True
        for handler in self.listeners:
            handler()


@pytest.fixture
def scene(monkeypatch):
    window = SimpleNamespace(state=State(), events=SimpleNamespace(closed=Closed()))
    thread = Mock()
    thread.is_alive.return_value = False
    monkeypatch.setattr(native_close, "current_thread", lambda: thread)
    monkeypatch.setattr("lanctl.core.config.load_config", lambda: {"activeProject": None})
    monkeypatch.setattr(native_close, "project_operation", nullcontext)
    guard = Mock()
    monkeypatch.setattr(native_close, "require_project", guard)
    event = SimpleNamespace(
        message="original", error_id="failure", to_dict=lambda: {"original": True}
    )
    report = Mock(return_value=event)
    monkeypatch.setattr("lanctl.core.errors.errors.from_exception", report)
    calls = []

    def close(decision):
        thread.join.assert_called_once_with(5)
        guard.assert_called_once()
        calls.append(decision)
        window.events.closed.fire()
        return {"ok": True, "closed": True}

    manager = native_close.NativeClose(window, SimpleNamespace(_lock=RLock()), close)
    return SimpleNamespace(
        manager=manager, window=window, thread=thread, guard=guard, calls=calls, report=report
    )


def test_close_only_after_rpc_receipt_and_once(scene):
    token = scene.manager.prepare("discard")["token"]
    assert not scene.calls
    assert not scene.window.events.closed.is_set()
    scene.manager.receive("change", "lanctl_close_receipt", token)
    assert scene.calls == ["discard"]
    assert scene.window.events.closed.is_set()
    assert not scene.window.state.listeners
    scene.manager.receive("change", "lanctl_close_receipt", token)
    assert scene.calls == ["discard"]


@pytest.mark.parametrize(
    "event,key,value",
    [
        ("delete", "lanctl_close_receipt", "x"),
        ("change", "other", "x"),
        ("change", "lanctl_close_receipt", None),
        ("change", "lanctl_close_receipt", "wrong"),
        ("change", "lanctl_close_receipt", "☃" * 32),
    ],
)
def test_invalid_receipts_do_not_consume_ticket(scene, event, key, value):
    scene.manager.prepare()
    scene.manager.receive(event, key, value)
    assert scene.manager.ticket is not None
    assert not scene.calls
    scene.thread.join.assert_not_called()


@pytest.mark.parametrize("decision", ["cancel", [], None])
def test_invalid_decision(scene, decision):
    with pytest.raises(ValueError):
        scene.manager.prepare(decision)
    assert scene.manager.ticket is None


def test_duplicate_preparation_is_busy(scene):
    scene.manager.prepare()
    with pytest.raises(RuntimeError):
        scene.manager.prepare()
    assert not scene.calls


def test_expired_ticket_replaced(scene, monkeypatch):
    monkeypatch.setattr(native_close.time, "monotonic", lambda: 100)
    first = scene.manager.prepare()["token"]
    monkeypatch.setattr(native_close.time, "monotonic", lambda: 116)
    second = scene.manager.prepare()["token"]
    scene.manager.receive("change", "lanctl_close_receipt", first)
    assert not scene.calls
    scene.manager.receive("change", "lanctl_close_receipt", second)
    assert scene.calls == ["save"]


def test_rpc_not_finished_preserves_window_and_original_diagnostic(scene):
    scene.thread.is_alive.return_value = True
    token = scene.manager.prepare()["token"]
    scene.manager.receive("change", "lanctl_close_receipt", token)
    assert not scene.calls
    assert not scene.window.events.closed.is_set()
    assert scene.manager.ticket is None
    result = scene.window.state.lanctl_close_error
    assert result["token"] == token
    assert result["errorId"] == "failure"
    assert result["errorDetails"] == {"original": True}
    assert isinstance(scene.report.call_args.args[0], TimeoutError)
    assert scene.report.call_args.kwargs["origin"] == "LANCTL.GUI.NativeClose.Commit"


def test_changed_project_does_not_close(scene):
    scene.guard.side_effect = ValueError("stale project")
    token = scene.manager.prepare()["token"]
    scene.manager.receive("change", "lanctl_close_receipt", token)
    assert not scene.calls
    assert not scene.window.events.closed.is_set()
    assert str(scene.report.call_args.args[0]) == "stale project"


def test_close_service_error_is_preserved(scene):
    original = {"ok": False, "errorId": "save-failed", "errorDetails": {"source": "disk"}}
    scene.manager.close = lambda decision: original
    token = scene.manager.prepare()["token"]
    scene.manager.receive("change", "lanctl_close_receipt", token)
    assert not scene.window.events.closed.is_set()
    assert scene.window.state.lanctl_close_error == {"token": token, **original}
    scene.report.assert_not_called()


def test_destroy_not_confirmed_is_not_success(scene):
    scene.manager.close = lambda decision: {"ok": True, "closed": True}
    token = scene.manager.prepare()["token"]
    scene.manager.receive("change", "lanctl_close_receipt", token)
    assert isinstance(scene.report.call_args.args[0], TimeoutError)
    assert not scene.window.events.closed.is_set()


def test_frontend_receipt_retry_and_legacy_arguments():
    import subprocess
    from pathlib import Path

    playwright = pytest.importorskip("playwright")
    node = Path(playwright.__file__).parent / "driver/node"
    if not node.is_file():
        pytest.skip("Bundled Node runtime unavailable")
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            str(node),
            str(root / "tests/native_close_frontend.cjs"),
            str(root / "gui/native-close.js"),
        ],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_expired_receipt_never_closes(scene, monkeypatch):
    monkeypatch.setattr(native_close.time, "monotonic", lambda: 100)
    token = scene.manager.prepare()["token"]
    monkeypatch.setattr(native_close.time, "monotonic", lambda: 116)
    scene.manager.receive("change", "lanctl_close_receipt", token)
    assert not scene.calls
    assert scene.manager.ticket is None
    scene.thread.join.assert_not_called()
    assert isinstance(scene.report.call_args.args[0], TimeoutError)
    assert scene.window.state.lanctl_close_error["token"] == token


def test_only_declared_decisions_are_allowed(scene):
    scene.manager.decisions = frozenset({"save"})
    with pytest.raises(ValueError):
        scene.manager.prepare("discard")
    assert scene.manager.ticket is None


def test_native_close_is_never_a_remote_rpc():
    from lanctl.apps.access.remote import RemoteGuiApi

    backend = Mock()
    remote = RemoteGuiApi(Mock(), backend)
    with pytest.raises(PermissionError):
        remote.call(None, "prepare_native_close", ["save"])
    backend.prepare_native_close.assert_not_called()


def test_busy_project_operation_does_not_block_or_close(scene):
    lock = Mock()
    lock.acquire.return_value = False
    scene.manager.api._lock = lock
    token = scene.manager.prepare()["token"]
    scene.manager.receive("change", "lanctl_close_receipt", token)
    lock.acquire.assert_called_once_with(blocking=False)
    lock.release.assert_not_called()
    assert not scene.calls
    assert isinstance(scene.report.call_args.args[0], RuntimeError)
    assert not scene.window.events.closed.is_set()


@pytest.mark.parametrize(
    "outcome", ["closed", "rejected", "destroy-error", "unconfirmed", "preflight-error"]
)
def test_provisional_owner_tracks_native_confirmation(scene, tmp_path, monkeypatch, outcome):
    import json

    from lanctl.core.coordination import Coordinator
    from lanctl.core.database import DeviceDatabase
    from lanctl.core.projects.provisional import (
        claim_provisional_close,
        join_provisional_workspace,
        prepare_provisional_close,
        prepare_provisional_workspace,
        provisional_operation,
    )

    coordinator = Coordinator(tmp_path / "coordinator.db")
    owner = coordinator.register("lanip", "gui")
    draft = prepare_provisional_workspace(root=tmp_path / "drafts")
    join_provisional_workspace(draft, owner, coordinator=coordinator)
    with provisional_operation(draft, owner, coordinator=coordinator, base={}) as settings:
        DeviceDatabase(settings["database"]).add_manual_device(idf="PC-001")
    claim = claim_provisional_close(draft, owner, coordinator=coordinator)
    prepare_provisional_close(
        draft, owner, claim["token"], coordinator=coordinator, decision="discard"
    )
    scene.manager.provisional = native_close.ProvisionalClose(
        draft, owner, claim["token"], coordinator, "discard"
    )
    original_close = scene.manager.close

    def close(decision):
        metadata = json.loads((draft.root / "workspace.json").read_text())
        assert owner in metadata["owners"]
        assert metadata["closeLease"]["token"] == claim["token"]
        if outcome == "rejected":
            return {"ok": False, "closed": False, "errorId": "original-close-error"}
        if outcome == "destroy-error":
            raise OSError("native destroy failed")
        if outcome == "unconfirmed":
            return {"ok": True, "closed": True}
        return original_close(decision)

    scene.manager.close = close
    if outcome == "preflight-error":

        def fail_validation(self):
            raise OSError("saved project unavailable")

        monkeypatch.setattr(native_close.ProvisionalClose, "validate", fail_validation)
    with pytest.raises(ValueError):
        scene.manager.prepare("save")
    scene.report.reset_mock()  # setup may report the expected absence of VLF history
    token = scene.manager.prepare("discard")["token"]
    scene.manager.receive("change", "lanctl_close_receipt", token)
    metadata = json.loads((draft.root / "workspace.json").read_text())
    assert scene.manager.provisional is None
    assert "closeLease" not in metadata
    if outcome == "closed":
        assert metadata["closed"] and metadata["owners"] == []
        scene.report.assert_not_called()
    else:
        assert owner in metadata["owners"] and not metadata.get("closed")
        with provisional_operation(draft, owner, coordinator=coordinator, base={}):
            assert DeviceDatabase(settings["database"]).load()[0].idf == "PC-001"
        if outcome == "rejected":
            assert scene.window.state.lanctl_close_error["errorId"] == "original-close-error"
