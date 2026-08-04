from __future__ import annotations
from dataclasses import replace
from .models import *
import json
from pathlib import Path
from .configuration import ConfigProvider as DefaultConfigProvider

class InMemoryMetricsStore:
    def __init__(self):self.rows=[]
    def write(self,result,session_id):self.rows.append((session_id,result))
class InMemorySessionRepository:
    def __init__(self):self.rows={}
    def save(self,session):self.rows[session.sessionId]=session
    def active(self):return next((x for x in reversed(list(self.rows.values())) if x.status in {"pending","active","stopping"}),None)
class JsonSessionRepository(InMemorySessionRepository):
    def __init__(self,path):
        super().__init__();self.path=Path(path)
        if self.path.exists():
            for value in json.loads(self.path.read_text(encoding="utf-8")):self.rows[value["sessionId"]]=MonitorSession(**value)
    def save(self,session):
        super().save(session);self.path.parent.mkdir(parents=True,exist_ok=True);temporary=self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps([vars(x) for x in self.rows.values()],indent=2,ensure_ascii=False)+"\n",encoding="utf-8");temporary.replace(self.path)
class InMemoryIncidentRepository:
    def __init__(self):self.rows={}
    def list(self):return list(self.rows.values())
    def save(self,incident):self.rows[incident.incidentId]=incident
class JsonIncidentRepository(InMemoryIncidentRepository):
    def __init__(self,path):
        super().__init__();self.path=Path(path)
        if self.path.exists():
            for value in json.loads(self.path.read_text(encoding="utf-8")):self.rows[value["incidentId"]]=Incident(**value)
    def save(self,incident):
        super().save(incident);self.path.parent.mkdir(parents=True,exist_ok=True);temporary=self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps([vars(x) for x in self.rows.values()],indent=2,ensure_ascii=False)+"\n",encoding="utf-8");temporary.replace(self.path)
class NullReportBuilder:
    def completed(self,session):pass
