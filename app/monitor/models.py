from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

PRESENCE={"unknown","online","offline","waking"}; HEALTH={"healthy","warning","critical","maintenance"}
SESSION_STATES={"pending","active","stopping","completed","expired","cancelled","error"}
AUTHORITIES={"observe","operate","administer"}; MODES={"permanent","temporary","diagnostic","once"}

def now_iso(): return datetime.now().astimezone().isoformat()

@dataclass(frozen=True)
class MonitorProfile:
    profile_id:str="default"; presence_interval:float=60; critical_interval:float=15
    discovery_interval:float=300; services_interval:float=1800; deep_interval:float=86400
    timeout:float=.8; workers:int=8; jitter:float=.1; failure_threshold:int=3; recovery_threshold:int=2

@dataclass
class MonitorSession:
    sessionId:str; runId:str; managerId:str; projectId:str; network:str; interface:str; localIp:str
    mode:str; authority:str; startedAt:str; expiresAt:str|None=None; status:str="pending"; error:dict|None=None
    def __post_init__(self):
        if self.mode not in MODES or self.authority not in AUTHORITIES or self.status not in SESSION_STATES: raise ValueError("sesión monitor no válida")

@dataclass(frozen=True)
class CheckSpec:
    check_id:str; owner:str; handler:Any; minimum_interval:float=10; timeout:float=1; critical:bool=False

@dataclass(frozen=True)
class CheckResult:
    checkId:str; target:str; success:bool; timestamp:str=field(default_factory=now_iso); latencyMs:float|None=None
    evidence:tuple[str,...]=(); metrics:dict=field(default_factory=dict); error:dict|None=None

@dataclass
class DeviceState:
    deviceId:str; presence:str="unknown"; health:str="healthy"; consecutiveFailures:int=0; consecutiveRecoveries:int=0; updatedAt:str=field(default_factory=now_iso)

@dataclass
class Incident:
    incidentId:str; deviceId:str; severity:str; cause:str; origin:str; openedAt:str
    status:str="open"; resolvedAt:str|None=None; correlationId:str|None=None; sessionId:str|None=None

class ConfigProvider(Protocol):
    def profile(self, profile_id:str="default")->MonitorProfile: ...
class AssignmentProvider(Protocol):
    def targets(self, session:MonitorSession)->list[Any]: ...
class MetricsStore(Protocol):
    def write(self,result:CheckResult,session_id:str)->None: ...
class SessionRepository(Protocol):
    def save(self,session:MonitorSession)->None: ...
    def active(self)->MonitorSession|None: ...
class IncidentRepository(Protocol):
    def list(self)->list[Incident]: ...
    def save(self,incident:Incident)->None: ...
class ReportBuilder(Protocol):
    def completed(self,session:MonitorSession)->None: ...
