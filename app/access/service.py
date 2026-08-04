from __future__ import annotations
import json,uuid
from datetime import datetime
from pathlib import Path
from app.core.history import HistoryEvent,HistoryService
from .auth import AuthenticationService,AuthorizationService
from .network import port_available,validate_endpoint
from .store import AccessStore

DEFAULT_CONFIG={"schemaVersion":1,"ssh":{"enabled":False,"bind":None,"cidr":None,"port":2222,"passwordAuthentication":False,"hostKey":None},"https":{"enabled":False,"bind":None,"cidr":None,"port":8443,"certificate":None,"privateKey":None},"firewall":{"managed":False}}
class AccessService:
    def __init__(self,config_path,user_store):
        self.config_path=Path(config_path);self.store=AccessStore(user_store);self.auth=AuthenticationService(self.store,self._audit);self.authorization=AuthorizationService(self.store)
    def config(self):
        if not self.config_path.exists():return json.loads(json.dumps(DEFAULT_CONFIG))
        value=json.loads(self.config_path.read_text(encoding="utf-8"));return {**DEFAULT_CONFIG,**value,"ssh":{**DEFAULT_CONFIG["ssh"],**value.get("ssh",{})},"https":{**DEFAULT_CONFIG["https"],**value.get("https",{})}}
    def save_config(self,value):
        self.config_path.parent.mkdir(parents=True,exist_ok=True);temporary=self.config_path.with_suffix(".tmp");temporary.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n",encoding="utf-8");temporary.replace(self.config_path)
    def initialize(self):
        if not self.config_path.exists():self.save_config(DEFAULT_CONFIG)
        if not self.store.path.exists():self.store.save(self.store.load())
        self._audit("access.config.initialized",None,"success");return self.status()
    def configure(self,protocol,*,bind,cidr,port,password_authentication=None,interfaces=None):
        if protocol not in {"ssh","https"}:raise ValueError("protocolo de acceso no válido")
        bind,cidr,port=validate_endpoint(bind,cidr,port,interfaces=interfaces)
        config=self.config();other="https" if protocol=="ssh" else "ssh"
        if config[other]["enabled"] and config[other]["bind"]==bind and config[other]["port"]==port:raise ValueError("el puerto colisiona con el otro servicio remoto")
        config[protocol].update({"bind":bind,"cidr":cidr,"port":port})
        if protocol=="ssh" and password_authentication is not None:config[protocol]["passwordAuthentication"]=bool(password_authentication)
        self.save_config(config);self._audit("access.config.changed",None,"success");return config[protocol]
    def enable(self,protocol):
        config=self.config();settings=config.get(protocol)
        if protocol not in {"ssh","https"} or not settings:raise ValueError("protocolo de acceso no válido")
        validate_endpoint(settings["bind"],settings["cidr"],settings["port"])
        if protocol=="https" and (not settings.get("certificate") or not settings.get("privateKey") or not Path(settings["certificate"]).is_file() or not Path(settings["privateKey"]).is_file()):raise RuntimeError("HTTPS requiere certificado TLS y clave privada válidos")
        if protocol=="ssh" and (not settings.get("hostKey") or not Path(settings["hostKey"]).is_file()):raise RuntimeError("SSH requiere una host key válida")
        if not port_available(settings["bind"],settings["port"]):raise RuntimeError("el puerto configurado no está disponible en la interfaz elegida")
        config[protocol]["enabled"]=True;self.save_config(config);self._audit(f"access.{protocol}.enabled",None,"success");return config[protocol]
    def disable(self,protocol):
        config=self.config();config[protocol]["enabled"]=False;self.save_config(config);self._audit(f"access.{protocol}.disabled",None,"success");return config[protocol]
    def status(self):
        config=self.config();result={"ssh":{k:v for k,v in config["ssh"].items() if k not in {"hostKey"}},"https":{k:v for k,v in config["https"].items() if k not in {"privateKey"}},"users":len(self.store.users()),"sessions":sum(not x.revokedAt for x in self.store.sessions())}
        from app.monitor.lifecycle import _process_alive
        for protocol in ("ssh","https"):
            pid=config[protocol].get("processId");running=False
            if pid:
                try:_process_alive(int(pid));running=True
                except OSError:pass
            result[protocol]["running"]=running
        return result
    def _audit(self,event_type,user,result,source_ip=""):
        try:HistoryService().write(HistoryEvent(event_type,"lanctl.access","local",result,event_type,details={"userId":user.userId if user else None,"sourceIp":source_ip}))
        except (ValueError,OSError):pass
