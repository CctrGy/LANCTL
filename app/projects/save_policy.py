from __future__ import annotations

import hashlib
import json
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from app.core.config import load_config
from app.core.logger import write_log


class SaveMode(str, Enum):
    MANUAL = "manual"
    MANUAL_CLOSE_CONSULT = "manual.inCloseConsult"
    TO_CLOSE = "automatic.toClose"
    TO_SCAN = "automatic.toScan"
    TIME_TO_SAVE = "automatic.timeToSave"
    ALL_CHANGES = "automatic.allChanges"


class SaveTrigger(str, Enum):
    CHANGE = "change"
    CLOSE = "close"
    SCAN = "scan"
    TIMER = "timer"


_ALIASES = {
    "manual": SaveMode.MANUAL.value,
    "manual.incloseconsult": SaveMode.MANUAL_CLOSE_CONSULT.value,
    "automatic.toclose": SaveMode.TO_CLOSE.value,
    "automatic.toscan": SaveMode.TO_SCAN.value,
    "automatic.timetosave": SaveMode.TIME_TO_SAVE.value,
    "automatic.allchanges": SaveMode.ALL_CHANGES.value,
    "automatic..allchanges": SaveMode.ALL_CHANGES.value,
}
_BUILTIN_TRIGGERS = {
    SaveMode.MANUAL.value: frozenset(),
    SaveMode.MANUAL_CLOSE_CONSULT.value: frozenset(),
    SaveMode.TO_CLOSE.value: frozenset({SaveTrigger.CLOSE.value}),
    SaveMode.TO_SCAN.value: frozenset({SaveTrigger.SCAN.value}),
    SaveMode.TIME_TO_SAVE.value: frozenset({SaveTrigger.TIMER.value}),
    SaveMode.ALL_CHANGES.value: frozenset(
        {SaveTrigger.CHANGE.value, SaveTrigger.SCAN.value, SaveTrigger.CLOSE.value}
    ),
}
_SAVE_LOCK = threading.RLock()


@dataclass(frozen=True, slots=True)
class SaveModeDefinition:
    mode: str
    triggers: frozenset[str]
    owner: str = "LANCTL"
    description: str = ""


@dataclass(frozen=True, slots=True)
class SaveResult:
    saved: bool
    mode: str
    trigger: str
    path: str = ""
    reason: str = ""


class ProjectAutosaveScheduler:
    """Temporizador cooperativo para sesiones persistentes de LANCTL."""

    def __init__(self) -> None:
        self._stop = threading.Event()
        self._thread = threading.Thread(
            target=self._run,
            name="LANCTL-project-autosave",
            daemon=True,
        )

    def start(self) -> ProjectAutosaveScheduler:
        self._thread.start()
        return self

    def stop(self) -> None:
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _run(self) -> None:
        while not self._stop.is_set():
            settings = load_config()
            try:
                minutes = float(settings.get("projectSaveIntervalMinutes", 5))
            except (TypeError, ValueError):
                minutes = 5.0
            if self._stop.wait(max(1.0, minutes * 60.0)):
                return
            try:
                save_active_project(SaveTrigger.TIMER)
            except Exception as error:  # noqa: BLE001 - un ciclo no detiene el siguiente
                write_log(f"PROJECT AUTOSAVE TIMER ERROR detail={error}")


def _plugin_modes() -> list[SaveModeDefinition]:
    try:
        from app.plugins import get_plugin_manager

        extensions = get_plugin_manager().extensions.list("project-save-mode")
    except (AttributeError, ImportError, RuntimeError, ValueError):
        return []
    modes = []
    for extension in extensions:
        specification = extension.specification
        mode = str(specification.get("mode") or extension.extension_id).strip()
        triggers = frozenset(
            str(value).strip().casefold() for value in specification.get("triggers", [])
        )
        invalid = triggers - {item.value for item in SaveTrigger}
        if not mode or invalid:
            continue
        modes.append(
            SaveModeDefinition(
                mode=mode,
                triggers=triggers,
                owner=extension.owner,
                description=str(specification.get("description", "")),
            )
        )
    return modes


def available_save_modes() -> list[SaveModeDefinition]:
    builtins = [
        SaveModeDefinition(SaveMode.MANUAL.value, _BUILTIN_TRIGGERS[SaveMode.MANUAL.value]),
        SaveModeDefinition(
            SaveMode.MANUAL_CLOSE_CONSULT.value,
            _BUILTIN_TRIGGERS[SaveMode.MANUAL_CLOSE_CONSULT.value],
            description="Pregunta al cerrar si hay cambios pendientes.",
        ),
        SaveModeDefinition(
            SaveMode.TO_CLOSE.value,
            _BUILTIN_TRIGGERS[SaveMode.TO_CLOSE.value],
            description="Guarda al cerrar LANCTL.",
        ),
        SaveModeDefinition(
            SaveMode.TO_SCAN.value,
            _BUILTIN_TRIGGERS[SaveMode.TO_SCAN.value],
            description="Guarda después de cada escaneo LAN.",
        ),
        SaveModeDefinition(
            SaveMode.TIME_TO_SAVE.value,
            _BUILTIN_TRIGGERS[SaveMode.TIME_TO_SAVE.value],
            description="Guarda periódicamente según el intervalo configurado.",
        ),
        SaveModeDefinition(
            SaveMode.ALL_CHANGES.value,
            _BUILTIN_TRIGGERS[SaveMode.ALL_CHANGES.value],
            description="Guarda después de cualquier cambio confirmado.",
        ),
    ]
    known = {item.mode.casefold() for item in builtins}
    return [*builtins, *(item for item in _plugin_modes() if item.mode.casefold() not in known)]


def normalize_save_mode(value: str, *, allow_plugins: bool = True) -> str:
    raw = str(value).strip()
    normalized = _ALIASES.get(raw.casefold())
    if normalized:
        return normalized
    if allow_plugins:
        for definition in available_save_modes():
            if definition.mode.casefold() == raw.casefold():
                return definition.mode
    choices = ", ".join(item.mode for item in available_save_modes())
    raise ValueError(f"SaveMode no válido: {value}. Opciones: {choices}")


def _definition(mode: str) -> SaveModeDefinition:
    normalized = normalize_save_mode(mode)
    return next(
        item for item in available_save_modes() if item.mode.casefold() == normalized.casefold()
    )


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def workspace_fingerprint(settings: Mapping[str, Any]) -> str | None:
    workspace = settings.get("projectWorkspace")
    if not isinstance(workspace, Mapping):
        return None
    files = [Path(str(workspace.get(key, ""))) for key in ("database", "groups")]
    if any(not path.is_file() for path in files):
        return None
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.name.encode("utf-8"))
        digest.update(_hash_file(path).encode("ascii"))
    return digest.hexdigest()


def workspace_is_dirty(settings: Mapping[str, Any]) -> bool:
    workspace = settings.get("projectWorkspace")
    current = workspace_fingerprint(settings)
    if not isinstance(workspace, Mapping) or current is None:
        return False
    metadata_path = Path(str(workspace.get("metadata", "")))
    if not metadata_path.is_file():
        return True
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True
    return metadata.get("workspaceHash") != current


def save_active_project(
    trigger: str | SaveTrigger = SaveTrigger.CHANGE,
    *,
    force: bool = False,
    config: Mapping[str, Any] | None = None,
) -> SaveResult:
    trigger_value = str(trigger.value if isinstance(trigger, SaveTrigger) else trigger).casefold()
    if trigger_value not in {item.value for item in SaveTrigger}:
        raise ValueError(f"disparador de guardado desconocido: {trigger}")
    with _SAVE_LOCK:
        settings = dict(config or load_config())
        mode = normalize_save_mode(str(settings.get("projectSaveMode", SaveMode.MANUAL.value)))
        active = str(settings.get("activeProject") or "").strip()
        if not active:
            return SaveResult(False, mode, trigger_value, reason="no-active-project")
        if not force and trigger_value not in _definition(mode).triggers:
            return SaveResult(False, mode, trigger_value, active, "mode-does-not-match")
        if not force and not workspace_is_dirty(settings):
            return SaveResult(False, mode, trigger_value, active, "workspace-unchanged")

        from app.projects.vlf import update_project
        from app.projects.workspace import activate_project_workspace

        result = update_project(active, config=settings)
        workspace = activate_project_workspace(result["path"], refresh=True)
        try:
            from app.plugins import get_plugin_manager

            get_plugin_manager().events.emit(
                "LANCTL.Project.File.Save",
                {"path": result["path"], "project_id": workspace.project_id},
            )
        except (ImportError, RuntimeError, ValueError):
            pass
        write_log(
            f"PROJECT SAVE mode={mode} trigger={trigger_value} "
            f"id={workspace.project_id} path={result['path']}"
        )
        return SaveResult(True, mode, trigger_value, result["path"], "saved")


def close_active_project(*, input_fn=input, output_fn=print) -> SaveResult:
    """Aplica la política de cierre y consulta únicamente si existen cambios."""

    settings = load_config()
    mode = normalize_save_mode(str(settings.get("projectSaveMode", SaveMode.MANUAL.value)))
    if mode != SaveMode.MANUAL_CLOSE_CONSULT.value:
        return save_active_project(SaveTrigger.CLOSE, config=settings)
    active = str(settings.get("activeProject") or "").strip()
    if not active:
        return SaveResult(False, mode, SaveTrigger.CLOSE.value, reason="no-active-project")
    if not workspace_is_dirty(settings):
        return SaveResult(False, mode, SaveTrigger.CLOSE.value, active, "workspace-unchanged")
    try:
        answer = input_fn("Hay cambios sin guardar. ¿Guardar el proyecto antes de cerrar? [S/n] ")
    except (EOFError, KeyboardInterrupt):
        output_fn("")
        answer = "n"
    if str(answer).strip().casefold() not in ("", "s", "si", "sí", "y", "yes"):
        write_log(f"PROJECT SAVE DECLINED mode={mode} trigger=close path={active}")
        return SaveResult(False, mode, SaveTrigger.CLOSE.value, active, "user-declined")
    return save_active_project(SaveTrigger.CLOSE, force=True, config=settings)


def start_autosave_scheduler() -> ProjectAutosaveScheduler:
    return ProjectAutosaveScheduler().start()
