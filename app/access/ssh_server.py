from __future__ import annotations

import socket
import threading
from contextlib import suppress

try:
    import paramiko

    _Base = paramiko.ServerInterface
except ImportError:
    paramiko = None

    class _Base:
        pass


from .network import source_allowed
from .remote import LanctlCommandAdapter


class RestrictedSshServer(_Base):
    """Negocia solo terminal, exec o subsystem LANCTL; nunca una shell del SO."""

    def __init__(self, auth, authorization, password_enabled=False, source_ip=""):
        super().__init__()
        self.auth = auth
        self.authorization = authorization
        self.password_enabled = password_enabled
        self.source_ip = source_ip
        self.user = None
        self.mode = None
        self.command = None
        self.requested = threading.Event()

    def check_auth_publickey(self, username, key):
        self.user = None
        if not self.auth or not paramiko:
            return 2
        try:
            value = f"{key.get_name()} {key.get_base64()}"
            self.user = self.auth.authenticate_ssh_key(username, value, self.source_ip)
            return paramiko.AUTH_SUCCESSFUL
        except (ValueError, PermissionError):
            return paramiko.AUTH_FAILED

    def check_auth_password(self, username, password):
        self.user = None
        if not self.password_enabled or not self.auth or not paramiko:
            return 2
        try:
            self.user = self.auth.authenticate_password(username, password, self.source_ip)
            return paramiko.AUTH_SUCCESSFUL
        except (ValueError, PermissionError):
            return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "publickey,password" if self.password_enabled else "publickey"

    def check_channel_request(self, kind, _chanid):
        if paramiko and kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED if paramiko else False

    def check_channel_pty_request(
        self, channel, term, width, height, _pixelwidth, _pixelheight, _modes
    ):
        return bool(self.user)

    def check_channel_window_change_request(self, *args):
        return True

    def check_channel_shell_request(self, channel):
        self.mode = "shell"
        self.requested.set()
        return bool(self.user)

    def check_channel_exec_request(self, channel, command):
        try:
            decoded = command.decode("utf-8") if isinstance(command, bytes) else str(command)
        except UnicodeDecodeError:
            return False
        self.mode, self.command = "exec", decoded
        self.requested.set()
        return bool(self.user)

    def check_channel_subsystem_request(self, channel, name):
        if name != "lanctl":
            return False
        self.mode = "shell"
        self.requested.set()
        return bool(self.user)

    def check_channel_x11_request(self, *args):
        return False

    def check_channel_forward_agent_request(self, *args):
        return False

    def check_port_forward_request(self, *args):
        return False

    def cancel_port_forward_request(self, *args):
        return False

    @staticmethod
    def capability():
        return {
            "available": bool(paramiko),
            "backend": "paramiko" if paramiko else None,
            "reason": None if paramiko else "instala paramiko",
        }


class SshAccessServer:
    def __init__(
        self,
        bind,
        port,
        cidr,
        host_key,
        auth,
        authorization,
        password_enabled=False,
        command_adapter=None,
    ):
        self.bind, self.port, self.cidr = bind, port, cidr
        self.host_key, self.auth = host_key, auth
        self.authorization = authorization
        self.password_enabled = password_enabled
        self.adapter = command_adapter or LanctlCommandAdapter(authorization)
        self.closed = threading.Event()
        self.socket = None
        self.capacity = threading.BoundedSemaphore(32)

    def serve_forever(self):
        listener, key = self.prepare()
        try:
            while not self.closed.is_set():
                try:
                    client, address = listener.accept()
                except TimeoutError:
                    continue
                except OSError:
                    if self.closed.is_set():
                        break
                    raise
                if not source_allowed(address[0], self.cidr):
                    client.close()
                    continue
                if not self.capacity.acquire(blocking=False):
                    client.close()
                    continue
                threading.Thread(
                    target=self._bounded_client,
                    args=(client, address[0], key),
                    daemon=True,
                ).start()
        finally:
            listener.close()

    def prepare(self):
        """Abre el listener sincronicamente para detectar fallos de inicio."""
        if not paramiko:
            raise RuntimeError("capability SSH no disponible: falta paramiko")
        if self.socket is not None:
            return self.socket, self._host_key
        listener = socket.socket()
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            listener.bind((self.bind, self.port))
            listener.listen(16)
            listener.settimeout(1)
            key = paramiko.Ed25519Key.from_private_key_file(self.host_key)
        except Exception:
            listener.close()
            raise
        self.socket, self._host_key = listener, key
        return listener, key

    def _bounded_client(self, client, source, key):
        try:
            self._client(client, source, key)
        finally:
            self.capacity.release()

    def _client(self, client, source, key):
        transport = paramiko.Transport(
            client,
            disabled_algorithms={
                "kex": ["diffie-hellman-group1-sha1", "diffie-hellman-group14-sha1"],
                "keys": ["ssh-rsa", "ssh-dss"],
                "pubkeys": ["ssh-rsa", "ssh-dss"],
            },
        )
        transport.banner_timeout = 15
        transport.auth_timeout = 30
        transport.add_server_key(key)
        server = RestrictedSshServer(self.auth, self.authorization, self.password_enabled, source)
        try:
            transport.start_server(server=server)
            channel = transport.accept(15)
            if not channel or not server.user or not server.requested.wait(5):
                return
            channel.settimeout(120)
            if server.mode == "exec":
                code, output = self._execute(server.user, server.command or "")
                channel.sendall((output + "\r\n").encode("utf-8"))
                channel.send_exit_status(code)
                return
            self._interactive(channel, server.user)
        except (EOFError, OSError):
            pass
        finally:
            transport.close()

    def _execute(self, user, command):
        try:
            return self.adapter.execute(user, command)
        except (ValueError, PermissionError) as error:
            return 2, f"Error: {error}"

    def _interactive(self, channel, user):
        permissions = ", ".join(sorted(self.authorization.permissions(user)))
        banner = (
            "LANCTL restricted console\r\n"
            "Escribe un comando LANCTL, 'help', 'whoami' o 'exit'.\r\n"
            f"Usuario: {user.username} | Permisos: {permissions}\r\n"
        )
        channel.sendall(banner.encode("utf-8"))
        buffer = bytearray()
        while not self.closed.is_set() and not channel.closed:
            channel.sendall(f"{user.username}@lanctl> ".encode())
            while b"\n" not in buffer:
                try:
                    chunk = channel.recv(1024)
                except TimeoutError:
                    channel.sendall(b"\r\nSesion cerrada por inactividad.\r\n")
                    return
                if not chunk:
                    return
                buffer.extend(chunk)
                if len(buffer) > 8192:
                    channel.sendall(b"\r\nError: linea demasiado larga.\r\n")
                    return
            raw, _, remainder = buffer.partition(b"\n")
            buffer = bytearray(remainder)
            line = raw.rstrip(b"\r").decode("utf-8", "replace").strip()
            if not line:
                continue
            if line.casefold() in {"exit", "quit", "logout"}:
                channel.sendall(b"Hasta pronto.\r\n")
                return
            if line.casefold() == "whoami":
                channel.sendall((user.username + "\r\n").encode("utf-8"))
                continue
            if line.casefold() in {"help", "?"}:
                channel.sendall(
                    b"Comandos remotos: list, search, ping, history, smb, monitor, "
                    b"scan, wol, project y comandos de configuracion segun el rol.\r\n"
                    b"Control raiz: root status | root refresh | root forced-view VIEW.\r\n"
                )
                continue
            code, output = self._execute(user, line)
            rendered = output.replace("\r\n", "\n").replace("\n", "\r\n")
            channel.sendall((rendered + f"\r\n[codigo {code}]\r\n").encode("utf-8"))

    def stop(self):
        self.closed.set()
        if self.socket:
            with suppress(OSError):
                self.socket.close()
