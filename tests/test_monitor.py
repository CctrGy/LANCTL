import json,tempfile,unittest
from datetime import datetime,timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock,patch

from app.cli import build_parser
from app.monitor.checks import CheckRegistry
from app.monitor.identity import IdentityResolver,NetworkIdentity
from app.monitor.incidents import IncidentManager
from app.monitor.lifecycle import SingletonLock
from app.monitor.models import CheckResult,CheckSpec,MonitorProfile
from app.monitor.repositories import InMemoryIncidentRepository,InMemorySessionRepository
from app.monitor.scheduler import MonitorScheduler,MonitorWorkerPool
from app.monitor.sessions import SessionManager
from app.monitor.state import StateEvaluator
from app.platform.linux import LinuxPlatform
from app.core.database import DeviceDatabase

class ImmediateFuture:
    def __init__(self,fn,args):
        try:self.value=fn(*args);self.error=None
        except Exception as error:self.error=error
    def add_done_callback(self,callback):callback(self)
    def result(self):
        if self.error:raise self.error
        return self.value
class ImmediateExecutor:
    def submit(self,fn,*args):return ImmediateFuture(fn,args)
    def shutdown(self,**kwargs):pass

class MonitorTests(unittest.TestCase):
    def test_scheduler_uses_monotonic_queue_no_overlap_and_backoff(self):
        now=[0.0];calls=[];pool=MonitorWorkerPool(1,1,ImmediateExecutor());scheduler=MonitorScheduler(pool,lambda:now[0],jitter=0)
        scheduler.schedule("task","dev","availability",10,1,lambda target,timeout:calls.append(target))
        self.assertEqual(scheduler.tick(),1);self.assertEqual(calls,["dev"]);self.assertEqual(scheduler.tick(),0)
        now[0]=10;self.assertEqual(scheduler.tick(),1);scheduler.close()

    def test_worker_backpressure_is_bounded(self):
        pool=MonitorWorkerPool(1,1,MagicMock());pool.executor.submit.return_value=MagicMock()
        self.assertIsNotNone(pool.submit(lambda:None));self.assertIsNone(pool.submit(lambda:None))

    def test_bounded_runner_limits_and_cooperative_cancellation(self):
        from app.monitor.operations import BoundedRunner
        clock=[0.0];calls=[]
        runner=BoundedRunner(lambda:clock[0],lambda seconds:clock.__setitem__(0,clock[0]+seconds))
        rows=runner.run(lambda:calls.append(1),interval=2,duration=10,cancel=lambda:len(calls)>=3)
        self.assertEqual(len(rows),3)
        with self.assertRaises(ValueError):runner.run(lambda:None,interval=.1,duration=1)

    def test_state_thresholds_and_recovery_are_hysteretic(self):
        evaluator=StateEvaluator(MonitorProfile(failure_threshold=3,recovery_threshold=2))
        for _ in range(2):state,changed,_=evaluator.evaluate(CheckResult("availability","dev",False))
        self.assertEqual(state.presence,"unknown")
        state,changed,_=evaluator.evaluate(CheckResult("availability","dev",False));self.assertEqual(state.presence,"offline");self.assertTrue(changed)
        evaluator.evaluate(CheckResult("availability","dev",True));self.assertEqual(state.presence,"offline")
        evaluator.evaluate(CheckResult("availability","dev",True));self.assertEqual(state.presence,"online")

    def test_incidents_dedupe_acknowledge_and_resolve(self):
        manager=IncidentManager(InMemoryIncidentRepository());first=manager.open("dev","critical","offline","monitor.state.evaluate");second=manager.open("dev","critical","offline","monitor.state.evaluate")
        self.assertEqual(first.incidentId,second.incidentId);manager.acknowledge(first.incidentId);self.assertEqual(manager.resolve("dev","offline").status,"resolved")

    def test_sessions_expire_without_authority_escalation(self):
        now=[datetime(2026,8,3,10,0).astimezone()];manager=SessionManager(InMemorySessionRepository(),clock=lambda:now[0])
        session=manager.start("mgr","project",mode="diagnostic",authority="observe",duration=60);self.assertEqual(session.authority,"observe")
        now[0]+=timedelta(seconds=61);self.assertEqual(manager.expire().status,"expired")

    def test_network_identity_mismatch_requires_confirmation(self):
        resolver=IdentityResolver(SimpleNamespace(identity=lambda:NetworkIdentity(gatewayMac="AA")))
        with self.assertRaises(PermissionError):resolver.validate(NetworkIdentity(gatewayMac="BB"),resolver.resolve())
        self.assertFalse(resolver.validate(NetworkIdentity(gatewayMac="BB"),resolver.resolve(),confirm=True))

    def test_check_registry_validates_plugin_limits(self):
        registry=CheckRegistry()
        with self.assertRaises(ValueError):registry.register(CheckSpec("bad","plugin",lambda:None,1,1))
        registry.register(CheckSpec("good","plugin",lambda:None,5,1));self.assertEqual(registry.get("good").owner,"plugin")

    def test_singleton_recovers_stale_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/"monitor.lock";path.write_text('{"pid":99999999}')
            lock=SingletonLock(path).acquire();self.assertTrue(lock.status()["running"]);lock.release();self.assertFalse(path.exists())

    def test_systemd_unit_is_safe_and_install_needs_confirmation(self):
        adapter=LinuxPlatform();unit=adapter.unit_text("/usr/bin/python3","/tmp/test.vlf")
        self.assertIn('ExecStart="/usr/bin/python3" -m app monitor foreground --project "/tmp/test.vlf"',unit)
        self.assertIn("NoNewPrivileges=true",unit);self.assertEqual(adapter.service("install",confirm=False).status,"blocked")
        with self.assertRaises(ValueError):adapter.unit_text("bad\ncommand","/tmp/test.vlf")
        with self.assertRaises(ValueError):adapter.unit_text("/usr/bin/python3","")

    def test_systemd_unit_quotes_paths_with_spaces(self):
        unit=LinuxPlatform().unit_text("/opt/LAN CTL/python", "/srv/LAN projects/site.vlf")
        self.assertIn('ExecStart="/opt/LAN CTL/python"', unit)
        self.assertIn('--project "/srv/LAN projects/site.vlf"', unit)

    def test_cli_parser_and_status_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            args=build_parser().parse_args(["monitor","status","--json","--monitor-db",str(Path(temporary)/"monitor.db"),"--lock",str(Path(temporary)/"lock")])
            from io import StringIO
            import contextlib
            output=StringIO()
            with contextlib.redirect_stdout(output):self.assertEqual(args.handler(args),0)
            self.assertIsNone(json.loads(output.getvalue())["status"])

    def _cli_context(self,temporary):
        root=Path(temporary);devices=root/"devices.json";DeviceDatabase(devices).upsert([{"IP":"192.168.1.8","MAC":"02:11:22:33:44:55","ALIAS":"NAS"}])
        return {"database":str(devices),"monitorDatabase":str(root/"monitor.db"),"monitorProfiles":str(root/"profiles.json"),"monitorAssignments":str(root/"assignments.json"),"monitorRuntime":str(root/"sessions.json"),"monitorIncidents":str(root/"incidents.json"),"monitorLock":str(root/"lock"),"timeout":.1,"workers":1,"activeProject":None}

    def test_ping_route_uses_bounded_runner_and_metrics_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            config=self._cli_context(temporary);args=build_parser().parse_args(["monitor","ping","NAS","--duration","10s","--interval","2s","--monitor-db",config["monitorDatabase"]])
            with patch("app.commands.monitor.load_config",return_value=config),patch("app.commands.monitor.ping_targets",return_value={"status":"completed","samples":5,"lossPercent":0}) as runner:
                from io import StringIO
                import contextlib
                with contextlib.redirect_stdout(StringIO()):self.assertEqual(args.handler(args),0)
            self.assertEqual(runner.call_args.kwargs["interval"],2);self.assertEqual(runner.call_args.kwargs["duration"],10)

    def test_scan_presence_and_identify_routes_are_real(self):
        with tempfile.TemporaryDirectory() as temporary:
            config=self._cli_context(temporary)
            scan=build_parser().parse_args(["monitor","scan","NAS","--type","presence","--monitor-db",config["monitorDatabase"]])
            identify=build_parser().parse_args(["monitor","identify","NAS","--monitor-db",config["monitorDatabase"]])
            from io import StringIO
            import contextlib
            with patch("app.commands.monitor.load_config",return_value=config),patch("app.commands.monitor.scan_target",return_value={"success":True}) as scanner,patch("app.commands.monitor.identify_target",return_value={"confidence":"confirmed"}),contextlib.redirect_stdout(StringIO()):self.assertEqual(scan.handler(scan),0);self.assertEqual(identify.handler(identify),0)
            scanner.assert_called_once()

    def test_smb_scan_is_specifically_unsupported_when_provider_absent(self):
        with tempfile.TemporaryDirectory() as temporary:
            config=self._cli_context(temporary);args=build_parser().parse_args(["monitor","scan","NAS","--type","smb","--monitor-db",config["monitorDatabase"]])
            manager=MagicMock();manager.list.return_value=[]
            from io import StringIO
            import contextlib
            output=StringIO()
            with patch("app.commands.monitor.load_config",return_value=config),patch("app.plugins.manager.get_plugin_manager",return_value=manager),contextlib.redirect_stdout(output):self.assertEqual(args.handler(args),1)
            self.assertEqual(json.loads(output.getvalue())["operationId"],"monitor.scan.smb")

    def test_health_and_events_read_real_repositories(self):
        with tempfile.TemporaryDirectory() as temporary:
            config=self._cli_context(temporary)
            health=build_parser().parse_args(["monitor","health","--monitor-db",config["monitorDatabase"]]);events=build_parser().parse_args(["monitor","events","--monitor-db",config["monitorDatabase"]])
            history=MagicMock();history.query.return_value=[]
            from io import StringIO
            import contextlib
            with patch("app.commands.monitor.load_config",return_value=config),patch("app.commands.monitor.HistoryService",return_value=history),contextlib.redirect_stdout(StringIO()):self.assertEqual(health.handler(health),0);self.assertEqual(events.handler(events),0)

    def test_restart_never_kills_without_verified_active_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            config=self._cli_context(temporary);args=build_parser().parse_args(["monitor","restart","--monitor-db",config["monitorDatabase"],"--lock",config["monitorLock"]])
            from io import StringIO
            import contextlib
            output=StringIO()
            with patch("app.commands.monitor.load_config",return_value=config),patch("app.commands.monitor.os.kill") as killed,contextlib.redirect_stdout(output):self.assertEqual(args.handler(args),0)
            killed.assert_not_called();self.assertEqual(json.loads(output.getvalue())["status"],"not-running")

if __name__=="__main__":unittest.main()
