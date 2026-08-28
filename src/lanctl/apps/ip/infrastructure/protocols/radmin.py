from __future__ import annotations

import os
import platform
import socket
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PORT = 4899
MODE_SWITCHES = {
    "control": None,
    "view": "/noinput",
    "file": "/file",
    "shutdown": "/shutdown",
    "chat": "/chat",
    "voice": "/voice",
    "message": "/message",
    "telnet": "/telnet",
}
MODES = tuple(MODE_SWITCHES)
COLOR_DEPTHS = (24, 16, 8, 4, 2, 1)


def validate_port(value: object) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError) as error:
        raise ValueError("el puerto Radmin debe ser un número") from error
    if not 1 <= port <= 65535:
        raise ValueError("el puerto Radmin debe estar entre 1 y 65535")
    return port


def validate_mode(value: object) -> str:
    mode = str(value or "control").strip().casefold()
    aliases = {"view-only": "view", "readonly": "view", "solo-visualizacion": "view"}
    mode = aliases.get(mode, mode)
    if mode not in MODES:
        raise ValueError("modo Radmin no válido: " + ", ".join(MODES))
    return mode


def _candidate_paths(environ: dict[str, str] | None = None) -> list[Path]:
    env = os.environ if environ is None else environ
    roots = [env.get("ProgramFiles"), env.get("ProgramFiles(x86)"), env.get("ProgramW6432")]
    candidates: list[Path] = []
    for root in roots:
        if root:
            candidates.append(Path(root) / "Radmin Viewer 3" / "Radmin.exe")
    return list(dict.fromkeys(candidates))


def find_viewer(
    configured_path: str | None = None,
    *,
    system: str | None = None,
    environ: dict[str, str] | None = None,
) -> Path | None:
    if (system or platform.system()) != "Windows":
        return None
    if configured_path:
        path = Path(configured_path).expanduser()
        if not path.is_file():
            raise ValueError(f"Radmin Viewer no existe en la ruta configurada: {path}")
        if path.suffix.casefold() != ".exe":
            raise ValueError("la ruta de Radmin Viewer debe apuntar a un archivo .exe")
        return path.resolve()
    for path in _candidate_paths(environ):
        if path.is_file():
            return path.resolve()
    return None


def build_arguments(
    executable: Path | str,
    host: str,
    port: int = DEFAULT_PORT,
    mode: str = "control",
    *,
    through: str | None = None,
    fullscreen: bool = False,
    color_depth: int | None = None,
    updates: int | None = None,
    phonebook_path: str | None = None,
    phonebook_id: int | None = None,
) -> list[str]:
    selected_port = validate_port(port)
    selected_mode = validate_mode(mode)
    arguments = [str(executable), f"/connect:{host}:{selected_port}"]
    mode_switch = MODE_SWITCHES[selected_mode]
    if mode_switch:
        arguments.append(mode_switch)
    if through:
        gateway, separator, gateway_port = through.rpartition(":")
        if not separator or not gateway:
            raise ValueError("through debe usar HOST:PUERTO")
        arguments.append(f"/through:{gateway}:{validate_port(gateway_port)}")
    if fullscreen:
        if selected_mode not in {"control", "view"}:
            raise ValueError("fullscreen sólo es válido en control o view")
        arguments.append("/fullscreen")
    if color_depth is not None:
        if color_depth not in COLOR_DEPTHS:
            raise ValueError("profundidad Radmin no válida")
        arguments.append(f"/{color_depth}bpp")
    if updates is not None:
        if not 1 <= int(updates) <= 120:
            raise ValueError("updates debe estar entre 1 y 120")
        arguments.append(f"/updates:{int(updates)}")
    if phonebook_path:
        resolved = Path(phonebook_path).expanduser().resolve()
        if resolved.suffix.casefold() != ".rpb":
            raise ValueError("el phonebook Radmin debe ser .rpb")
        arguments.append(f'/pbpath"{resolved}"')
    if phonebook_id is not None:
        if int(phonebook_id) < 0:
            raise ValueError("pbid no válido")
        arguments.append(f"/pbid:{int(phonebook_id)}")
    return arguments


def tcp_probe(
    host: str,
    port: int = DEFAULT_PORT,
    timeout: float = 0.8,
    connector: Callable[..., object] = socket.create_connection,
) -> bool:
    selected_port = validate_port(port)
    try:
        connection = connector((host, selected_port), timeout=timeout)
        close = getattr(connection, "close", None)
        if close:
            close()
        return True
    except OSError:
        return False


@dataclass(frozen=True)
class RadminLaunch:
    executable: Path
    arguments: list[str]
    process: object


def launch(
    host: str,
    *,
    port: int = DEFAULT_PORT,
    mode: str = "control",
    executable_path: str | None = None,
    popen: Callable[..., object] = subprocess.Popen,
    **options,
) -> RadminLaunch:
    if platform.system() != "Windows":
        raise RuntimeError("Radmin Viewer solo está disponible en Windows")
    executable = find_viewer(executable_path)
    if executable is None:
        raise RuntimeError(
            "Radmin Viewer no está instalado. Instálalo o configura su ruta con "
            "'lanctl settings --radmin-viewer RUTA'."
        )
    arguments = build_arguments(executable, host, port, mode, **options)
    return RadminLaunch(executable, arguments, popen(arguments))
