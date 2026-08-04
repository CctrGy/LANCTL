from __future__ import annotations

import csv
import io
import json
import re
import uuid
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from app.core.config import load_config
from app.projects.vlf import append_history_event


ID_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$", re.I)
RESULTS = {"success","sent","online","offline","skipped","blocked","timeout","cancelled","error","invalid"}
SENSITIVE = re.compile(r"password|passwd|credential|secret|token|private.?key|api.?key", re.I)


def redact(value: Any, key: str = "") -> Any:
    if SENSITIVE.search(str(key)): return "[OCULTO]"
    if isinstance(value, dict): return {str(k): redact(v, str(k)) for k,v in value.items()}
    if isinstance(value, (list,tuple)): return [redact(v) for v in value]
    if isinstance(value, (str,int,float,bool)) or value is None: return value
    return str(value)


@dataclass(frozen=True)
class DeviceSnapshot:
    id: str = ""; mac: str = ""; ip: str = ""; label: str = ""


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

    def __post_init__(self):
        if self.schemaVersion != 1 or not ID_PATTERN.fullmatch(self.type): raise ValueError("tipo de evento no válido")
        if not self.source or not self.actor: raise ValueError("source y actor son obligatorios")
        if self.result not in RESULTS: raise ValueError("resultado de historial no válido")
        parsed=datetime.fromisoformat(self.timestamp)
        if parsed.tzinfo is None: raise ValueError("timestamp debe incluir zona horaria")
        for value in (self.taskId,self.operationId):
            if value and not ID_PATTERN.fullmatch(value): raise ValueError("id de traza no válido")

    def to_dict(self) -> dict:
        value=asdict(self); value["changes"]=[redact(item) for item in self.changes]
        value["details"]=redact(self.details); value["error"]=redact(self.error)
        value["summary"]=str(redact(self.summary,"summary"))
        return {k:v for k,v in value.items() if v not in (None,{},[],())}

    @classmethod
    def from_dict(cls,value:dict) -> "HistoryEvent":
        allowed={field.name for field in __import__('dataclasses').fields(cls)}
        unknown=set(value)-allowed
        if unknown: raise ValueError("campos de historial desconocidos: "+", ".join(sorted(unknown)))
        data=dict(value); device=data.get("device")
        if isinstance(device,dict): data["device"]=DeviceSnapshot(**device)
        data["changes"]=tuple(data.get("changes",()))
        return cls(**data)


class HistoryWriter:
    def __init__(self, project: str|Path): self.project=Path(project)
    def write(self,event:HistoryEvent) -> HistoryEvent:
        append_history_event(self.project,event.to_dict(),now=datetime.fromisoformat(event.timestamp)); return event


class HistoryReader:
    def __init__(self, project: str|Path): self.project=Path(project)
    def read(self, strict: bool=False) -> list[HistoryEvent]:
        events=[]
        with zipfile.ZipFile(self.project) as archive:
            for name in sorted(archive.namelist()):
                if name.startswith("logs/events/") and name.endswith(".jsonl"):
                    for number,line in enumerate(archive.read(name).decode("utf-8",errors="replace").splitlines(),1):
                        if not line.strip(): continue
                        try: events.append(HistoryEvent.from_dict(json.loads(line)))
                        except Exception:
                            if strict: raise ValueError(f"evento corrupto en {name}:{number}")
                elif re.fullmatch(r"logs/\d{2}-\d{2}-\d{4}\.log",name):
                    events.extend(_legacy(name,archive.read(name).decode("utf-8",errors="replace")))
        return events


def _legacy(name:str,text:str)->list[HistoryEvent]:
    day=datetime.strptime(Path(name).stem,"%d-%m-%Y").date(); rows=[]
    for line in text.splitlines():
        match=re.match(r"(\d{2}:\d{2}:\d{2})\s+(.*)",line)
        if not match: continue
        stamp=datetime.combine(day,datetime.strptime(match.group(1),"%H:%M:%S").time()).astimezone()
        body=match.group(2); identity=""; kind="audit.legacy"; changes=[]
        change=re.match(r"CAMBIO\s+(\S+)\s+(.*)",body)
        if change:
            identity=change.group(1); kind="device.updated"
            for item in change.group(2).split("; "):
                field_name,sep,values=item.partition(":")
                before,arrow,after=values.partition("=>")
                if sep and arrow: changes.append({"field":field_name,"before":redact(before,field_name),"after":redact(after,field_name)})
        rows.append(HistoryEvent(kind,"legacy.vlf","local","success",body,timestamp=stamp.isoformat(),device=DeviceSnapshot(id=identity,label=identity) if identity else None,changes=tuple(changes),details={"format":"legacy"}))
    return rows


class HistoryService:
    def __init__(self, project: str|Path|None=None):
        self.project=Path(project or load_config().get("activeProject") or "")
        if not str(self.project) or not self.project.is_file(): raise ValueError("no hay un proyecto VLF activo")
    def write(self,event:HistoryEvent)->HistoryEvent:return HistoryWriter(self.project).write(event)
    def query(self,selector:str|None=None,*,date_from:date|None=None,date_to:date|None=None,types=(),source=None,result=None,errors=False,search=None,limit=100,reverse=False)->list[HistoryEvent]:
        rows=HistoryReader(self.project).read()
        if selector:
            wanted=selector.casefold(); identities={wanted}
            for event in rows:
                historical={str(change.get(side,"")).strip('"').casefold() for change in event.changes for side in ("before","after") if change.get("field","").casefold() in {"ip","alias","name","mac"}}
                current={x.casefold() for x in (event.device.id,event.device.mac,event.device.ip,event.device.label) if x} if event.device else set()
                if wanted in current|historical: identities.update(current|historical)
            def matches(event):
                if not event.device:return False
                current={x.casefold() for x in (event.device.id,event.device.mac,event.device.ip,event.device.label) if x}
                historical={str(change.get(side,"")).strip('"').casefold() for change in event.changes for side in ("before","after") if change.get("field","").casefold() in {"ip","alias","name","mac"}}
                return bool(identities.intersection(current|historical))
            rows=[e for e in rows if matches(e)]
        if date_from: rows=[e for e in rows if datetime.fromisoformat(e.timestamp).date()>=date_from]
        if date_to: rows=[e for e in rows if datetime.fromisoformat(e.timestamp).date()<=date_to]
        if types: rows=[e for e in rows if e.type in types]
        if source: rows=[e for e in rows if e.source.casefold()==source.casefold()]
        if result: rows=[e for e in rows if e.result==result]
        if errors: rows=[e for e in rows if e.error or e.result=="error"]
        if search: rows=[e for e in rows if search.casefold() in json.dumps(e.to_dict(),ensure_ascii=False).casefold()]
        rows.sort(key=lambda e:e.timestamp,reverse=reverse)
        return rows[:max(1,min(int(limit),10000))]
