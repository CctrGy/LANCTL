from __future__ import annotations

import json
import re
import uuid
import zipfile
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field, fields
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from app.core.config import load_config

ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$", re.IGNORECASE)
RESULTS = {
    "success",
    "sent",
    "online",
    "offline",
    "skipped",
    "blocked",
    "timeout",
    "cancelled",
    "error",
    "invalid",
}
SENSITIVE = re.compile(
    r"password|passwd|credential|secret|token|private.?key|api.?key",
    re.IGNORECASE,
)
IDENTITY_FIELDS = {"ip", "alias", "name", "mac"}


def redact(value: Any, key: str = "") -> Any:
    """Oculta secretos de forma recursiva antes de persistir un evento."""

    if SENSITIVE.search(str(key)):
        return "[OCULTO]"
    if isinstance(value, dict):
        return {str(item_key): redact(item, str(item_key)) for item_key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


@dataclass(frozen=True)
class DeviceSnapshot:
    id: str = ""
    mac: str = ""
    ip: str = ""
    label: str = ""


@dataclass(frozen=True)
class HistoryEvent:
    type: str
    source: str
    actor: str
    result: str
    summary: str
    timestamp: str = field(default_factory=lambda: datetime.now().astimezone().isoformat())
    schemaVersion: int = 1
    eventId: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlationId: str | None = None
    runId: str | None = None
    taskId: str | None = None
    operationId: str | None = None
    device: DeviceSnapshot | None = None
    changes: tuple[dict, ...] = ()
    details: dict = field(default_factory=dict)
    error: dict | None = None
    durationMs: int | None = None

    def __post_init__(self) -> None:
        if self.schemaVersion != 1 or not ID_PATTERN.fullmatch(self.type):
            raise ValueError("tipo de evento no válido")
        if not self.source or not self.actor:
            raise ValueError("source y actor son obligatorios")
        if self.result not in RESULTS:
            raise ValueError("resultado de historial no válido")
        parsed = datetime.fromisoformat(self.timestamp)
        if parsed.tzinfo is None:
            raise ValueError("timestamp debe incluir zona horaria")
        for value in (self.taskId, self.operationId):
            if value and not ID_PATTERN.fullmatch(value):
                raise ValueError("id de traza no válido")

    def to_dict(self) -> dict:
        value = asdict(self)
        value["changes"] = [redact(item) for item in self.changes]
        value["details"] = redact(self.details)
        value["error"] = redact(self.error)
        value["summary"] = str(redact(self.summary, "summary"))
        return {key: item for key, item in value.items() if item not in (None, {}, [], ())}

    @classmethod
    def from_dict(cls, value: dict) -> HistoryEvent:
        allowed = {model_field.name for model_field in fields(cls)}
        unknown = set(value) - allowed
        if unknown:
            raise ValueError("campos de historial desconocidos: " + ", ".join(sorted(unknown)))
        data = dict(value)
        device = data.get("device")
        if isinstance(device, dict):
            data["device"] = DeviceSnapshot(**device)
        data["changes"] = tuple(data.get("changes", ()))
        return cls(**data)


class HistoryWriter:
    def __init__(self, project: str | Path) -> None:
        self.project = Path(project)

    def write(self, event: HistoryEvent) -> HistoryEvent:
        # Cargar VLF implica leer SQLite, plugins e inventario; se pospone hasta
        # que exista un proyecto real al que anexar el evento.
        from app.projects.vlf import append_history_event

        append_history_event(
            self.project,
            event.to_dict(),
            now=datetime.fromisoformat(event.timestamp),
        )
        return event


class HistoryReader:
    def __init__(self, project: str | Path) -> None:
        self.project = Path(project)

    def read(self, strict: bool = False) -> list[HistoryEvent]:
        events: list[HistoryEvent] = []
        with zipfile.ZipFile(self.project) as archive:
            for name in sorted(archive.namelist()):
                if name.startswith("logs/events/") and name.endswith(".jsonl"):
                    events.extend(self._structured_events(archive, name, strict))
                elif re.fullmatch(r"logs/\d{2}-\d{2}-\d{4}\.log", name):
                    text = archive.read(name).decode("utf-8", errors="replace")
                    events.extend(_legacy(name, text))
        return events

    @staticmethod
    def _structured_events(archive: zipfile.ZipFile, name: str, strict: bool) -> list[HistoryEvent]:
        rows = archive.read(name).decode("utf-8", errors="replace").splitlines()
        events = []
        for number, line in enumerate(rows, 1):
            if not line.strip():
                continue
            try:
                events.append(HistoryEvent.from_dict(json.loads(line)))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
                if strict:
                    raise ValueError(f"evento corrupto en {name}:{number}") from error
        return events


def _legacy(name: str, text: str) -> list[HistoryEvent]:
    day_number, month, year = map(int, Path(name).stem.split("-"))
    day = date(year, month, day_number)
    local_timezone = datetime.now().astimezone().tzinfo
    events = []
    for line in text.splitlines():
        match = re.match(r"(\d{2}:\d{2}:\d{2})\s+(.*)", line)
        if not match:
            continue
        event_time = time.fromisoformat(match.group(1))
        timestamp = datetime.combine(day, event_time, tzinfo=local_timezone)
        body = match.group(2)
        identity = ""
        event_type = "audit.legacy"
        changes = []
        change = re.match(r"CAMBIO\s+(\S+)\s+(.*)", body)
        if change:
            identity = change.group(1)
            event_type = "device.updated"
            changes = _legacy_changes(change.group(2))
        events.append(
            HistoryEvent(
                event_type,
                "legacy.vlf",
                "local",
                "success",
                body,
                timestamp=timestamp.isoformat(),
                device=(DeviceSnapshot(id=identity, label=identity) if identity else None),
                changes=tuple(changes),
                details={"format": "legacy"},
            )
        )
    return events


def _legacy_changes(text: str) -> list[dict]:
    changes = []
    for item in text.split("; "):
        field_name, separator, values = item.partition(":")
        before, arrow, after = values.partition("=>")
        if separator and arrow:
            changes.append(
                {
                    "field": field_name,
                    "before": redact(before, field_name),
                    "after": redact(after, field_name),
                }
            )
    return changes


def _event_identities(event: HistoryEvent) -> set[str]:
    current = (
        {
            value.casefold()
            for value in (
                event.device.id,
                event.device.mac,
                event.device.ip,
                event.device.label,
            )
            if value
        }
        if event.device
        else set()
    )
    historical = {
        str(change.get(side, "")).strip('"').casefold()
        for change in event.changes
        for side in ("before", "after")
        if change.get("field", "").casefold() in IDENTITY_FIELDS
    }
    return current | historical


class HistoryService:
    def __init__(self, project: str | Path | None = None) -> None:
        configured = project or load_config().get("activeProject")
        if not configured:
            raise ValueError("no hay un proyecto VLF activo")
        self.project = Path(configured)
        if not self.project.is_file():
            raise ValueError("no hay un proyecto VLF activo")

    def write(self, event: HistoryEvent) -> HistoryEvent:
        return HistoryWriter(self.project).write(event)

    def query(
        self,
        selector: str | None = None,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
        types: Iterable[str] = (),
        source: str | None = None,
        result: str | None = None,
        errors: bool = False,
        search: str | None = None,
        limit: int = 100,
        reverse: bool = False,
    ) -> list[HistoryEvent]:
        rows = HistoryReader(self.project).read()
        if selector:
            rows = self._matching_identity(rows, selector)

        type_filter = set(types)
        source_filter = source.casefold() if source else ""
        search_filter = search.casefold() if search else ""

        def accepted(event: HistoryEvent) -> bool:
            if date_from or date_to:
                event_date = datetime.fromisoformat(event.timestamp).date()
                if date_from and event_date < date_from:
                    return False
                if date_to and event_date > date_to:
                    return False
            if type_filter and event.type not in type_filter:
                return False
            if source_filter and event.source.casefold() != source_filter:
                return False
            if result and event.result != result:
                return False
            if errors and not (event.error or event.result == "error"):
                return False
            return (
                not search_filter
                or search_filter in json.dumps(event.to_dict(), ensure_ascii=False).casefold()
            )

        rows = [event for event in rows if accepted(event)]
        rows.sort(
            key=lambda event: datetime.fromisoformat(event.timestamp),
            reverse=reverse,
        )
        return rows[: max(1, min(int(limit), 10_000))]

    @staticmethod
    def _matching_identity(rows: list[HistoryEvent], selector: str) -> list[HistoryEvent]:
        wanted = selector.casefold()
        identities = {wanted}
        for event in rows:
            event_identities = _event_identities(event)
            if wanted in event_identities:
                identities.update(event_identities)
        return [
            event
            for event in rows
            if event.device and identities.intersection(_event_identities(event))
        ]
