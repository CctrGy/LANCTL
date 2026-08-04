from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

PORTABLE_MARKER = "LANCTL.portable"
PORTABLE_MARKER_CONTENT = "LANCTL-PORTABLE-V1"

_STRUCTURED_PATHS = {
    ".config": Path("config/config.json"),
    "devices.json": Path("database/devices.json"),
    "groups.json": Path("database/groups.json"),
    "log": Path("logs"),
    "plugins": Path("plugins"),
    "plugins.registry": Path("plugins/registry.json"),
    "languajes": Path("config/languages"),
    "icons": Path("config/icons"),
    "wol-sequences.json": Path("automation/wol-sequences.json"),
    "monitor-sessions.json": Path("monitoring/sessions.json"),
    "monitor-incidents.json": Path("monitoring/incidents.json"),
    "monitor.lock": Path("monitoring/monitor.lock"),
    "monitor.db": Path("monitoring/monitor.db"),
    "monitor-profiles.json": Path("monitoring/profiles.json"),
    "monitor-assignments.json": Path("monitoring/assignments.json"),
    "plugin-storage": Path("plugins/storage"),
    "cisco_profiles.json": Path("config/cisco_profiles.json"),
}
_STRUCTURED_PREFIXES={
    "log":Path("logs"),"plugins":Path("plugins"),"plugin-storage":Path("plugins/storage"),
    "languajes":Path("config/languages"),"icons":Path("config/icons"),
}


def application_directory() -> Path:
    """Directorio inmutable de la aplicación, independiente del cwd."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def is_portable_install() -> bool:
    if not getattr(sys, "frozen", False):
        return False
    marker = application_directory() / PORTABLE_MARKER
    try:
        return marker.is_file() and marker.read_text(encoding="ascii").strip() == PORTABLE_MARKER_CONTENT
    except OSError:
        return False


def data_root() -> Path:
    """Resuelve la raíz mutable sin crearla ni tocar el sistema de archivos."""
    override = os.environ.get("LANCTL_DATA_DIR")
    if override:
        candidate = Path(override).expanduser()
        if not candidate.is_absolute():
            raise ValueError("LANCTL_DATA_DIR debe ser una ruta absoluta")
        return candidate.resolve()
    if is_portable_install():
        return (application_directory() / "data" / "lanctl").resolve()
    if getattr(sys, "frozen", False):
        if platform.system() == "Windows":
            return (Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData")) / "LANCTL").resolve()
        return Path("/var/lib/lanctl")
    return (application_directory() / "data" / "lc").resolve()


def secret_root() -> Path:
    """Datos sensibles con ámbito de usuario/servicio y ACL del sistema."""
    override=os.environ.get("LANCTL_SECRET_DIR")
    if override:
        candidate=Path(override).expanduser()
        if not candidate.is_absolute():raise ValueError("LANCTL_SECRET_DIR debe ser una ruta absoluta")
        return candidate.resolve()
    if os.environ.get("LANCTL_DATA_DIR"):
        return (data_root()/"access").resolve()
    if is_portable_install():return (data_root()/"access").resolve()
    if getattr(sys,"frozen",False) and platform.system()=="Windows":
        local=Path(os.environ.get("LOCALAPPDATA",application_directory()))
        return (local/"LANCTL"/"access").resolve()
    return (data_root()/"access").resolve()


def application_path(value: str | Path) -> Path:
    """Resuelve rutas de datos heredadas contra el contrato mutable central."""
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    normalized = path.as_posix()
    if normalized == "data/lc" or normalized.startswith("data/lc/"):
        suffix = Path(*path.parts[2:]) if len(path.parts) > 2 else Path()
        if suffix.as_posix()==".credentials":
            return (secret_root()/"device-credentials.dat").resolve()
        if suffix.parts and suffix.parts[0] == "access":
            return (secret_root()/Path(*suffix.parts[1:])).resolve()
        else:
            translated = _STRUCTURED_PATHS.get(suffix.as_posix())
            if translated is None and suffix.parts and suffix.parts[0] in _STRUCTURED_PREFIXES:
                translated=_STRUCTURED_PREFIXES[suffix.parts[0]]/Path(*suffix.parts[1:])
            if translated is None:translated=suffix
        return (data_root() / translated).resolve()
    return (application_directory() / path).resolve()
