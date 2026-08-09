from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from app.core.config import load_config
from app.core.paths import application_path


@dataclass(frozen=True)
class LogCleanupResult:
    enabled: bool
    retention_days: int
    deleted: tuple[Path, ...] = ()


def cleanup_old_logs(
    directory: str | Path,
    retention_days: int,
    *,
    today: date | None = None,
) -> tuple[Path, ...]:
    """Elimina solamente logs diarios reconocidos que superen la retención."""
    if retention_days < 1:
        raise ValueError("la retención de logs debe ser de al menos 1 día")

    current_day = today or datetime.now(timezone.utc).astimezone().date()
    oldest_allowed = current_day - timedelta(days=retention_days)
    log_directory = application_path(directory)
    if not log_directory.is_dir():
        return ()

    deleted: list[Path] = []
    for path in log_directory.iterdir():
        if not path.is_file() or path.suffix.casefold() != ".log":
            continue
        try:
            day, month, year = map(int, path.stem.split("-"))
            log_day = date(year, month, day)
        except ValueError:
            continue
        if log_day < oldest_allowed and log_day != current_day:
            path.unlink()
            deleted.append(path.resolve())
    return tuple(sorted(deleted))


def run_automatic_log_cleanup() -> LogCleanupResult:
    """Ejecuta la tarea interna según la configuración persistente."""
    config = load_config()
    enabled = bool(config.get("logCleanupEnabled", False))
    retention_days = int(config.get("logRetentionDays", 90))
    if not enabled:
        return LogCleanupResult(False, retention_days)
    directory = config.get("programLog", config["log"])
    deleted = cleanup_old_logs(directory, retention_days)
    return LogCleanupResult(True, retention_days, deleted)
