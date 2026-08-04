import json,tempfile,unittest
from datetime import datetime,timedelta
from pathlib import Path
from unittest.mock import patch

from app.access.auth import AuthenticationService,AuthorizationService,hash_password,verify_password
from app.access.https_server import COOKIE_ATTRIBUTES,HttpsCapability,SECURITY_HEADERS
from app.access.firewall import FirewallManager
from app.access.network import source_allowed,validate_endpoint
from app.access.service import AccessService
from app.access.ssh_server import RestrictedSshServer
from app.access.store import AccessStore
from app.cli import build_parser
from app.commands.access import _public_session,_setup_wizard

class AccessTests(unittest.TestCase):
    def test_defaults_are_disabled_and_monitor_does_not_change_them(self):
        with tempfile.TemporaryDirectory() as temporary:
            service=AccessService(Path(temporary)/"config.json",Path(temporary)/"users.json");status=service.initialize()
            self.assertFalse(status["ssh"]["enabled"]);self.assertFalse(status["https"]["enabled"])

    def test_bind_and_source_are_lan_restricted(self):
        self.assertEqual(validate_endpoint("192.168.1.5","192.168.1.0/24",8443)[0],"192.168.1.5")
        self.assertTrue(source_allowed("192.168.1.20","192.168.1.0/24"));self.assertFalse(source_allowed("8.8.8.8","192.168.1.0/24"))
        for bind in ("0.0.0.0","::","localhost"):
            with self.assertRaises(ValueError):validate_endpoint(bind,"192.168.1.0/24",8443)

    def test_password_hash_rbac_lock_and_no_plaintext(self):
        with tempfile.TemporaryDirectory() as temporary:
            store=AccessStore(Path(temporary)/"users.json");auth=AuthenticationService(store);user=auth.add_user("operator",["operator"],"a-very-strong-password")
            raw=store.path.read_text();self.assertNotIn("a-very-strong-password",raw);self.assertTrue(verify_password("a-very-strong-password",user.passwordHash))
            AuthorizationService(store).require(user,"wol.send")
            with self.assertRaises(PermissionError):AuthorizationService(store).require(user,"users.manage")
            for _ in range(5):
                with self.assertRaises(PermissionError):auth.authenticate_password("operator","wrong","192.168.1.2")
            self.assertIsNotNone(auth.user("operator").lockedUntil)

    def test_ssh_and_web_authenticators_are_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            store=AccessStore(Path(temporary)/"users.json");auth=AuthenticationService(store);key="ssh-ed25519 AAAAC3NzaExample user@test"
            user=auth.add_user("alice",["viewer"],"another-strong-password",[key]);self.assertNotEqual(user.passwordHash,user.sshKeys[0]);self.assertEqual(auth.authenticate_ssh_key("alice",key,"192.168.1.2").userId,user.userId)

    def test_sessions_csrf_revocation_and_pairing_single_use(self):
        with tempfile.TemporaryDirectory() as temporary:
            store=AccessStore(Path(temporary)/"users.json");auth=AuthenticationService(store);user=auth.add_user("alice",["viewer"],"another-strong-password")
            session,csrf=auth.create_session(user,"web-password","192.168.1.2");self.assertEqual(auth.validate_session(session.sessionId,"192.168.1.2",csrf).userId,user.userId)
            with self.assertRaises(PermissionError):auth.validate_session(session.sessionId,"192.168.1.2","bad")
            auth.revoke(session.sessionId)
            with self.assertRaises(PermissionError):auth.validate_session(session.sessionId,"192.168.1.2")
            code=auth.create_pairing(user.userId);self.assertEqual(auth.consume_pairing(code).userId,user.userId)
            with self.assertRaises(PermissionError):auth.consume_pairing(code)
            self.assertNotIn("csrfHash",_public_session(session))

    def test_expired_user_is_rejected_at_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            auth=AuthenticationService(AccessStore(Path(temporary)/"users.json"))
            with self.assertRaisesRegex(ValueError,"futura"):
                auth.add_user("expired",["viewer"],"another-strong-password",expires_at=(datetime.now().astimezone()-timedelta(minutes=1)).isoformat())

    def test_ssh_policy_forbids_os_access_and_forwarding(self):
        server=RestrictedSshServer(None,None)
        import paramiko
        self.assertEqual(server.check_channel_request("session",1),paramiko.OPEN_SUCCEEDED);self.assertNotEqual(server.check_channel_request("direct-tcpip",1),paramiko.OPEN_SUCCEEDED);self.assertFalse(server.check_channel_shell_request(None));self.assertFalse(server.check_channel_exec_request(None,b"whoami"));self.assertFalse(server.check_channel_subsystem_request(None,"sftp"));self.assertFalse(server.check_port_forward_request())

    def test_https_security_contract(self):
        self.assertIn("Secure",COOKIE_ATTRIBUTES);self.assertIn("HttpOnly",COOKIE_ATTRIBUTES);self.assertIn("SameSite=Strict",COOKIE_ATTRIBUTES);self.assertIn("default-src 'self'",SECURITY_HEADERS["Content-Security-Policy"])
        self.assertFalse(HttpsCapability.cors("https://evil","*"));self.assertTrue(HttpsCapability.cors("https://lanctl","https://lanctl"))

    def test_enable_requires_keys_and_cli_is_registered(self):
        with tempfile.TemporaryDirectory() as temporary:
            service=AccessService(Path(temporary)/"config.json",Path(temporary)/"users.json");service.initialize();service.configure("ssh",bind="192.168.1.5",cidr="192.168.1.0/24",port=2222)
            with self.assertRaisesRegex(RuntimeError,"host key"):service.enable("ssh")
        args=build_parser().parse_args(["access","status"]);self.assertEqual(args.words,["status"])

    def test_monitor_configuration_never_enables_remote_access(self):
        with tempfile.TemporaryDirectory() as temporary:
            service=AccessService(Path(temporary)/"config.json",Path(temporary)/"users.json");service.initialize();before=service.status()
            from app.monitor.configuration import ConfigProvider
            try:ConfigProvider(config={"monitor":{"enabled":True}}).monitor()
            except ValueError:pass
            after=service.status();self.assertEqual(before["ssh"]["enabled"],after["ssh"]["enabled"]);self.assertEqual(before["https"]["enabled"],after["https"]["enabled"])

    def test_setup_wizard_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            service=AccessService(Path(temporary)/"config.json",Path(temporary)/"users.json")
            with patch("builtins.input",side_effect=["0.0.0.0","192.168.1.0/24","2222","8443"]),patch("builtins.print"):
                with self.assertRaises(ValueError):_setup_wizard(service)
            self.assertFalse(service.config()["ssh"]["enabled"]);self.assertFalse(service.config()["https"]["enabled"])

    def test_firewall_rule_is_limited_and_injectable(self):
        calls=[]
        class Completed:returncode=0
        manager=FirewallManager("Windows",lambda command,**kwargs:calls.append(command) or Completed())
        rule=manager.add("https","192.168.1.5","192.168.1.0/24",8443)
        self.assertIn("remoteip=192.168.1.0/24",calls[0]);self.assertIn("localip=192.168.1.5",calls[0]);self.assertIn("profile=private",calls[0])
        manager.remove(rule);self.assertIn("delete",calls[1])

if __name__=="__main__":unittest.main()
