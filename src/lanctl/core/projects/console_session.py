"""Own physical console lifetimes without borrowing the GUI's lifecycle."""

from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from math import isfinite
from pathlib import Path
from threading import Event, RLock, Thread
from time import monotonic

from lanctl.core.config import load_config
from lanctl.core.paths import application_path
from lanctl.core.project_context import project_identity, project_operation
from lanctl.core.projects.physical import workspace_path
from lanctl.core.projects.save_policy import (
    SaveMode,
    SaveTrigger,
    normalize_save_mode,
    save_active_project,
    workspace_is_dirty,
)
from lanctl.core.session import PROJECT_KEYS, bind_session, current_session

_current = ContextVar("lanctl_physical_console", default=None)


def _interval(settings):
    try:
        seconds = float(settings.get("projectSaveIntervalMinutes", 5)) * 60
    except (TypeError, ValueError, OverflowError):
        seconds = 300
    return max(1, seconds) if isfinite(seconds) else 300


class PhysicalConsoleSession:
    """Retain each operation's workspace; an explicit database never follows selection."""

    def __init__(self, database_path, *, follow_project=False):
        self.path = application_path(database_path).resolve()
        self.follow_project = follow_project
        self._fixed_config = None
        self._contexts = {}
        self._deadlines = {}
        self._messages = []
        self._lock = RLock()
        self._stop = Event()
        self._thread = None
        self._closed = False
        self._owner = current_session()

    @contextmanager
    def operation(self):
        settings = load_config()
        # Refresh permissions/preferences, retaining only the selected stores
        # and their save policy when this explicitly pinned project is inactive.
        if (
            not self.follow_project
            and self._fixed_config is not None
            and project_identity(settings) != project_identity(self._fixed_config)
        ):
            settings.update({key: deepcopy(self._fixed_config.get(key)) for key in PROJECT_KEYS})
            for key in ("projectSaveMode", "projectSaveIntervalMinutes"):
                settings[key] = self._fixed_config.get(key)
            if hasattr(settings, "project_base"):
                settings.project_base = {key: deepcopy(settings.get(key)) for key in PROJECT_KEYS}
                settings.base_values = deepcopy(dict(settings))
        with project_operation(settings):
            settings = load_config()
            path = (
                application_path(settings.get("physicalDatabase") or self.path).resolve()
                if self.follow_project
                else self.path
            )
            workspace = settings.get("projectWorkspace")
            if (
                settings.get("activeProject")
                and isinstance(workspace, dict)
                and workspace.get("database")
                and path == workspace_path(Path(workspace["database"])).resolve()
                and path == application_path(settings["physicalDatabase"]).resolve()
            ):
                key = tuple(project_identity(settings))
                with self._lock:
                    self._contexts[key] = deepcopy(settings)
                    self._deadlines.setdefault(key, monotonic() + _interval(settings))
                if not self.follow_project:
                    self._fixed_config = deepcopy(settings)
            yield path

    def start(self):
        if self._thread is None:
            self._thread = Thread(target=self._run, name="LANCTL-physical-autosave", daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            # Do not let a writer outlive its session or race a confirmed discard.
            self._thread.join()

    def messages(self):
        with self._lock:
            messages, self._messages = self._messages, []
            return messages

    def _refresh(self):
        current = load_config()
        key = tuple(project_identity(current))
        if key in self._contexts:
            self._contexts[key] = deepcopy(current)

    def _report(self, error, trigger):
        from lanctl.core.errors import errors

        if trigger == "timer":
            event = errors.from_exception(
                error,
                origin="LANCTL.Project.Physical.Session.Timer",
                code="PROJECT.PHYSICAL.SESSION.TIMER_FAILED",
                level=43,
                print_output=False,
                break_execution=False,
            )
        else:
            event = errors.from_exception(
                error,
                origin="LANCTL.Project.Physical.Session.Close",
                code="PROJECT.PHYSICAL.SESSION.CLOSE_FAILED",
                level=43,
                print_output=False,
                break_execution=False,
            )
        return (
            f"No se pudo guardar el proyecto; el workspace se conserva. [{event.error_id}] {error}"
        )

    def _tick(self):
        with self._lock:
            if self._closed or self._stop.is_set():
                return
            self._refresh()
            now = monotonic()
            for key, settings in self._contexts.items():
                # A shorter interval takes effect without waiting for the old deadline.
                deadline = min(self._deadlines[key], now + _interval(settings))
                self._deadlines[key] = deadline
                if now < deadline:
                    continue
                self._deadlines[key] = now + _interval(settings)
                try:
                    with project_operation(settings):
                        save_active_project(SaveTrigger.TIMER, config=settings)
                except Exception as error:  # noqa: BLE001 - keep the timer alive for retry
                    message = self._report(error, "timer")
                    self._messages[:] = [message]  # bound repeated failures while idle

    def _run(self):
        with bind_session(self._owner):
            while not self._stop.wait(1):
                try:
                    self._tick()
                except Exception as error:  # noqa: BLE001 - configuration can recover too
                    with self._lock:
                        self._messages[:] = [self._report(error, "timer")]

    def request_close(self, *, interactive=True, input_fn=None, output_fn=print):
        input_fn = input if input_fn is None else input_fn
        with self._lock:
            if self._closed:
                return True
            try:
                self._refresh()
                decisions = []
                for settings in self._contexts.values():
                    mode = normalize_save_mode(settings.get("projectSaveMode", "manual"))
                    force = False
                    if mode == SaveMode.MANUAL_CLOSE_CONSULT.value:
                        if not workspace_is_dirty(settings):
                            continue
                        if not interactive:
                            output_fn(
                                "Cambios pendientes conservados en el workspace; no se guardó el VLF."
                            )
                            continue
                        while True:
                            try:
                                answer = (
                                    str(
                                        input_fn(
                                            f"Guardar {settings['activeProject']} antes de cerrar? "
                                            "[S/n/c=cancelar] "
                                        )
                                    )
                                    .strip()
                                    .casefold()
                                )
                            except (EOFError, KeyboardInterrupt):
                                return False
                            if answer in {"c", "cancel", "cancelar"}:
                                return False
                            if answer in {"n", "no"}:
                                break
                            if answer in {"", "s", "si", "sí", "y", "yes"}:
                                force = True
                                break
                            output_fn("Responde S, n o c.")
                        if not force:
                            continue
                    decisions.append((settings, force))
                for settings, force in decisions:
                    with project_operation(settings):
                        save_active_project(SaveTrigger.CLOSE, force=force, config=settings)
                self._closed = True
                return True
            except Exception as error:  # noqa: BLE001 - failed close leaves the editor usable
                output_fn(self._report(error, "close"))
                return False


@contextmanager
def physical_console_session(database_path, *, follow_project=False):
    """Entrypoint and console adapters share one owner, including direct API callers."""
    existing = _current.get()
    if existing is not None and existing.path == application_path(database_path).resolve():
        yield existing
        return
    session = PhysicalConsoleSession(database_path, follow_project=follow_project)
    token = _current.set(session)
    try:
        yield session
    finally:
        try:
            session.stop()
        finally:
            _current.reset(token)
