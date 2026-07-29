from __future__ import annotations

from datetime import datetime
from pathlib import Path
from threading import Lock
from app.core.paths import application_path


PROGRAM_LOG_DIRECTORY = application_path("data/als/log")
_LOCK = Lock()


def write_log(message: str, directory: Path | None = None) -> Path:
    """Añade una línea al log operativo diario del programa."""
    now = datetime.now()
    if directory is None:
        from app.core.config import load_config

        configured = load_config().get("programLog", str(PROGRAM_LOG_DIRECTORY))
        log_directory = application_path(configured)
    else:
        log_directory = application_path(directory)
    return _append_daily_log(message, log_directory, now)


def write_database_log(message: str, directory: Path | None = None) -> Path | None:
    """Añade una entrada al VLF activo o al directorio explícito de pruebas."""
    now = datetime.now()
    if directory is None:
        from app.core.config import load_config
        from app.projects.vlf import append_database_log

        active_project = load_config().get("activeProject")
        if not active_project:
            return None
        with _LOCK:
            return append_database_log(active_project, message, now=now)
    return _append_daily_log(message, application_path(directory), now)


def _append_daily_log(message: str, log_directory: Path, now: datetime) -> Path:
    path = log_directory / f"{now:%d-%m-%Y}.log"
    clean_message = " | ".join(str(message).splitlines()).strip()
    line = f"{now:%H:%M:%S} {clean_message}\n"

    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="") as log:
            log.write(line)
    return path.resolve()
