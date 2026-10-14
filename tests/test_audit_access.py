import http.client
import json
import socket
import ssl
import subprocess
import threading
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from lanctl.apps.access.auth import AuthenticationService, AuthorizationService
from lanctl.apps.access.https_server import HttpsAccessServer
from lanctl.apps.access.remote import LanctlCommandAdapter, parse_remote_command
from lanctl.apps.access.store import AccessStore
from lanctl.apps.ip.infrastructure.protocols.ssh import (
    SshProfile,
    _key_fingerprint,
    run_show_command,
)


@pytest.mark.parametrize(
    "suffix", ["--output file", "--output=file", "--out=file", "-o file", "-ofile", "-o=file"]
)
def test_remote_commands_reject_output_paths(suffix):
    with pytest.raises(PermissionError):
        parse_remote_command("list " + suffix)


def test_viewer_cannot_scan_but_operator_can(tmp_path):
    auth = AuthenticationService(AccessStore(tmp_path / "users.dc"))
    viewer = auth.add_user("viewer", password="audit-test-password")
    operator = auth.add_user("operator", roles=["operator"], password="audit-test-password")
    runner = Mock(return_value=SimpleNamespace(returncode=0, stdout="ok", stderr=""))
    adapter = LanctlCommandAdapter(AuthorizationService(auth.store), runner=runner)
    with pytest.raises(PermissionError):
        adapter.execute(viewer, "list")
    runner.assert_not_called()
    assert adapter.execute(operator, "list") == (0, "ok")


@pytest.mark.parametrize("change", ["disable", "delete", "roles", "expire", "password", "keys"])
def test_existing_remote_user_is_revalidated_before_every_command(tmp_path, change):
    store = AccessStore(tmp_path / "users.dc")
    auth = AuthenticationService(store)
    user = auth.add_user("operator", ["operator"], "audit-test-password")
    authorization = AuthorizationService(store)
    runner = Mock(return_value=SimpleNamespace(returncode=0, stdout="ok", stderr=""))
    adapter = LanctlCommandAdapter(authorization, runner=runner)
    adapter.execute(user, "list")
    if change == "delete":
        store.delete_user(user.userId)
    else:
        fields = {
            "disable": {"enabled": False},
            "roles": {"roles": ["viewer"]},
            "expire": {
                "expiresAt": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
            },
            "password": {"passwordHash": "rotated"},
            "keys": {"sshKeys": ["changed"]},
        }
        store.save_user(replace(user, **fields[change]))
    runner.reset_mock()
    with pytest.raises(PermissionError):
        adapter.execute(user, "list")
    runner.assert_not_called()


def test_source_remote_launcher_is_executable_from_another_directory(tmp_path):
    command = LanctlCommandAdapter.command(["--help"])
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, timeout=20, check=False)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert b"LANIP" in result.stdout


@pytest.mark.parametrize(
    "name, sibling, expected",
    [
        ("LANIP", False, ["--help"]),
        ("LANCTL", False, ["lanip", "--help"]),
        ("LANACCESS", True, ["--help"]),
    ],
)
def test_frozen_launchers_select_the_ip_application(tmp_path, monkeypatch, name, sibling, expected):
    from lanctl.bootstrap import commands

    executable = tmp_path / f"{name}.exe"
    executable.touch()
    if sibling:
        (tmp_path / "LANIP.exe").touch()
    monkeypatch.setattr(commands.sys, "frozen", True, raising=False)
    monkeypatch.setattr(commands.sys, "executable", str(executable))
    command = commands.ip_command("--help")
    assert command[1:] == expected
    assert Path(command[0]).name == ("LANIP.exe" if sibling else executable.name)


@pytest.mark.parametrize("matching", [True, False])
def test_show_pins_the_authenticated_connection_before_credentials(matching):
    key = SimpleNamespace(asbytes=lambda: b"host-key")
    profile = SshProfile(
        driver="cisco_s300", fingerprint=_key_fingerprint(key) if matching else "SHA256:other"
    )
    steps = []

    class Connection:
        def _open(self):
            self.key_policy.missing_host_key(None, "192.0.2.1", key)
            steps.append("credentials")

        def send_command(self, command):
            steps.append(command)
            return "result"

        def disconnect(self):
            steps.append("close")

    def connector(**kwargs):
        assert kwargs["auto_connect"] is False
        assert kwargs["ssh_strict"] is True
        assert kwargs["system_host_keys"] is False
        assert kwargs["alt_host_keys"] is False
        return Connection()

    if matching:
        assert (
            run_show_command("192.0.2.1", "user", "secret", profile, "show system", connector)
            == "result"
        )
        assert steps == ["credentials", "show system", "close"]
    else:
        with pytest.raises(ValueError, match="huella SSH ha cambiado"):
            run_show_command("192.0.2.1", "user", "secret", profile, "show system", connector)
        assert steps == ["close"]


def test_slow_tls_peer_does_not_block_https_and_missing_csrf_is_rejected(tmp_path):
    from lanctl.apps.access.keys import generate_certificate

    certificate, key = generate_certificate(tmp_path / "tls.crt", tmp_path / "tls.key", "127.0.0.1")
    (tmp_path / "index.html").write_text("LANCTL", encoding="utf-8")
    auth = AuthenticationService(AccessStore(tmp_path / "users.dc"))
    user = auth.add_user("viewer", password="audit-test-password")
    session, csrf = auth.create_session(user, "web-password", "127.0.0.1")
    server = HttpsAccessServer(
        "127.0.0.1",
        0,
        "127.0.0.0/8",
        certificate,
        key,
        auth,
        static_directory=tmp_path,
        gui_api=Mock(),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server.server_address[1]
    stalled = socket.create_connection(("127.0.0.1", port), timeout=2)
    context = ssl.create_default_context(cafile=str(certificate))
    connection = http.client.HTTPSConnection("127.0.0.1", port, context=context, timeout=3)
    try:
        connection.request("GET", "/")
        response = connection.getresponse()
        assert (response.status, response.read()) == (200, b"LANCTL")
        for token in (None, "", "wrong"):
            headers = {"Cookie": f"lanctl_session={session.sessionId}"}
            if token is not None:
                headers["X-CSRF-Token"] = token
            connection.request("POST", "/api/logout", "{}", headers)
            response = connection.getresponse()
            response.read()
            assert response.status == 403
        connection.request(
            "POST",
            "/api/logout",
            "{}",
            {"Cookie": f"lanctl_session={session.sessionId}", "X-CSRF-Token": csrf},
        )
        response = connection.getresponse()
        assert response.status == 200
        assert json.loads(response.read())["ok"]
    finally:
        stalled.close()
        connection.close()
        server.stop()
        thread.join(2)
