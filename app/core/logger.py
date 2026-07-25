from __future__ import annotations

from datetime import datetime
from pathlib import Path
from threading import Lock
from app.core.paths import application_path


LOG_DIRECTORY = application_path("data/als/log")
_LOCK = Lock()


def write_log(message: str, directory: Path | None = None) -> Path:
    """Añade una línea al log diario con hora local en formato 24 horas."""
    now = datetime.now()
    log_directory = (
        application_path(directory) if directory is not None else LOG_DIRECTORY
    )
    path = log_directory / f"{now:%d-%m-%Y}.log"
    clean_message = " | ".join(str(message).splitlines()).strip()
    line = f"{now:%H:%M:%S} {clean_message}\n"

    with _LOCK:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="") as log:
            log.write(line)
    return path.resolve()
