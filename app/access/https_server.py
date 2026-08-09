from __future__ import annotations

import json
import mimetypes
import ssl
import threading
import time
from collections import defaultdict, deque
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from app.core.resources import bundled_path

from .auth import AuthorizationService
from .network import source_allowed
from .remote import LanctlCommandAdapter, RemoteGuiApi

SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; connect-src 'self'; "
        "frame-ancestors 'none'; object-src 'none'; base-uri 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}
COOKIE_ATTRIBUTES = "Secure; HttpOnly; SameSite=Strict; Path=/"
MAX_BODY = 64 * 1024


class HttpsCapability:
    @staticmethod
    def context(certificate, private_key):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(certificate, private_key)
        return context

    @staticmethod
    def cors(origin, allowed_origin):
        return origin == allowed_origin and allowed_origin not in {"*", "null", ""}


class _RequestError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class _LoginLimiter:
    def __init__(self, attempts=10, window=60):
        self.attempts, self.window = attempts, window
        self.values = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, source):
        current = time.monotonic()
        with self.lock:
            values = self.values[source]
            while values and current - values[0] > self.window:
                values.popleft()
            if len(values) >= self.attempts:
                return False
            values.append(current)
            return True


class _BoundedHttpServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 32

    def __init__(self, *args, max_threads=32, **kwargs):
        self._capacity = threading.BoundedSemaphore(max_threads)
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address):
        if not self._capacity.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self._capacity.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self._capacity.release()


class HttpsAccessServer:
    def __init__(
        self,
        bind,
        port,
        cidr,
        certificate,
        private_key,
        auth,
        authorization=None,
        status_provider=dict,
        allowed_origin=None,
        static_directory=None,
        gui_api=None,
        command_adapter=None,
    ):
        self.bind, self.port, self.cidr, self.auth = bind, port, cidr, auth
        self.authorization = authorization or AuthorizationService(auth.store)
        self.status_provider = status_provider
        self.allowed_origin = allowed_origin or f"https://{bind}:{port}"
        self.static_directory = Path(static_directory or bundled_path("gui"))
        self.gui_api = RemoteGuiApi(self.authorization, gui_api)
        self.command_adapter = command_adapter or LanctlCommandAdapter(self.authorization)
        self.login_limiter = _LoginLimiter()
        parent = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "LANCTL-HTTPS"

            def setup(self):
                super().setup()
                self.connection.settimeout(15)

            def log_message(self, format, *args):
                return

            def _headers(self, content_type, length, cookie=None):
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(length))
                for key, value in SECURITY_HEADERS.items():
                    self.send_header(key, value)
                if cookie:
                    self.send_header("Set-Cookie", cookie)

            def _send(self, status, payload, cookie=None):
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self._headers("application/json; charset=utf-8", len(body), cookie)
                self.end_headers()
                self.wfile.write(body)

            def _send_file(self, path):
                try:
                    body = path.read_bytes()
                except OSError:
                    return self._send(404, {"error": "not found"})
                content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
                self.send_response(200)
                self._headers(content_type, len(body))
                self.end_headers()
                self.wfile.write(body)

            def _source(self):
                return source_allowed(self.client_address[0], parent.cidr)

            def _body(self):
                raw_length = self.headers.get("Content-Length")
                try:
                    length = int(raw_length) if raw_length is not None else 0
                except ValueError as error:
                    raise _RequestError(400, "Content-Length no valido") from error
                if length < 0:
                    raise _RequestError(400, "Content-Length no valido")
                if length > MAX_BODY:
                    raise _RequestError(413, "cuerpo de peticion demasiado grande")
                try:
                    value = json.loads(self.rfile.read(length) or b"{}")
                except (json.JSONDecodeError, UnicodeDecodeError) as error:
                    raise _RequestError(400, "JSON no valido") from error
                if not isinstance(value, dict):
                    raise _RequestError(400, "el cuerpo JSON debe ser un objeto")
                return value

            def _session(self, csrf=False):
                cookie = SimpleCookie(self.headers.get("Cookie", ""))
                session = cookie.get("lanctl_session")
                return parent.auth.validate_session(
                    session.value if session else "",
                    self.client_address[0],
                    self.headers.get("X-CSRF-Token") if csrf else None,
                )

            def _origin(self):
                origin = self.headers.get("Origin")
                if origin and not HttpsCapability.cors(origin, parent.allowed_origin):
                    raise _RequestError(403, "origin rejected")

            def _authorized(self, permission, csrf=False):
                user = self._session(csrf)
                parent.authorization.require(user, permission)
                return user

            def do_GET(self):
                if not self._source():
                    return self._send(403, {"error": "source outside managed LAN"})
                path = urlsplit(self.path).path
                if path in {"/", "/index.html", "/app.js", "/styles.css"}:
                    filename = "index.html" if path in {"/", "/index.html"} else path[1:]
                    return self._send_file(parent.static_directory / filename)
                try:
                    if path == "/api/status":
                        self._authorized("monitor.read")
                        return self._send(200, parent.status_provider())
                    if path == "/api/me":
                        user = self._session()
                        return self._send(
                            200,
                            {
                                "username": user.username,
                                "roles": user.roles,
                                "permissions": sorted(parent.authorization.permissions(user)),
                            },
                        )
                except PermissionError:
                    return self._send(401, {"error": "authentication required"})
                return self._send(404, {"error": "not found"})

            def do_POST(self):
                if not self._source():
                    return self._send(403, {"error": "source outside managed LAN"})
                path = urlsplit(self.path).path
                try:
                    self._origin()
                    if path == "/api/login":
                        if not parent.login_limiter.allow(self.client_address[0]):
                            return self._send(429, {"error": "demasiados intentos"})
                        body = self._body()
                        try:
                            user = parent.auth.authenticate_password(
                                str(body.get("username", "")),
                                str(body.get("password", "")),
                                self.client_address[0],
                            )
                        except (ValueError, PermissionError):
                            return self._send(401, {"error": "authentication rejected"})
                        session, csrf = parent.auth.create_session(
                            user, "web-password", self.client_address[0]
                        )
                        return self._send(
                            200,
                            {"csrfToken": csrf, "username": user.username, "roles": user.roles},
                            f"lanctl_session={session.sessionId}; {COOKIE_ATTRIBUTES}",
                        )
                    user = self._session(csrf=True)
                    body = self._body()
                    if path == "/api/logout":
                        cookie = SimpleCookie(self.headers.get("Cookie", ""))
                        session = cookie.get("lanctl_session")
                        if session:
                            parent.auth.revoke(session.value)
                        return self._send(
                            200,
                            {"ok": True},
                            f"lanctl_session=; Max-Age=0; {COOKIE_ATTRIBUTES}",
                        )
                    if path == "/api/rpc":
                        payload = parent.gui_api.call(
                            user, str(body.get("method", "")), body.get("args", [])
                        )
                        return self._send(200, payload)
                    if path == "/api/command":
                        code, output = parent.command_adapter.execute(
                            user, str(body.get("command", ""))
                        )
                        return self._send(200, {"ok": code == 0, "code": code, "output": output})
                    return self._send(404, {"error": "not found"})
                except _RequestError as error:
                    return self._send(error.status, {"error": str(error)})
                except PermissionError as error:
                    return self._send(403, {"error": str(error)})
                except ValueError as error:
                    return self._send(400, {"error": str(error)})
                except (OSError, RuntimeError):
                    return self._send(500, {"error": "internal operation failed"})

        server = _BoundedHttpServer((bind, port), Handler)
        server.socket = HttpsCapability.context(certificate, private_key).wrap_socket(
            server.socket, server_side=True
        )
        self.server = server

    def serve_forever(self):
        self.server.serve_forever(poll_interval=0.5)

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
