"""Bounded, read-only union of program logs and project audit logs."""

from __future__ import annotations

import json
import re
import zipfile
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

from lanctl.core.paths import application_path

MAX_READ = 1024 * 1024


def _rows(text, source, name, limit):
    rows = []
    for line in deque(text.splitlines(), maxlen=limit):
        level = None
        if "ERROR_EVENT " in line:
            try:
                event = json.loads(line.split("ERROR_EVENT ", 1)[1])
                level = int(event["level"])
            except (ValueError, KeyError, TypeError):
                level = None
        # Strip terminal escapes and C0 controls from untrusted log content.
        clean = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", line)
        clean = "".join(char for char in clean if char.isprintable() or char == "\t")
        rows.append({"source": source, "file": name, "level": level, "message": clean[:4096]})
    return rows


def _date(name):
    for pattern in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return (
                datetime.strptime(Path(name).stem, pattern)
                .replace(tzinfo=timezone.utc)
                .strftime("%Y-%m-%d")
            )
        except ValueError:
            continue
    return ""


def read_events(config, *, project=None, source="all", limit=100, minimum=1):
    if not 1 <= limit <= 1000 or not 1 <= minimum <= 59:
        raise ValueError("limit debe estar entre 1-1000 y level entre 1-59")
    rows = []
    if source in {"all", "program"}:
        directory = application_path(config["programLog"])
        for path in sorted(directory.glob("*.log"), key=lambda p: _date(p.name))[-5:]:
            with path.open("rb") as stream:
                stream.seek(max(0, path.stat().st_size - MAX_READ))
                rows.extend(
                    _rows(
                        stream.read(MAX_READ).decode("utf-8", errors="replace"),
                        "program",
                        path.name,
                        limit,
                    )
                )
    active = project or config.get("activeProject")
    if source in {"all", "project"} and active:
        with zipfile.ZipFile(application_path(active)) as archive:
            members = [
                item
                for item in archive.infolist()
                if item.filename.startswith("logs/") and item.filename.endswith((".log", ".jsonl"))
            ]
            for member in sorted(members, key=lambda item: _date(item.filename))[-5:]:
                if member.file_size > MAX_READ:
                    rows.append(
                        {
                            "source": "project",
                            "file": member.filename,
                            "level": None,
                            "message": "Registro omitido: supera 1 MiB; consultar archivo con herramienta especializada",
                        }
                    )
                    continue
                with archive.open(member) as stream:
                    rows.extend(
                        _rows(
                            stream.read(MAX_READ).decode("utf-8", errors="replace"),
                            "project",
                            member.filename,
                            limit,
                        )
                    )
    rows = [row for row in rows if row["level"] is None or row["level"] >= minimum]
    rows.sort(key=lambda row: (_date(row["file"]), row["message"][:8], row["source"]))
    return rows[-limit:]
