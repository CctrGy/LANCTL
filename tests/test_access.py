import json
import tempfile
import unittest
from contextlib import suppress
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from lanctl.apps.access.auth import (
    AuthenticationService,
    AuthorizationService,
    fingerprint_key,
    verify_password,
)
from lanctl.apps.access.firewall import FirewallManager
from lanctl.apps.access.https_server import (
    COOKIE_ATTRIBUTES,
    SECURITY_HEADERS,
    HttpsAccessServer,
    HttpsCapability,
)
from lanctl.apps.access.keys import generate_certificate, generate_host_key
from lanctl.apps.access.network import source_allowed, validate_endpoint
from lanctl.apps.access.remote import (
    LanctlCommandAdapter,
    RemoteGuiApi,
    parse_remote_command,
    required_permission,
)
from lanctl.apps.access.runtime import AccessRuntime
from lanctl.apps.access.service import AccessService
from lanctl.apps.access.ssh_server import RestrictedSshServer, SshAccessServer
from lanctl.apps.access.store import AccessStore
from lanctl.apps.ip.interfaces.cli.commands.access import _public_session, _setup_wizard
from lanctl.apps.ip.interfaces.cli.main import build_parser


class AccessTests(unittest.TestCase):
    def test_users_dc_migrates_the_legacy_store_without_exposing_passwords(self):
        with tempfile.TemporaryDirectory() as temporary:
            legacy = Path(temporary) / "users.json"
            old_store = AccessStore(legacy)
            AuthenticationService(old_store).add_user(
                "administrator", ["administrator"], "a-very-strong-password"
            )

            store = AccessStore(Path(temporary) / "users.dc")

            self.assertFalse(legacy.exists())
            self.assertEqual(store.users()[0].username, "administrator")
            self.assertNotIn("a-very-strong-password", store.path.read_text(encoding="utf-8"))

    def test_defaults_are_disabled_and_monitor_does_not_change_them(self):
        with tempfile.TemporaryDirectory() as temporary:
            service = AccessService(Path(temporary) / "config.json", Path(temporary) / "users.json")
            status = service.initialize()
            self.assertFalse(status["ssh"]["enabled"])
            self.assertFalse(status["https"]["enabled"])

    def test_bind_and_source_are_lan_restricted(self):
        self.assertEqual(validate_endpoint("192.168.1.5", "192.168.1.0/24", 8443)[0], "192.168.1.5")
        self.assertTrue(source_allowed("192.168.1.20", "192.168.1.0/24"))
        self.assertFalse(source_allowed("8.8.8.8", "192.168.1.0/24"))
        for bind in ("0.0.0.0", "::", "localhost"):
            with self.assertRaises(ValueError):
                validate_endpoint(bind, "192.168.1.0/24", 8443)

    def test_password_hash_rbac_lock_and_no_plaintext(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = AccessStore(Path(temporary) / "users.json")
            auth = AuthenticationService(store)
            user = auth.add_user("operator", ["operator"], "a-very-strong-password")
            raw = store.path.read_text()
            self.assertNotIn("a-very-strong-password", raw)
            self.assertTrue(verify_password("a-very-strong-password", user.passwordHash))
            AuthorizationService(store).require(user, "wol.send")
            with self.assertRaises(PermissionError):
                AuthorizationService(store).require(user, "users.manage")
            for _ in range(5):
                with self.assertRaises(PermissionError):
                    auth.authenticate_password("operator", "wrong", "192.168.1.2")
            self.assertIsNotNone(auth.user("operator").lockedUntil)

    def test_ssh_and_web_authenticators_are_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = AccessStore(Path(temporary) / "users.json")
            auth = AuthenticationService(store)
            key = (
                "ssh-ed25519 " + __import__("base64").b64encode(b"test-key").decode() + " user@test"
            )
            user = auth.add_user("alice", ["viewer"], "another-strong-password", [key])
            self.assertNotEqual(user.passwordHash, user.sshKeys[0])
            self.assertEqual(
                auth.authenticate_ssh_key("alice", key, "192.168.1.2").userId, user.userId
            )

    def test_sessions_csrf_revocation_and_pairing_single_use(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = AccessStore(Path(temporary) / "users.json")
            auth = AuthenticationService(store)
            user = auth.add_user("alice", ["viewer"], "another-strong-password")
            session, csrf = auth.create_session(user, "web-password", "192.168.1.2")
            self.assertEqual(
                auth.validate_session(session.sessionId, "192.168.1.2", csrf).userId, user.userId
            )
            with self.assertRaises(PermissionError):
                auth.validate_session(session.sessionId, "192.168.1.2", "bad")
            auth.revoke(session.sessionId)
            with self.assertRaises(PermissionError):
                auth.validate_session(session.sessionId, "192.168.1.2")
            code = auth.create_pairing(user.userId)
            self.assertEqual(auth.consume_pairing(code).userId, user.userId)
            with self.assertRaises(PermissionError):
                auth.consume_pairing(code)
            self.assertNotIn("csrfHash", _public_session(session))

    def test_destructive_remote_commands_require_administrator_permission(self):
        self.assertEqual(
            required_permission(["element", "192.0.2.1", "-delete"]),
            "system.destructive",
        )
        with tempfile.TemporaryDirectory() as temporary:
            store = AccessStore(Path(temporary) / "users.json")
            auth = AuthenticationService(store)
            operator = auth.add_user("operator", ["operator"], "another-strong-password")
            administrator = auth.add_user(
                "administrator", ["administrator"], "another-strong-password"
            )
            with self.assertRaises(PermissionError):
                AuthorizationService(store).require(operator, "system.destructive")
            self.assertTrue(
                AuthorizationService(store).require(administrator, "system.destructive")
            )

    def test_expired_user_is_rejected_at_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            auth = AuthenticationService(AccessStore(Path(temporary) / "users.json"))
            with self.assertRaisesRegex(ValueError, "futura"):
                auth.add_user(
                    "expired",
                    ["viewer"],
                    "another-strong-password",
                    expires_at=(datetime.now().astimezone() - timedelta(minutes=1)).isoformat(),
                )

    def test_ssh_policy_forbids_os_access_and_forwarding(self):
        server = RestrictedSshServer(None, None)
        import paramiko

        self.assertEqual(server.check_channel_request("session", 1), paramiko.OPEN_SUCCEEDED)
        self.assertNotEqual(
            server.check_channel_request("direct-tcpip", 1), paramiko.OPEN_SUCCEEDED
        )
        self.assertFalse(server.check_channel_shell_request(None))
        self.assertFalse(server.check_channel_exec_request(None, b"whoami"))
        self.assertFalse(server.check_channel_subsystem_request(None, "sftp"))
        self.assertFalse(server.check_port_forward_request())

    def test_https_security_contract(self):
        self.assertIn("Secure", COOKIE_ATTRIBUTES)
        self.assertIn("HttpOnly", COOKIE_ATTRIBUTES)
        self.assertIn("SameSite=Strict", COOKIE_ATTRIBUTES)
        self.assertIn("default-src 'self'", SECURITY_HEADERS["Content-Security-Policy"])
        self.assertFalse(HttpsCapability.cors("https://evil", "*"))
        self.assertTrue(HttpsCapability.cors("https://lanctl", "https://lanctl"))

    def test_enable_requires_keys_and_cli_is_registered(self):
        with tempfile.TemporaryDirectory() as temporary:
            service = AccessService(Path(temporary) / "config.json", Path(temporary) / "users.json")
            service.initialize()
            service.configure("ssh", bind="192.168.1.5", cidr="192.168.1.0/24", port=2222)
            with self.assertRaisesRegex(RuntimeError, "host key"):
                service.enable("ssh")
        args = build_parser().parse_args(["access", "status"])
        self.assertEqual(args.words, ["status"])

    def test_monitor_configuration_never_enables_remote_access(self):
        with tempfile.TemporaryDirectory() as temporary:
            service = AccessService(Path(temporary) / "config.json", Path(temporary) / "users.json")
            service.initialize()
            before = service.status()
            from lanctl.apps.monitor.configuration import ConfigProvider

            with suppress(ValueError):
                ConfigProvider(config={"monitor": {"enabled": True}}).monitor()
            after = service.status()
            self.assertEqual(before["ssh"]["enabled"], after["ssh"]["enabled"])
            self.assertEqual(before["https"]["enabled"], after["https"]["enabled"])

    def test_setup_wizard_fails_closed(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            patch("builtins.input", side_effect=["0.0.0.0", "192.168.1.0/24", "2222", "8443"]),
            patch("builtins.print"),
        ):
            service = AccessService(Path(temporary) / "config.json", Path(temporary) / "users.json")
            with self.assertRaises(ValueError):
                _setup_wizard(service)
            self.assertFalse(service.config()["ssh"]["enabled"])
            self.assertFalse(service.config()["https"]["enabled"])

    def test_firewall_rule_is_limited_and_injectable(self):
        calls = []

        class Completed:
            returncode = 0

        manager = FirewallManager(
            "Windows", lambda command, **kwargs: calls.append(command) or Completed()
        )
        rule = manager.add("https", "192.168.1.5", "192.168.1.0/24", 8443)
        self.assertIn("remoteip=192.168.1.0/24", calls[0])
        self.assertIn("localip=192.168.1.5", calls[0])
        self.assertIn("profile=private", calls[0])
        manager.remove(rule)
        self.assertIn("delete", calls[1])

    def test_openssh_fingerprint_ignores_comment(self):
        encoded = __import__("base64").b64encode(b"binary-openssh-key").decode()
        plain = f"ssh-ed25519 {encoded}"
        self.assertEqual(
            fingerprint_key(plain + " first@host"), fingerprint_key(plain + " second@host")
        )
        with self.assertRaises(ValueError):
            fingerprint_key("not-a-key")

    def test_certificate_uses_ip_or_dns_san(self):
        from cryptography import x509

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, expected in (
                ("192.168.1.5", "192.168.1.5"),
                ("lanctl.local", "lanctl.local"),
            ):
                certificate, _key = generate_certificate(
                    root / (name + ".crt"), root / (name + ".key"), name
                )
                value = x509.load_pem_x509_certificate(Path(certificate).read_bytes())
                san = value.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
                self.assertIn(expected, [str(item.value) for item in san])

    def test_remote_command_adapter_is_allowlisted_and_role_authorized(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = AccessStore(Path(temporary) / "users.json")
            user = AuthenticationService(store).add_user(
                "viewer", ["viewer"], "another-strong-password"
            )
            calls = []

            class Completed:
                returncode = 0
                stdout = "inventario\n"
                stderr = ""

            adapter = LanctlCommandAdapter(
                AuthorizationService(store),
                runner=lambda *a, **k: calls.append((a, k)) or Completed(),
            )
            code, output = adapter.execute(user, "lanctl list --format json")
            self.assertEqual((code, output), (0, "inventario"))
            self.assertFalse(calls[0][1]["shell"])
            with self.assertRaises(PermissionError):
                adapter.execute(user, "wol equipo")
            with self.assertRaises(PermissionError):
                adapter.execute(user, "access user list")
            self.assertEqual(
                parse_remote_command('lanctl search "core switch"'), ["search", "core switch"]
            )
            for command in (
                "wol equipo --datab C:/foreign.db",
                "wol equipo --stor C:/foreign.dc",
            ):
                with self.assertRaises(PermissionError):
                    parse_remote_command(command)

    def test_remote_root_commands_are_internal_and_permission_checked(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = AccessStore(Path(temporary) / "users.json")
            auth = AuthenticationService(store)
            viewer = auth.add_user("viewer", ["viewer"], "another-strong-password")
            admin = auth.add_user("admin", ["administrator"], "another-strong-password")
            adapter = LanctlCommandAdapter(AuthorizationService(store))
            with patch(
                "lanctl.apps.access.root_control.root_status", return_value={"state": "BACKEND"}
            ):
                code, output = adapter.execute(viewer, "root status")
            self.assertEqual(code, 0)
            self.assertIn("BACKEND", output)
            with self.assertRaises(PermissionError):
                adapter.execute(viewer, "root refresh")
            with patch(
                "lanctl.apps.access.root_control.forced_view", return_value={"launched": True}
            ):
                code, output = adapter.execute(admin, "root forced-view settings")
            self.assertEqual(code, 0)
            self.assertIn("launched", output)

    def test_remote_gui_rpc_enforces_permissions(self):
        class FakeApi:
            def list_devices(self, query=""):
                return {"ok": True, "devices": [query]}

            def scan_network(self, profile="normal"):
                return {"ok": True, "profile": profile}

        with tempfile.TemporaryDirectory() as temporary:
            store = AccessStore(Path(temporary) / "users.json")
            auth = AuthenticationService(store)
            viewer = auth.add_user("viewer", ["viewer"], "another-strong-password")
            remote = RemoteGuiApi(AuthorizationService(store), FakeApi())
            self.assertEqual(remote.call(viewer, "list_devices", ["router"])["devices"], ["router"])
            with self.assertRaises(PermissionError):
                remote.call(viewer, "scan_network", ["normal"])
            with self.assertRaises(PermissionError):
                remote.call(viewer, "open_terminal", ["router"])
            with self.assertRaises(PermissionError):
                remote.call(viewer, "plugin_action", ["windows-smb.scan", {}])

    def test_remote_device_deletion_requires_destructive_permission(self):
        class FakeApi:
            def delete_device(self, selector, confirmed=False):
                return {"ok": confirmed, "selector": selector}

        with tempfile.TemporaryDirectory() as temporary:
            store = AccessStore(Path(temporary) / "users.json")
            store.update(
                lambda value: value["roles"].update(
                    configurator=["inventory.read", "system.configure"]
                )
            )
            auth = AuthenticationService(store)
            configurator = auth.add_user(
                "configurator", ["configurator"], "another-strong-password"
            )
            administrator = auth.add_user(
                "administrator", ["administrator"], "another-strong-password"
            )
            remote = RemoteGuiApi(AuthorizationService(store), FakeApi())
            with self.assertRaisesRegex(PermissionError, "system.destructive"):
                remote.call(configurator, "delete_device", ["router", True])
            self.assertTrue(remote.call(administrator, "delete_device", ["router", True])["ok"])

    def test_https_serves_gui_and_authenticated_rpc(self):
        import http.client
        import ssl
        import threading

        class FakeApi:
            def list_devices(self, query=""):
                return {"ok": True, "devices": [query]}

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "index.html").write_text("<h1>LANCTL</h1>", encoding="utf-8")
            certificate, key = generate_certificate(root / "tls.crt", root / "tls.key", "127.0.0.1")
            store = AccessStore(root / "users.json")
            auth = AuthenticationService(store)
            auth.add_user("viewer", ["viewer"], "another-strong-password")
            server = HttpsAccessServer(
                "127.0.0.1",
                0,
                "127.0.0.0/8",
                certificate,
                key,
                auth,
                AuthorizationService(store),
                static_directory=root,
                gui_api=FakeApi(),
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            connection = http.client.HTTPSConnection(
                "127.0.0.1",
                server.server.server_address[1],
                context=ssl._create_unverified_context(),
            )
            try:
                connection.request("GET", "/")
                response = connection.getresponse()
                self.assertEqual(response.status, 200)
                self.assertIn(b"LANCTL", response.read())
                body = json.dumps({"username": "viewer", "password": "another-strong-password"})
                connection.request("POST", "/api/login", body, {"Content-Type": "application/json"})
                response = connection.getresponse()
                payload = json.loads(response.read())
                cookie = response.getheader("Set-Cookie").split(";", 1)[0]
                self.assertEqual(response.status, 200)
                rpc = json.dumps({"method": "list_devices", "args": ["switch"]})
                connection.request(
                    "POST",
                    "/api/rpc",
                    rpc,
                    {
                        "Content-Type": "application/json",
                        "Cookie": cookie,
                        "X-CSRF-Token": payload["csrfToken"],
                    },
                )
                response = connection.getresponse()
                result = json.loads(response.read())
                self.assertEqual(result["devices"], ["switch"])
            finally:
                connection.close()
                server.stop()
                thread.join(2)

    def test_ssh_exec_runs_only_the_lanctl_adapter(self):
        import threading
        import time

        import paramiko

        class Adapter:
            def execute(self, user, command):
                return (0, f"{user.username}:{command}")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            host_key = generate_host_key(root / "ssh_host_key")
            store = AccessStore(root / "users.json")
            auth = AuthenticationService(store)
            auth.add_user("operator", ["operator"], "another-strong-password")
            authorization = AuthorizationService(store)
            server = SshAccessServer(
                "127.0.0.1", 0, "127.0.0.0/8", host_key, auth, authorization, True, Adapter()
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            for _ in range(100):
                if server.socket:
                    break
                time.sleep(0.01)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(
                    "127.0.0.1",
                    port=server.socket.getsockname()[1],
                    username="operator",
                    password="another-strong-password",
                    allow_agent=False,
                    look_for_keys=False,
                    timeout=5,
                    auth_timeout=5,
                    banner_timeout=5,
                )
                _stdin, stdout, _stderr = client.exec_command("list")
                self.assertEqual(stdout.channel.recv_exit_status(), 0)
                self.assertIn("operator:list", stdout.read().decode())
            finally:
                client.close()
                server.stop()
                thread.join(2)

    def test_https_accepts_multiple_simultaneous_clients(self):
        import http.client
        import ssl
        import threading
        from concurrent.futures import ThreadPoolExecutor

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "index.html").write_text("LANCTL", encoding="utf-8")
            certificate, key = generate_certificate(root / "tls.crt", root / "tls.key", "127.0.0.1")
            store = AccessStore(root / "users.json")
            server = HttpsAccessServer(
                "127.0.0.1",
                0,
                "127.0.0.0/8",
                certificate,
                key,
                AuthenticationService(store),
                AuthorizationService(store),
                static_directory=root,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = server.server.server_address[1]

            def request(_index):
                connection = http.client.HTTPSConnection(
                    "127.0.0.1", port, context=ssl._create_unverified_context(), timeout=5
                )
                try:
                    connection.request("GET", "/")
                    response = connection.getresponse()
                    return response.status, response.read()
                finally:
                    connection.close()

            try:
                with ThreadPoolExecutor(max_workers=8) as executor:
                    results = list(executor.map(request, range(8)))
                self.assertEqual(results, [(200, b"LANCTL")] * 8)
            finally:
                server.stop()
                thread.join(2)

    def test_persistent_runtime_reconciles_enabled_services(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            service = AccessService(root / "config.json", root / "users.json")
            host_key = generate_host_key(root / "ssh_host_key")
            certificate, private_key = generate_certificate(
                root / "tls.crt", root / "tls.key", "127.0.0.1"
            )

            def enable(config):
                config["ssh"].update(
                    enabled=True, bind="127.0.0.1", cidr="127.0.0.0/8", port=0, hostKey=host_key
                )
                config["https"].update(
                    enabled=True,
                    bind="127.0.0.1",
                    cidr="127.0.0.0/8",
                    port=0,
                    certificate=certificate,
                    privateKey=private_key,
                )

            service.update_config(enable)
            runtime = AccessRuntime(service, poll_interval=0.5).start()
            try:
                self.assertEqual(set(runtime.instances), {"ssh", "https"})

                def disable(config):
                    config["ssh"]["enabled"] = False
                    config["https"]["enabled"] = False

                service.update_config(disable)
                runtime.reconcile()
                self.assertFalse(runtime.instances)
            finally:
                runtime.stop()

    def test_password_hash_rejects_untrusted_cost_before_scrypt(self):
        encoded = (
            "scrypt$999999999$"
            + __import__("base64").b64encode(b"0" * 16).decode()
            + "$"
            + __import__("base64").b64encode(b"0" * 32).decode()
        )
        with patch("lanctl.apps.access.auth.hashlib.scrypt") as derive:
            self.assertFalse(verify_password("password", encoded))
        derive.assert_not_called()


if __name__ == "__main__":
    unittest.main()
