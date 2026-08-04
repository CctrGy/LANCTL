from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ServiceResult:
    supported:bool;status:str;message:str;detail:dict|None=None
class PlatformAdapter:
    def service(self,action,**kwargs):return ServiceResult(False,"unsupported","La gestión de servicios no está soportada en esta plataforma")
    def identity(self):
        from app.monitor.identity import NetworkIdentity
        return NetworkIdentity()
