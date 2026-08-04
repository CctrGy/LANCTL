import tempfile,unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
from app.monitor.configuration import *
from app.monitor.database import *
from app.monitor.models import CheckResult,Incident,MonitorSession
from app.monitor.reports import ReportBuilder,monitor_view

class MonitorDataTests(unittest.TestCase):
 def test_durations_config_and_saturation(self):
  self.assertEqual(parse_duration("5m"),300)
  with self.assertRaises(ValueError):parse_duration("eval(1)")
  with self.assertRaises(ValueError):MonitorConfig(mode="temporary")
  with self.assertRaisesRegex(ValueError,"saturar"):validate_profile(MonitorProfile("bad",1,1,5,5,5))
 def test_profiles_and_assignments_transactional(self):
  with tempfile.TemporaryDirectory() as t:
   profiles=ProfileManager(Path(t)/"profiles.json");profiles.save(MonitorProfile("storage"));self.assertEqual(profiles.profile("storage").profile_id,"storage")
   with self.assertRaises(ValueError):profiles.delete("normal")
   assignments=AssignmentManager(Path(t)/"assignments.json");one=assignments.assign("NAS",device_id="dev_1",checks=({"type":"port","interval":"30s","args":{"port":22}},));two=assignments.assign("NAS2",device_id="dev_1",priority="critical")
   self.assertEqual(one.assignmentId,two.assignmentId);self.assertEqual(len(assignments.list()),1)
 def test_sqlite_samples_aggregate_retention_sessions_incidents_report(self):
  with tempfile.TemporaryDirectory() as t:
   with MonitorDatabase(Path(t)/"monitor.db") as db:
    metrics=MetricsStore(db);now=datetime.now(timezone.utc);old=(now-timedelta(days=2)).isoformat()
    metrics.write(CheckResult("availability","dev_1",True,timestamp=old,latencyMs=10),"s1");metrics.write(CheckResult("availability","dev_1",False,timestamp=now.isoformat()),"s1")
    self.assertGreater(metrics.aggregate(now=now),0);self.assertEqual(metrics.cleanup({"rawSamples":"24h","fiveMinuteAggregates":"30d","hourlyAggregates":"365d"},now=now),1)
    sessions=SessionRepository(db);session=MonitorSession("s1","r1","m1","p1","net","eth0","10.0.0.2","once","observe",now.isoformat(),status="completed");sessions.save(session)
    incidents=IncidentRepository(db);incident=Incident("i1","dev_1","critical","offline","test",now.isoformat(),sessionId="s1");incidents.save(incident);incident.status="resolved";incident.resolvedAt=now.isoformat();incidents.save(incident)
    report=ReportBuilder(db,sessions,incidents).build(session);self.assertEqual(report["summary"]["incidents"],1);self.assertEqual(len(db.execute("SELECT transitions FROM incidents").fetchone()[0])>2,True)
    self.assertIn("items",monitor_view(db))
 def test_future_schema_and_cross_platform_path(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/"future.db";connection=__import__('sqlite3').connect(path);connection.execute("PRAGMA user_version=99");connection.close()
   with self.assertRaisesRegex(ValueError,"futura"):MonitorDatabase(path)
  self.assertEqual(monitor_database_path(environment={"XDG_STATE_HOME":"/tmp/state"},platform_name="Linux"),Path("/tmp/state/lanctl/monitor.db"))
 def test_identity_evidence_mismatch_is_explicit(self):
  with tempfile.TemporaryDirectory() as t:
   with MonitorDatabase(Path(t)/"m.db") as db:
    identities=IdentityRepository(db);first=identities.manager();self.assertEqual(first["manager_id"],identities.manager()["manager_id"])
    identities.save_network("lan1",evidence=("gw:aa",),confidence=.9);self.assertFalse(identities.compare("lan1",("gw:bb",))["match"])

if __name__=="__main__":unittest.main()
