from __future__ import annotations

import argparse
import os
import platform
import subprocess

from app.commands.terminal import run_terminal
from app.core.config import load_config
from app.core.database import DeviceDatabase
from app.core.logger import write_log
from app.models import normalize_protocol
from app.protocols.radmin import (
    COLOR_DEPTHS,
    validate_mode,
)
from app.protocols.radmin import (
    DEFAULT_PORT as RADMIN_PORT,
)
from app.protocols.radmin import (
    MODES as RADMIN_MODES,
)
from app.protocols.radmin import (
    launch as launch_radmin,
)

OPEN_PROTOCOLS = (
    "auto",
    "ssh",
    "tr-064",
    "telnet",
    "http",
    "https",
    "ftp",
    "rdp",
    "rtsp",
    "smb",
    "radmin",
)
DEFAULT_PORTS = {
    "telnet": 23,
    "http": 80,
    "https": 443,
    "ftp": 21,
    "rdp": 3389,
    "rtsp": 554,
}


def connection_target(ip: str, protocol: str, port: int | None = None, path: str = "") -> str:
    protocol = normalize_protocol(protocol)
    suffix = path.lstrip("/")
    if protocol == "smb":
        return rf"\\{ip}" + (rf"\{suffix}" if suffix else "")
    if protocol == "rdp":
        return f"{ip}:{port or DEFAULT_PORTS['rdp']}"
    selected_port = port or DEFAULT_PORTS.get(protocol)
    authority = f"{ip}:{selected_port}" if selected_port else ip
    return f"{protocol}://{authority}/" + suffix


def register_open_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "open",
        aliases=["connect"],
        help="Abre un elemento con un cliente acorde al protocolo.",
    )
    command.add_argument("selector", help="IP, MAC o alias del elemento.")
    command.add_argument(
        "protocol",
        nargs="?",
        default="auto",
        choices=OPEN_PROTOCOLS,
        help="Protocolo o detección automática.",
    )
    command.add_argument("--port", type=int, help="Puerto alternativo.")
    command.add_argument("--path", default="", help="Ruta HTTP/FTP/RTSP o recurso SMB.")
    command.add_argument("--mode", choices=RADMIN_MODES, help="Modo de conexión Radmin.")
    command.add_argument("--through", help="Servidor Radmin intermedio HOST:PUERTO.")
    command.add_argument(
        "--fullscreen", action="store_true", help="Abre control o vista a pantalla completa."
    )
    command.add_argument(
        "--color-depth",
        type=int,
        choices=COLOR_DEPTHS,
        help="Profundidad de color de Radmin (1, 2, 4, 8, 16 o 24 bits).",
    )
    command.add_argument(
        "--updates",
        type=int,
        help="Máximo de actualizaciones de pantalla por segundo (1-120).",
    )
    command.add_argument("--phonebook", help="Ruta de phonebook Radmin .rpb.")
    command.add_argument(
        "--phonebook-id",
        type=int,
        help="Identificador de entrada dentro del phonebook de Radmin.",
    )
    command.add_argument("--dry-run", action="store_true", help="Muestra el destino sin abrirlo.")
    command.add_argument(
        "--database", default=config["database"], help="Archivo JSON de elementos."
    )
    command.add_argument(
        "--store", default=config["credentials"], help="Almacén cifrado de credenciales."
    )
    command.set_defaults(handler=run_open)


def _automatic_protocol(device) -> str:
    if len(device.protocols) == 1:
        return device.protocols[0]
    raise ValueError(
        "no se puede elegir protocolo automáticamente; disponibles: "
        + (", ".join(device.protocols) or "ninguno")
    )


def run_open(args: argparse.Namespace) -> int:
    device = DeviceDatabase(args.database).resolve(args.selector)
    if device.ip in ("", "-"):
        raise ValueError(f"{args.selector} no tiene una IP registrada")
    protocol = _automatic_protocol(device) if args.protocol == "auto" else args.protocol
    if args.port is not None and not 1 <= args.port <= 65535:
        raise ValueError("el puerto debe estar entre 1 y 65535")
    if protocol in ("ssh", "tr-064"):
        if args.dry_run:
            print(f"{protocol}://{device.ip}:{args.port or (22 if protocol == 'ssh' else 49000)}")
            return 0
        return run_terminal(
            argparse.Namespace(
                selector=args.selector, protocol=protocol, database=args.database, store=args.store
            )
        )
    if protocol == "radmin":
        options = device.protocol_options.get("radmin", {})
        port = args.port if args.port is not None else options.get("port", RADMIN_PORT)
        mode = validate_mode(getattr(args, "mode", None) or options.get("mode", "control"))
        configured_executable = options.get("executable") or load_config().get("radminViewer")
        launch_options = {
            "through": getattr(args, "through", None) or options.get("through"),
            "fullscreen": bool(
                getattr(args, "fullscreen", False) or options.get("fullscreen", False)
            ),
            "color_depth": getattr(args, "color_depth", None) or options.get("colorDepth"),
            "updates": getattr(args, "updates", None) or options.get("updates"),
            "phonebook_path": getattr(args, "phonebook", None) or options.get("phonebookPath"),
            "phonebook_id": getattr(args, "phonebook_id", None)
            if getattr(args, "phonebook_id", None) is not None
            else options.get("phonebookId"),
        }
        if args.dry_run:
            selected = "&".join(
                f"{key}={value}"
                for key, value in launch_options.items()
                if value not in (None, False, "")
            )
            print(f"radmin://{device.ip}:{port}?mode={mode}" + (f"&{selected}" if selected else ""))
            return 0
        try:
            launch_radmin(
                device.ip,
                port=port,
                mode=mode,
                executable_path=configured_executable,
                **launch_options,
            )
        except Exception as error:
            write_log(
                f"OPEN protocol=radmin target={device.ip}:{port} mode={mode} result=error detail={error}"
            )
            raise
        write_log(f"OPEN protocol=radmin target={device.ip}:{port} mode={mode} result=started")
        return 0

    target = connection_target(device.ip, protocol, args.port, args.path)
    if args.dry_run:
        print(target)
        return 0
    if protocol == "rdp":
        subprocess.Popen(["mstsc.exe", f"/v:{target}"])
    elif protocol == "telnet":
        subprocess.Popen(["telnet", device.ip, str(args.port or 23)])
    elif platform.system() == "Windows":
        os.startfile(target)  # type: ignore[attr-defined]
    else:
        subprocess.Popen(["xdg-open", target])
    return 0
