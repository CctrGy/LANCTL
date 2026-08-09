from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from app.core.file_transaction import atomic_write_json, transactional_method

TASK_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


def utc_now() -> datetime:
    return datetime.now().astimezone()


@dataclass
class OperationResult:
    runId: str
    taskId: str
    operationId: str
    target: str
    status: str
    startedAt: str
    finishedAt: str
    durationMs: int
    error: dict | None = None
    detail: dict | None = None

    def to_dict(self) -> dict:
        return {key: value for key, value in asdict(self).items() if value is not None}


def result(
    task_id: str,
    operation_id: str,
    target: str,
    status: str,
    started: datetime,
    *,
    code: str | None = None,
    message: str = "",
    dependency: str | None = None,
    detail: dict | None = None,
    run_id: str | None = None,
) -> OperationResult:
    finished = utc_now()
    error = None
    if code:
        error = {"code": code, "origin": operation_id, "message": message}
        if dependency:
            error["dependency"] = dependency
    return OperationResult(
        run_id or str(uuid.uuid4()),
        task_id,
        operation_id,
        target,
        status,
        started.isoformat(),
        finished.isoformat(),
        max(0, int((finished - started).total_seconds() * 1000)),
        error,
        detail,
    )


class JsonStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> dict:
        if not self.path.exists():
            return {"sequences": {}, "runs": {}}
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("el almacén de tareas debe ser un objeto JSON")
        value.setdefault("sequences", {})
        value.setdefault("runs", {})
        return value

    @transactional_method
    def save(self, value: dict) -> None:
        atomic_write_json(self.path, value)
