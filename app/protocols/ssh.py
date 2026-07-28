from __future__ import annotations

from dataclasses import dataclass
import base64
import hashlib
import logging
import socket
import subprocess
import re
import shutil
import sys
import time
from typing import Callable


LEGACY_HOST_KEYS = {"ssh-rsa"}
LEGACY_KEX = {"diffie-hellman-group14-sha1"}
SSH_PROFILES = {
    "ssh_legacy_cisco_s300": {
        "profile": "ssh_legacy_cisco_s300",
        "port": 22,
        "driver": "cisco_s300",
        "hostKeyAlgorithms": ["ssh-rsa"],
        "kexAlgorithms": ["diffie-hellman-group14-sha1"],
        "legacyWarning": True,
    },
    "ssh_esp32_rack_monitor": {
        "profile": "ssh_esp32_rack_monitor",
        "port": 22,
        "driver": "generic",
        "hostKeyAlgorithms": [],
        "kexAlgorithms": [],
        "legacyWarning": False,
        "terminalAdapter": "esp32_rack_monitor",
        "role": "rack_manager_monitor",
    },
}


@dataclass(frozen=True)
class SshProfile:
    port: int = 22
    driver: str = "autodetect"
    host_key_algorithms: tuple[str, ...] = ()
    kex_algorithms: tuple[str, ...] = ()
    fingerprint: str = ""

    @classmethod
    def from_options(cls, options: dict) -> "SshProfile":
        profile = cls(
            port=int(options.get("port", 22)),
            driver=str(options.get("driver", "autodetect")),
            host_key_algorithms=tuple(options.get("hostKeyAlgorithms", [])),
            kex_algorithms=tuple(options.get("kexAlgorithms", [])),
            fingerprint=str(options.get("hostFingerprint", "")),
        )
        if not 1 <= profile.port <= 65535:
            raise ValueError("el puerto SSH debe estar entre 1 y 65535")
        unknown_keys = set(profile.host_key_algorithms) - LEGACY_HOST_KEYS
        unknown_kex = set(profile.kex_algorithms) - LEGACY_KEX
        if unknown_keys or unknown_kex:
            raise ValueError("el perfil solicita algoritmos SSH heredados no autorizados")
        return profile

    def openssh_arguments(self, host: str, username: str) -> list[str]:
        arguments = ["ssh", "-p", str(self.port)]
        for algorithm in self.host_key_algorithms:
            arguments.append(f"-oHostKeyAlgorithms=+{algorithm}")
        for algorithm in self.kex_algorithms:
            arguments.append(f"-oKexAlgorithms=+{algorithm}")
        arguments.append(f"{username}@{host}")
        return arguments


def tcp_available(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def arp_mac(host: str) -> str:
    """Devuelve la MAC observada en ARP sin alterar la identidad almacenada."""
    try:
        result = subprocess.run(
            ["arp", "-a", host], capture_output=True, text=True, timeout=3
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    match = re.search(r"(?:[0-9a-fA-F]{2}[-:]){5}[0-9a-fA-F]{2}", result.stdout)
    return match.group(0).replace("-", ":").upper() if match else ""


def host_fingerprint(host: str, profile: SshProfile, timeout: float = 5.0) -> tuple[str, bool]:
    """Obtiene la huella; prueba algoritmos modernos antes del fallback legacy."""
    try:
        import paramiko
    except ImportError as error:
        raise OSError("falta Paramiko para verificar la huella SSH") from error

    def negotiate(legacy: bool):
        connection = socket.create_connection((host, profile.port), timeout=timeout)
        transport = paramiko.Transport(connection)
        transport.banner_timeout = timeout
        security = transport.get_security_options()
        if legacy:
            security.key_types = tuple(dict.fromkeys((*profile.host_key_algorithms, *security.key_types)))
            security.kex = tuple(dict.fromkeys((*profile.kex_algorithms, *security.kex)))
        else:
            security.key_types = tuple(item for item in security.key_types if item not in LEGACY_HOST_KEYS)
            security.kex = tuple(item for item in security.kex if item not in LEGACY_KEX)
        try:
            transport.start_client(timeout=timeout)
            return transport.get_remote_server_key()
        finally:
            transport.close()

    legacy_used = False
    transport_logger = logging.getLogger("paramiko.transport")
    previous_level = transport_logger.level
    try:
        # El fallo moderno es una rama esperada para perfiles legacy; Paramiko
        # lo registra desde su hilo interno aunque después hagamos fallback.
        transport_logger.setLevel(logging.CRITICAL)
        try:
            key = negotiate(False)
        except (paramiko.SSHException, EOFError):
            if not profile.host_key_algorithms and not profile.kex_algorithms:
                raise
            key = negotiate(True)
            legacy_used = True
    finally:
        transport_logger.setLevel(previous_level)
    digest = base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip("=")
    return f"SHA256:{digest}", legacy_used


def verify_pinned_host(host: str, profile: SshProfile) -> bool:
    if not profile.fingerprint:
        raise ValueError(
            "la huella SSH no est\u00e1 fijada; usa primero 'run ssh ELEMENTO fingerprint' "
            "y despu\u00e9s 'run ssh ELEMENTO trust HUELLA'"
        )
    current, legacy_used = host_fingerprint(host, profile)
    if current != profile.fingerprint:
        raise ValueError(
            f"ALERTA: la huella SSH ha cambiado (esperada {profile.fingerprint}, actual {current})"
        )
    return legacy_used


def run_show_command(
    host: str,
    username: str,
    password: str,
    profile: SshProfile,
    command: str,
    connector: Callable | None = None,
) -> str:
    """Ejecuta exclusivamente consultas `show` mediante Netmiko."""
    if not command.strip().casefold().startswith("show "):
        raise ValueError("solo se permiten comandos Cisco de consulta que empiecen por 'show '")
    if connector is None:
        try:
            from netmiko import ConnectHandler
        except ImportError as error:
            raise OSError("falta Netmiko; instala las dependencias del proyecto") from error
        except AttributeError as error:
            if "serial" in str(error).casefold():
                raise OSError(
                    "Netmiko est\u00e1 cargando el paquete 'serial' incorrecto; "
                    "desinstala 'serial' y reinstala 'pyserial'"
                ) from error
            raise
        connector = ConnectHandler

    parameters = {
        "device_type": profile.driver,
        "host": host,
        "port": profile.port,
        "username": username,
        "password": password,
        # Paramiko conserva estos algoritmos en su catálogo. No se modifica
        # ninguna configuración global de OpenSSH ni del sistema.
        "disabled_algorithms": {},
    }
    connection = connector(**parameters)
    try:
        return str(connection.send_command(command))
    finally:
        connection.disconnect()


def open_interactive(host: str, username: str, profile: SshProfile) -> int:
    """Abre OpenSSH con excepciones pasadas solo a este proceso/host."""
    return subprocess.call(profile.openssh_arguments(host, username))


def open_colored_interactive(
    host: str,
    username: str,
    password: str,
    profile: SshProfile,
    *,
    theme: str = "generic",
    input_fn: Callable[[str], str] = input,
) -> int:
    """Terminal SSH lineal cuyo flujo de salida puede decorar LANCTL."""
    if not profile.fingerprint:
        raise ValueError(
            "la huella SSH no está fijada; usa primero ssh ELEMENTO fingerprint/trust"
        )
    try:
        import paramiko
    except ImportError as error:
        raise OSError("falta Paramiko para abrir la terminal SSH gestionada") from error

    connection = socket.create_connection((host, profile.port), timeout=8.0)
    transport = paramiko.Transport(connection)
    security = transport.get_security_options()
    if profile.host_key_algorithms:
        security.key_types = tuple(dict.fromkeys(
            (*profile.host_key_algorithms, *security.key_types)
        ))
    if profile.kex_algorithms:
        security.kex = tuple(dict.fromkeys((*profile.kex_algorithms, *security.kex)))
    try:
        transport.start_client(timeout=8.0)
        presented = _key_fingerprint(transport.get_remote_server_key())
        if presented != profile.fingerprint:
            raise ValueError(
                f"ALERTA: la huella SSH ha cambiado "
                f"(esperada {profile.fingerprint}, actual {presented})"
            )
        transport.auth_password(username, password)
        channel = transport.open_session(timeout=8.0)
        size = shutil.get_terminal_size(fallback=(120, 30))
        channel.get_pty(term="xterm-256color", width=size.columns, height=size.lines)
        channel.invoke_shell()
        _write_colored(_receive_until_idle(channel, idle=0.8), theme)
        while not channel.closed:
            try:
                command = input_fn("")
            except (EOFError, KeyboardInterrupt):
                channel.send("exit\n")
                print()
                break
            channel.send(command + "\n")
            _write_colored(_receive_until_idle(channel), theme)
        return channel.recv_exit_status() if channel.exit_status_ready() else 0
    finally:
        transport.close()


def _key_fingerprint(key) -> str:
    digest = base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip("=")
    return f"SHA256:{digest}"


def _receive_until_idle(channel, idle: float = 0.35) -> str:
    chunks: list[bytes] = []
    deadline = time.monotonic() + idle
    while not channel.closed:
        if channel.recv_ready():
            chunks.append(channel.recv(65535))
            deadline = time.monotonic() + idle
            continue
        if time.monotonic() >= deadline:
            break
        time.sleep(0.015)
    return b"".join(chunks).decode("utf-8", errors="replace")


def _write_colored(value: str, theme: str) -> None:
    if not value:
        return
    from app.terminals.ssh_color import colorize_ssh_output
    sys.stdout.write(colorize_ssh_output(value, theme))
    sys.stdout.flush()
