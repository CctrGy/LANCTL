"""Shared native GUI pages under a persistent, authenticated LAN shell."""

import http.client
import json
import ssl
import threading
from pathlib import Path
from threading import RLock

import pytest
from test_launcher_gui import workspace as workspace

from lanctl.apps.access.auth import AuthenticationService, AuthorizationService
from lanctl.apps.access.https_server import HttpsAccessServer
from lanctl.apps.access.keys import generate_certificate
from lanctl.apps.access.store import AccessStore
from lanctl.apps.access.web_suite import PAGES, WebSuiteGateway
from lanctl.core import config
from lanctl.core.project_context import project_identity


@pytest.fixture
def web(workspace, tmp_path):
    cfg = config.load_config()
    cfg["projectsDirectory"] = str(tmp_path / "projects")
    config.save_config(cfg)
    store = AccessStore(tmp_path / "web-users.json")
    auth = AuthenticationService(store)
    admin = auth.add_user("administrator", ["administrator"], "example-password-1234")
    viewer = auth.add_user("viewer", ["viewer"], "example-password-1234")
    authorization = AuthorizationService(store)
    return WebSuiteGateway(authorization), auth, authorization, admin, viewer


def test_all_launchers_reuse_their_real_gui_api_and_shared_theme(web):
    gateway, _, _, admin, _ = web
    shell = gateway.shell(admin, "session")
    assert shell["ok"] and set(shell["pages"]) == set(PAGES)
    assert shell["theme"]["id"] == "graphite"
    for page in PAGES:
        response = gateway.call(admin, "session", page, "bootstrap", [])
        assert response["ok"], (page, response)
        assert response["theme"] == shell["theme"]
        assert response["projectContext"] == shell["projectContext"]
        assert "bootstrap" in response["webMethods"]
        assert response["remote"]
    preferences = {**shell["preferences"], "theme": "violet"}
    assert gateway.call(admin, "session", "panel", "save_gui_preferences", [preferences])["ok"]
    assert gateway.call(admin, "session", "wire", "bootstrap", [])["theme"]["id"] == "violet"


def test_remote_project_creation_and_switch_are_shared_by_every_page(web):
    gateway, _, _, admin, _ = web
    shell = gateway.shell(admin, "session")
    created = gateway.call(
        admin, "session", "panel", "create_project", ["Web project"], shell["projectContext"]
    )
    assert created["ok"], created
    path = created["activeProject"]
    assert Path(path).is_file()
    for page in PAGES:
        payload = gateway.call(admin, "session", page, "bootstrap", [])
        assert payload["projectContext"][0] == path, (page, payload)
    with pytest.raises(ValueError):
        gateway.call(
            admin,
            "session",
            "wire",
            "wire_create",
            [{"kind": "pc.1port", "prefix": "PC"}],
            shell["projectContext"],
        )
    with pytest.raises(PermissionError):
        gateway.call(
            admin, "session", "panel", "use_project", ["/etc/passwd"], created["projectContext"]
        )


def test_wire_edits_use_native_service_and_project_context(web):
    gateway, _, _, admin, _ = web
    expected = project_identity(config.load_config())
    result = gateway.call(
        admin,
        "session",
        "wire",
        "project_call",
        [expected, "wire_create", [{"kind": "pc.1port", "prefix": "PC", "name": "Web station"}]],
    )
    assert result["ok"], result
    assert (
        gateway.call(admin, "session", "wire", "bootstrap", [])["records"][0]["data"]["name"]
        == "Web station"
    )
    assert (
        gateway.call(admin, "session", "rack", "bootstrap", [])["elements"][0]["data"]["name"]
        == "Web station"
    )


def test_permissions_apply_to_nested_calls_and_native_commands_are_blocked(web):
    gateway, _, _, admin, viewer = web
    for method in (
        "terminal_send",
        "start_terminal",
        "launch_gui",
        "open_device",
        "trust_plugin_publisher",
        "request_close",
        "__getattribute__",
    ):
        with pytest.raises(PermissionError):
            gateway.call(admin, "session", "panel", method, [])
    with pytest.raises(PermissionError):
        gateway.call(
            viewer,
            "viewer",
            "wire",
            "project_call",
            [project_identity(config.load_config()), "wire_create", [{}]],
        )
    with pytest.raises(PermissionError):
        gateway.call(viewer, "viewer", "access", "bootstrap", [])
    assert "access" not in gateway.shell(viewer, "viewer")["pages"]
    for page, method, args in (
        ([], "bootstrap", []),
        ("panel", [], []),
        ("panel", "project_call", [None, [], []]),
        ("panel", "project_call", [None, "bootstrap", {}]),
    ):
        with pytest.raises(ValueError):
            gateway.call(admin, "session", page, method, args)
    for path in ("access.remote.enabled", "projects.directory", "storage.database"):
        with pytest.raises(PermissionError):
            gateway.call(
                admin,
                "session",
                "panel",
                "save_catalog_settings",
                [{path: True}],
                project_identity(config.load_config()),
            )


def test_vault_unlock_is_session_local_and_logout_forgets_it(web):
    _, _, authorization, admin, _ = web

    class Fake:
        def __init__(self):
            self._lock = RLock()
            self.locked = True

        def bootstrap(self):
            return {"ok": True, "locked": self.locked}

        def access_unlock(self, password, confirmation=""):
            self.locked = False
            return {"ok": True}

    gateway = WebSuiteGateway(authorization, lambda _page: Fake())
    expected = project_identity(config.load_config())
    assert gateway.call(admin, "A", "access", "access_unlock", ["example"], expected)["ok"]
    assert not gateway.call(admin, "A", "access", "bootstrap", [])["locked"]
    assert gateway.call(admin, "B", "access", "bootstrap", [])["locked"]
    gateway.forget("A")
    assert gateway.call(admin, "A", "access", "bootstrap", [])["locked"]


def test_https_routes_embed_existing_pages_and_protect_rpc(web, tmp_path):
    gateway, auth, authorization, _, _ = web
    certificate, key = generate_certificate(tmp_path / "web.crt", tmp_path / "web.key", "127.0.0.1")
    server = HttpsAccessServer(
        "127.0.0.1",
        0,
        "127.0.0.0/8",
        certificate,
        key,
        auth,
        authorization,
        allowed_origin="https://core.lan",
        gui_api=object(),
    )
    server.web_suite = gateway
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    connection = http.client.HTTPSConnection(
        "127.0.0.1", server.server.server_address[1], context=ssl._create_unverified_context()
    )

    def get(path):
        connection.request("GET", path)
        response = connection.getresponse()
        return response.status, response.read(), dict(response.getheaders())

    def post(path, body, headers=None):
        connection.request(
            "POST", path, json.dumps(body), {"Content-Type": "application/json", **(headers or {})}
        )
        response = connection.getresponse()
        return response.status, json.loads(response.read()), dict(response.getheaders())

    try:
        for page in PAGES:
            status, html, _ = get("/lanctl/" + page)
            assert status == 200 and b"web-sidebar" in html
            status, html, headers = get("/lanctl/view/" + page)
            assert status == 200 and b'base href="/lanctl/resources/"' in html
            assert b"web-bridge.js" in html and b'data-lanctl-web="true"' in html
            assert "frame-ancestors 'self'" in headers["Content-Security-Policy"]
        assert b'id="device-rows"' in get("/lanctl/view/ip")[1]
        assert b'id="workspace"' in get("/lanctl/view/wire")[1]
        for path in (
            "/lanctl/resources/web-shell.js",
            "/lanctl/resources/web-bridge.js",
            "/lanctl/resources/suite.js",
            "/lanctl/assets/launcher-icons/lanctl.svg",
        ):
            assert get(path)[0] == 200, path
        for path in (
            "/lanctl/missing",
            "/lanctl/view/missing",
            "/lanctl/resources/../../pyproject.toml",
            "/lanctl/assets/../../pyproject.toml",
            "/lanctl/resources/suite.html",
        ):
            assert get(path)[0] == 404, path
        assert (
            post("/lanctl/api/gui", {"page": "panel", "method": "bootstrap", "args": []})[0] == 401
        )
        status, login, headers = post(
            "/lanctl/api/login", {"username": "administrator", "password": "example-password-1234"}
        )
        assert status == 200
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        headers = {
            "Cookie": cookie,
            "X-CSRF-Token": login["csrfToken"],
            "Origin": "https://core.lan",
        }
        status, result, _ = post("/lanctl/api/shell", {}, headers)
        assert status == 200 and result["ok"]
        assert set(result["pages"]) == set(PAGES)
        assert (
            post(
                "/lanctl/api/gui",
                {"page": "panel", "method": "bootstrap", "args": []},
                {"Cookie": cookie},
            )[0]
            == 403
        )
        assert (
            post(
                "/lanctl/api/gui",
                {"page": "panel", "method": "bootstrap", "args": []},
                {**headers, "Origin": "https://evil.example"},
            )[0]
            == 403
        )
        assert (
            post(
                "/lanctl/api/gui",
                {"page": "panel", "method": "start_terminal", "args": []},
                headers,
            )[0]
            == 403
        )
        assert post("/lanctl/api/logout", {}, headers)[0] == 200
        assert post("/lanctl/api/shell", {}, headers)[0] == 401
    finally:
        connection.close()
        server.stop()
        thread.join(3)


def test_service_links_are_deployment_owned_and_reject_credential_urls(monkeypatch):
    for name in ("HARDWARE", "DNS", "VPN"):
        monkeypatch.delenv("LANCTL_WEB_" + name + "_URL", raising=False)
    assert all(not item["url"] for item in WebSuiteGateway.services())
    monkeypatch.setenv("LANCTL_WEB_HARDWARE_URL", "https://core.lan/hardware/")
    assert WebSuiteGateway.services()[0]["url"] == "https://core.lan/hardware/"
    for invalid in (
        "javascript:alert(1)",
        "https://user:secret@core.lan/",
        "https://core.lan:bad/",
        "https://core.lan/\nnext",
    ):
        monkeypatch.setenv("LANCTL_WEB_HARDWARE_URL", invalid)
        with pytest.raises(ValueError):
            WebSuiteGateway.services()
