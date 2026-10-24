"""A session provider cannot inject extra cookies or HTTP response headers."""

import http.client
import json
import ssl
import threading
from types import SimpleNamespace
from unittest.mock import Mock

from lanctl.apps.access.auth import AuthenticationService, AuthorizationService
from lanctl.apps.access.https_server import HttpsAccessServer
from lanctl.apps.access.keys import generate_certificate
from lanctl.apps.access.store import AccessStore


def test_login_rejects_unsafe_session_ids_before_emitting_headers(tmp_path):
    certificate, key = generate_certificate(tmp_path / "tls.crt", tmp_path / "tls.key", "127.0.0.1")
    store = AccessStore(tmp_path / "users.json")
    auth = AuthenticationService(store)
    user = auth.add_user("viewer", ["viewer"], "another-strong-password")
    auth.authenticate_password = Mock(return_value=user)
    server = HttpsAccessServer(
        "127.0.0.1", 0, "127.0.0.0/8", certificate, key, auth, AuthorizationService(store)
    )
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    context = ssl.create_default_context(cafile=certificate)
    try:
        for identifier in (
            "session\r\nX-Injected: yes",
            "session\nX-Injected: yes",
            "session; Domain=attacker.invalid",
            "session\x00suffix",
            "",
            "x" * 129,
        ):
            auth.create_session = Mock(return_value=(SimpleNamespace(sessionId=identifier), "csrf"))
            connection = http.client.HTTPSConnection(
                "127.0.0.1", server.server.server_address[1], context=context, timeout=5
            )
            try:
                connection.request("POST", "/api/login", json.dumps({"username": "viewer"}))
                response = connection.getresponse()
                body = response.read().decode()
                assert response.status == 400
                assert response.getheader("X-Injected") is None
                assert response.getheader("Set-Cookie") is None
                assert body == json.dumps(
                    {"error": "identificador de sesión HTTP no válido"}, ensure_ascii=False
                )
            finally:
                connection.close()
    finally:
        server.stop()
        worker.join(2)
    assert not worker.is_alive()


def test_static_assets_ignore_untrusted_system_mime_registrations(tmp_path, monkeypatch):
    import mimetypes

    monkeypatch.setattr(
        mimetypes, "guess_type", lambda *a, **k: ("text/html\r\nX-Injected: yes", None)
    )
    expected = {
        "index.html": "text/html",
        "app.js": "application/javascript",
        "styles.css": "text/css",
    }
    for name in expected:
        (tmp_path / name).write_text("asset", encoding="utf-8")
    certificate, key = generate_certificate(tmp_path / "tls.crt", tmp_path / "tls.key", "127.0.0.1")
    auth = AuthenticationService(AccessStore(tmp_path / "users.json"))
    server = HttpsAccessServer(
        "127.0.0.1", 0, "127.0.0.0/8", certificate, key, auth, static_directory=tmp_path
    )
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    context = ssl.create_default_context(cafile=certificate)
    try:
        for name, media_type in expected.items():
            connection = http.client.HTTPSConnection(
                "127.0.0.1", server.server.server_address[1], context=context, timeout=5
            )
            try:
                connection.request("GET", "/" + name)
                response = connection.getresponse()
                assert response.status == 200
                assert response.read() == b"asset"
                assert response.getheader("Content-Type") == media_type
                assert response.getheader("X-Injected") is None
            finally:
                connection.close()
    finally:
        server.stop()
        worker.join(2)
    assert not worker.is_alive()
