from __future__ import annotations

import json
import tempfile
import threading
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from lanctl.core.config import load_config
from lanctl.core.logger import write_log


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
    "manual.consulttoclose": SaveMode.MANUAL_CLOSE_CONSULT.value,
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
_CLOSE_ANSWER: str | None = None


def remember_close_answer(answer: str) -> None:
    """Entrega una decisión tomada por una interfaz al cierre común de la aplicación."""

    global _CLOSE_ANSWER
    normalized = str(answer).strip().casefold()
    if normalized not in {"save", "discard"}:
        raise ValueError("decisión de cierre no válida")
    _CLOSE_ANSWER = normalized


def _consume_close_answer() -> str | None:
    global _CLOSE_ANSWER
    answer, _CLOSE_ANSWER = _CLOSE_ANSWER, None
    return answer


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
                from lanctl.core.errors import errors

                errors.from_exception(
                    error,
                    origin="LANCTL.Project.Autosave.Timer",
                    code="PROJECT.AUTOSAVE.RETRY",
                    level=18,
                    print_output=False,
                    break_execution=False,
                )


def _plugin_modes() -> list[SaveModeDefinition]:
    try:
        from lanctl.core.plugins import get_plugin_manager

        extensions = get_plugin_manager().extensions.list("project-save-mode")
    except (AttributeError, ImportError, RuntimeError, ValueError) as error:
        from lanctl.core.errors import errors

        errors.from_exception(
            error,
            origin="LANCTL.Project.SaveMode.Discovery",
            code="PROJECT.SAVE_MODE.FALLBACK",
            level=12,
            print_output=False,
            break_execution=False,
        )
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


def workspace_fingerprint(settings: Mapping[str, Any]) -> str | None:
    workspace = settings.get("projectWorkspace")
    if not isinstance(workspace, Mapping):
        return None
    files = [Path(str(workspace.get(key, ""))) for key in ("database", "groups")]
    if not files[0].is_file():
        return None
    from lanctl.core.database import DeviceDatabase
    from lanctl.core.group_database import GroupDatabase

    database = DeviceDatabase(str(files[0]))
    try:
        devices = database.load()
        groups = GroupDatabase(str(files[1]), database).load()
        device_rows = [device.to_dict() for device in devices]
        group_rows = [group.to_dict() for group in groups]
    except ValueError:
        # Mantiene la detección de cambios incluso para un almacén antiguo o
        # parcialmente migrado; el guardado real seguirá validando su esquema.
        device_rows = json.loads(files[0].read_text(encoding="utf-8"))
        group_rows = json.loads(files[1].read_text(encoding="utf-8")) if files[1].is_file() else []
    from lanctl.core.projects.fingerprint import inventory_fingerprint

    return inventory_fingerprint(device_rows, group_rows)


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


def _verify_saved_workspace(
    result: Mapping[str, Any],
    settings: Mapping[str, Any],
    *,
    expected: str | None = None,
) -> dict:
    """Valida el VLF escrito, compara su inventario y confirma el workspace."""

    from lanctl.core.projects.vlf import inspect_project, verify_project
    from lanctl.core.projects.workspace import (
        mark_workspace_synchronized,
        prepare_project_workspace,
    )

    verified = verify_project(result["path"])
    project_info = inspect_project(result["path"])
    workspace_mapping = settings.get("projectWorkspace")
    if not isinstance(workspace_mapping, Mapping):
        raise RuntimeError("el proyecto activo no tiene un workspace verificable")
    expected = expected or workspace_fingerprint(settings)
    with tempfile.TemporaryDirectory(prefix="lanctl-project-verify-") as temporary:
        extracted = prepare_project_workspace(
            result["path"], root=temporary, refresh=True, discard_changes=True
        )
        observed = workspace_fingerprint(
            {
                "projectWorkspace": {
                    "database": str(extracted.database),
                    "groups": str(extracted.groups),
                }
            }
        )
    if expected is None or observed != expected:
        backup = str(result.get("backup") or "")
        restored = False
        if backup and Path(backup).is_file():
            from lanctl.core.persistence import restore_backup

            restore_backup(result["path"], backup)
            restored = True
        outcome = (
            "se ha restaurado la copia de seguridad"
            if restored
            else "no había una copia de seguridad disponible para restaurar"
        )
        raise RuntimeError(
            "la verificación posterior al guardado no coincide con el workspace; " + outcome
        )
    mark_workspace_synchronized(
        workspace_mapping, project_info=project_info, workspace_hash=expected
    )
    return {"verified": verified, "project": project_info}


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

        from lanctl.core.file_transaction import locked_files
        from lanctl.core.projects.vlf import update_project

        workspace = settings.get("projectWorkspace")
        if not isinstance(workspace, Mapping):
            raise RuntimeError("el proyecto activo no tiene un workspace verificable")
        database = Path(str(workspace.get("database", "")))
        groups = Path(str(workspace.get("groups", "")))
        # La instantánea esperada y la creación del VLF comparten los mismos
        # locks que las bases. Otro proceso solo podrá escribir después; ese
        # cambio seguirá apareciendo pendiente en vez de quedar falsamente
        # confirmado por un hash calculado demasiado tarde.
        with locked_files((database, groups, Path(active))):
            expected = workspace_fingerprint(settings)
            result = update_project(active, config=settings)
            verification = _verify_saved_workspace(result, settings, expected=expected)
        verified = verification["verified"]
        project_info = verification["project"]
        project_id = str(project_info.get("id") or "")
        try:
            from lanctl.core.plugins import get_plugin_manager

            get_plugin_manager().events.emit(
                "LANCTL.Project.File.Save",
                {"path": result["path"], "project_id": project_id},
            )
        except (ImportError, RuntimeError, ValueError):
            pass
        write_log(
            f"PROJECT SAVE mode={mode} trigger={trigger_value} "
            f"id={project_id} checksum={verified.get('checksum', '-')} path={result['path']}"
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
    remembered = _consume_close_answer()
    if remembered is not None:
        answer = "s" if remembered == "save" else "n"
    else:
        try:
            answer = input_fn(
                "Hay cambios sin guardar. ¿Guardar el proyecto antes de cerrar? [S/n] "
            )
        except (EOFError, KeyboardInterrupt):
            output_fn("")
            answer = "n"
    if str(answer).strip().casefold() not in ("", "s", "si", "sí", "y", "yes"):
        write_log(f"PROJECT SAVE DECLINED mode={mode} trigger=close path={active}")
        return SaveResult(False, mode, SaveTrigger.CLOSE.value, active, "user-declined")
    return save_active_project(SaveTrigger.CLOSE, force=True, config=settings)


def start_autosave_scheduler() -> ProjectAutosaveScheduler:
    return ProjectAutosaveScheduler().start()
