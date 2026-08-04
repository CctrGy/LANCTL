from __future__ import annotations
import os,subprocess
from pathlib import Path, PurePosixPath
from .base import PlatformAdapter,ServiceResult

class LinuxPlatform(PlatformAdapter):
    UNIT="""[Unit]\nDescription=LANCTL Monitor\nAfter=network-online.target\nWants=network-online.target\n\n[Service]\nType=simple\nExecStart={executable} -m app virtual monitor foreground --project {project}\nRestart=on-failure\nNoNewPrivileges=true\nPrivateTmp=true\n\n[Install]\nWantedBy=multi-user.target\n"""
    def unit_text(self,executable,project):
        if not str(executable).strip() or not str(project).strip():
            raise ValueError("el ejecutable y el proyecto son obligatorios para systemd")
        executable_path = PurePosixPath(str(executable))
        project_path = PurePosixPath(str(project))
        if not executable_path.is_absolute() or not project_path.is_absolute():
            raise ValueError("systemd requiere rutas Linux absolutas")
        return self.UNIT.format(
            executable=_systemd_quote(executable_path),
            project=_systemd_quote(project_path),
        )
    def service(self,action,**kwargs):
        if action=="status":
            completed=subprocess.run(["systemctl","is-active","lanctl-monitor.service"],capture_output=True,text=True,check=False)
            return ServiceResult(True,"active" if completed.returncode==0 else "inactive",completed.stdout.strip() or completed.stderr.strip())
        if action in {"start","stop","restart"}:
            completed=subprocess.run(["systemctl",action,"lanctl-monitor.service"],capture_output=True,text=True,check=False)
            return ServiceResult(True,"success" if completed.returncode==0 else "error",completed.stderr.strip() or completed.stdout.strip())
        if action in {"install","uninstall"}:
            if not kwargs.get("confirm"):return ServiceResult(True,"blocked","La instalación del servicio requiere confirmación explícita")
            if os.geteuid()!=0:return ServiceResult(True,"blocked","Se requieren privilegios de administrador")
            unit=Path("/etc/systemd/system/lanctl-monitor.service")
            if action=="install":unit.write_text(self.unit_text(kwargs["executable"],kwargs["project"]),encoding="utf-8")
            elif unit.exists():unit.unlink()
            subprocess.run(["systemctl","daemon-reload"],check=False)
            return ServiceResult(True,"success",f"Servicio {action} completado")
        return super().service(action)


def _systemd_quote(value: PurePosixPath) -> str:
    text = str(value)
    if any(ord(character) < 32 for character in text):
        raise ValueError("ruta no válida para systemd")
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
