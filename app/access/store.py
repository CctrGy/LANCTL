from __future__ import annotations
import json
from pathlib import Path
from threading import RLock
from .models import AccessSession,RemoteUser

class AccessStore:
    def __init__(self,path):self.path=Path(path);self.lock=RLock()
    def load(self):
        if not self.path.exists():return {"schemaVersion":1,"users":[],"sessions":[],"pairings":[],"roles":{}}
        value=json.loads(self.path.read_text(encoding="utf-8"))
        if value.get("schemaVersion")!=1:raise ValueError("versión de almacén de acceso no compatible")
        return value
    def save(self,value):
        with self.lock:
            self.path.parent.mkdir(parents=True,exist_ok=True);temporary=self.path.with_suffix(self.path.suffix+".tmp")
            temporary.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8");temporary.replace(self.path)
    def users(self):return [RemoteUser(**x) for x in self.load()["users"]]
    def save_user(self,user):
        value=self.load();value["users"]=[x for x in value["users"] if x["userId"]!=user.userId]+[vars(user)];self.save(value)
    def delete_user(self,user_id):
        value=self.load();before=len(value["users"]);value["users"]=[x for x in value["users"] if x["userId"]!=user_id]
        if len(value["users"])==before:raise ValueError("usuario remoto no encontrado")
        value["sessions"]=[x for x in value["sessions"] if x["userId"]!=user_id];self.save(value)
    def sessions(self):return [AccessSession(**x) for x in self.load()["sessions"]]
    def save_session(self,session):
        value=self.load();value["sessions"]=[x for x in value["sessions"] if x["sessionId"]!=session.sessionId]+[vars(session)];self.save(value)
