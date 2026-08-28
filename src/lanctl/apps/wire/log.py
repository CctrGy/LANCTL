"""Gestión de los registros diarios de LANWRE."""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from .error import Error, ErrorLevel
from .path import application_path
from .xfile import locked_file

LOG_DIRECTORY = application_path("data/logs")
_LOCK = Lock()


def write_log(message: str, directory: str | Path | None = None) -> Path:
    """Añade una línea al archivo de registro del día y devuelve su ruta."""
    now = datetime.now(timezone.utc).astimezone()
    log_directory = application_path(directory or LOG_DIRECTORY)
    target = log_directory / f"{now:%Y-%m-%d}.log"
    clean_message = " | ".join(str(message).splitlines()).strip()
    line = f"{now:%H:%M:%S} {clean_message}\n"
    with _LOCK, locked_file(target):
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8", newline="") as stream:
            stream.write(line)
    return target.resolve()


def write_error(error: Error, directory: str | Path | None = None) -> Path:
    """Escribe un :class:`Error` en un formato estructurado y legible."""
    if not isinstance(error, Error):
        raise TypeError("write_error requiere una instancia de Error")

    fields = [
        f"level={error.level_name}",
        f"code={error.code}",
        f"caused={error.caused}",
        f"breakable={str(error.breakable).lower()}",
        f"text={json.dumps(error.text, ensure_ascii=False)}",
    ]
    if error.context:
        fields.append(
            "context="
            + json.dumps(error.context, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        )
    if error.cause is not None:
        fields.extend(
            (
                f"cause_type={type(error.cause).__name__}",
                f"cause_text={json.dumps(str(error.cause), ensure_ascii=False)}",
            )
        )
    return write_log(" | ".join(fields), directory)


def write_exception(
    exception: BaseException,
    *,
    caused: str,
    directory: str | Path | None = None,
    text: str | None = None,
    level: int | ErrorLevel = ErrorLevel.ERROR,
    breakable: bool = False,
    code: str = "LANWRE_ERROR",
    context: Mapping[str, Any] | None = None,
) -> Error:
    """Normaliza una excepción, la registra y devuelve el ``Error`` creado."""
    error = (
        exception
        if isinstance(exception, Error)
        else Error.wrap(
            exception,
            caused=caused,
            text=text,
            level=level,
            breakable=breakable,
            code=code,
            context=context,
        )
    )
    write_error(error, directory)
    return error


def cleanup_old_logs(
    directory: str | Path = LOG_DIRECTORY,
    retention_days: int = 90,
    *,
    today: date | None = None,
) -> tuple[Path, ...]:
    """Elimina únicamente logs diarios reconocidos anteriores a la retención."""
    if retention_days < 1:
        raise ValueError("la retención debe ser de al menos 1 día")
    current_day = today or datetime.now(timezone.utc).astimezone().date()
    oldest_allowed = current_day - timedelta(days=retention_days)
    log_directory = application_path(directory)
    if not log_directory.is_dir():
        return ()

    deleted: list[Path] = []
    for target in log_directory.glob("*.log"):
        try:
            log_day = date.fromisoformat(target.stem)
        except ValueError:
            continue
        if log_day < oldest_allowed and log_day != current_day:
            target.unlink()
            deleted.append(target.resolve())
    return tuple(sorted(deleted))


__all__ = [
    "LOG_DIRECTORY",
    "cleanup_old_logs",
    "write_error",
    "write_exception",
    "write_log",
]
