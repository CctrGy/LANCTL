"""Process/session adapter for the shared coordinator, without UI dependencies."""

from __future__ import annotations

import sqlite3
import sys
import threading
from contextlib import ExitStack, contextmanager
from contextvars import ContextVar
from copy import deepcopy
from functools import wraps
from pathlib import Path
from uuid import uuid4

from lanctl.core.coordination import Coordinator

PROJECT_KEYS = frozenset(
    {
        "activeProject",
        "projectWorkspace",
        "database",
        "groups",
        "networkDatabase",
        "networkGroups",
        "databaseLog",
        "physicalDatabase",
        "monitorRuntime",
        "monitorIncidents",
        "monitorLock",
        "monitorDatabase",
        "monitorProfiles",
        "monitorAssignments",
    }
)
_current = None
_guard = threading.RLock()
_reporting = threading.local()
_task_id = ContextVar("lanctl_task_id", default=None)
_bound_session = ContextVar("lanctl_bound_session", default=None)


def current_task_id():
    return _task_id.get()


def current_session():
    return _bound_session.get() or _current


@contextmanager
def bind_session(session):
    """Pin background workers to their owning interface, not a nested launcher."""
    token = _bound_session.set(session)
    try:
        yield
    finally:
        _bound_session.reset(token)


def _report(error):
    if getattr(_reporting, "active", False):
        return
    _reporting.active = True
    try:
        from lanctl.core.errors import errors

        errors.from_exception(
            error,
            origin="LANCTL.Core.Coordination.Transport",
            code="COORDINATION.TRANSPORT.FAILED",
            level=35,
            print_output=False,
            once_key="coordination.transport.failed",
        )
    finally:
        _reporting.active = False


class Session:
    def __init__(self, launcher, mode, config, *, coordinator=None, parent=None):
        self.coordinator = coordinator or Coordinator()
        self.launcher, self.mode = launcher, mode
        self.config = {key: deepcopy(config.get(key)) for key in PROJECT_KEYS}
        self.lock = threading.RLock()
        self.resources = set()
        self.id = self.coordinator.register(launcher, mode, self.project, parent)
        self.cursor = self.coordinator.latest()
        self.handler = None
        self.subscribers = []
        self._pending_changed = False
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, name="LANCTL-coordinator", daemon=True)
        self.thread.start()

    @property
    def project(self):
        return self.config.get("activeProject")

    def emit(self, event, **kwargs):
        kwargs.setdefault("correlation", current_task_id())
        kwargs.setdefault("project", self.project)
        try:
            return self.coordinator.publish(self.id, event, **kwargs)
        except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
            _report(error)
        return None

    def poll(self):
        self.coordinator.heartbeat(self.id, self.project, self.handler is not None)
        changed = self._pending_changed
        for event in self.coordinator.events(self.cursor):
            if event["seq"] > self.cursor + 1:
                changed = True  # retained history gap: reconcile from storage
            self.cursor = event["seq"]
            if event["session"] == self.id:
                continue
            for subscriber in tuple(self.subscribers):
                try:
                    subscriber(event)
                except Exception as error:  # noqa: BLE001 - isolate external observers
                    _report(error)
            if event["event"] == "LANCTL.Core.Storage.Changed" and event["project"] == self.project:
                changed = True
            if event["event"] == "LANCTL.Core.Config.Changed":
                changed = True
        if self.handler:
            if changed:
                self._pending_changed = True
                self.handler({"action": "data-changed"})
                self._pending_changed = False
            for command in self.coordinator.claim(self.id):
                try:
                    self.handler(command)
                except Exception:
                    self.coordinator.acknowledge(command["id"], False)
                    raise
                self.coordinator.acknowledge(command["id"], True)

    def _run(self):
        count = 0
        while not self.stop_event.wait(1):
            try:
                with bind_session(self):
                    self.poll()
                count += 1
                if count % 30 == 0:
                    self.coordinator.maintain()
            except Exception as error:  # noqa: BLE001 - an observer must not kill its UI
                _report(error)

    def close(self):
        self.stop_event.set()
        self.thread.join(timeout=6)
        self.coordinator.close(self.id)


def overlay_config(config):
    session = current_session()
    if session:
        with session.lock:
            replacement = deepcopy(config)
            replacement.update(deepcopy(session.config))
            return replacement
    return config


def prepare_config_save(config, stored):
    """Persist shared settings while retaining another session's last-used project.

    A deliberate project change updates the last-used project for future starts;
    existing sessions retain their pinned selection.
    """
    session = current_session()
    if not session:
        return config
    with session.lock:
        changed = any(config.get(key) != session.config.get(key) for key in PROJECT_KEYS)
        if changed:
            return config
        replacement = deepcopy(config)
        replacement.update({key: deepcopy(stored.get(key)) for key in PROJECT_KEYS})
        return replacement


def commit_config(config):
    session = current_session()
    if session:
        with session.lock:
            changed = any(config.get(key) != session.config.get(key) for key in PROJECT_KEYS)
            if changed:
                session.config = {key: deepcopy(config.get(key)) for key in PROJECT_KEYS}
                session.emit("LANCTL.Core.Session.Project")


@contextmanager
def task(origin):
    session = current_session()
    if not session:
        yield None
        return
    identifier = uuid4().hex
    session.coordinator.task(session.id, origin, identifier)
    token = _task_id.set(identifier)
    session.emit("LANCTL.Core.Task.Started", correlation=identifier)
    outcome = {"id": identifier, "state": "finished"}
    try:
        yield outcome
    except BaseException as error:
        outcome["state"] = (
            "finished" if isinstance(error, SystemExit) and error.code in (None, 0) else "failed"
        )
        raise
    finally:
        try:
            session.coordinator.task(session.id, origin, identifier, outcome["state"])
            session.emit(
                "LANCTL.Core.Task.Finished",
                correlation=identifier,
                metadata={"state": outcome["state"]},
            )
        except (OSError, sqlite3.Error) as error:
            # A diagnostic failure must not turn a committed write into a
            # reported application failure or hide the original exception.
            _report(error)
        _task_id.reset(token)


def _invoke(function, argv, args, kwargs):
    with task("LANCTL.Core.Command.Execute") as outcome:
        result = function(argv, *args, **kwargs)
        if outcome and isinstance(result, int) and result != 0:
            outcome["state"] = "failed"
        return result


def notify_write(path):
    session = current_session()
    if not session:
        return
    from lanctl.core.paths import application_path

    with session.lock:
        tracked = [
            session.config.get(key)
            for key in ("database", "groups", "physicalDatabase", "activeProject")
        ]
    target = Path(path).resolve()
    if target in session.resources or any(
        value and application_path(value).resolve() == target for value in tracked
    ):
        session.emit("LANCTL.Core.Storage.Changed", metadata={"path": str(target)})


def coordinated_launcher(launcher):
    def decorate(function):
        @wraps(function)
        def wrapped(argv=None, *args, **kwargs):
            global _current
            arguments = list(sys.argv[1:] if argv is None else argv)
            if any(
                word in {"--help", "-h", "/?", "--version", "ephemeral", "-e"} for word in arguments
            ):
                return function(argv, *args, **kwargs)
            parent = current_session()
            # Interactive commands re-enter the same main; preserve their session.
            if parent and parent.launcher == launcher:
                return _invoke(function, argv, args, kwargs)
            from lanctl.core.config import load_config

            stack = ExitStack()
            try:
                config = load_config()
                if launcher == "lanctl" and not arguments:
                    preferred = config.get("startupInterface", "cli")
                    if preferred not in {"cli", "tui", "gui"}:
                        preferred = "cli"
                    arguments = [f"--{preferred}"]
                    argv = arguments
                mode = (
                    "gui"
                    if "--gui" in arguments
                    else "tui"
                    if any(word in {"--tui", "-tui"} for word in arguments)
                    or (launcher == "lanip" and not arguments)
                    else "backend"
                    if "foreground" in arguments
                    else "cli"
                )
                if mode == "gui":
                    from lanctl.core.gui_instance import GuiInstance

                    if not stack.enter_context(GuiInstance(launcher)):
                        stack.close()
                        return 0
                session = Session(launcher, mode, config, parent=parent.id if parent else None)
            except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
                stack.close()
                from lanctl.core.errors import errors

                errors.from_exception(
                    error,
                    origin="LANCTL.Core.Coordination.Startup",
                    code="COORDINATION.STARTUP.FAILED",
                    level=44,
                )
                return 2
            with _guard:
                _current = session
            session.emit(
                "LANCTL.Core.Session.Started", metadata={"launcher": launcher, "mode": mode}
            )
            try:
                return _invoke(function, argv, args, kwargs)
            finally:
                session.emit("LANCTL.Core.Session.Stopped")
                with _guard:
                    _current = parent
                try:
                    session.close()
                except (OSError, sqlite3.Error) as error:
                    _report(error)
                finally:
                    stack.close()

        return wrapped

    return decorate
