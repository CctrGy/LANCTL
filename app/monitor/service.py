from __future__ import annotations
import time,uuid
from datetime import datetime
from app.core.history import HistoryEvent,HistoryService
from .checks import CheckRegistry,availability
from .incidents import IncidentManager
from .models import CheckSpec
from .repositories import DefaultConfigProvider,InMemoryIncidentRepository,InMemoryMetricsStore,InMemorySessionRepository,NullReportBuilder
from .scheduler import MonitorScheduler,MonitorWorkerPool
from .sessions import SessionManager
from .state import StateEvaluator

class MonitorService:
    def __init__(self,*,config=None,assignments=None,metrics=None,sessions=None,incidents=None,reports=None,clock=time.monotonic):
        if config is None:
            try:
                from .configuration import ConfigProvider
                config=ConfigProvider()
            except (ValueError,OSError):config=DefaultConfigProvider()
        self.config=config;self.assignments=assignments;self.metrics=metrics or InMemoryMetricsStore();self.session_repo=sessions or InMemorySessionRepository();self.incident_repo=incidents or InMemoryIncidentRepository();self.reports=reports or NullReportBuilder();self.clock=clock
        self.registry=CheckRegistry();self.registry.register(CheckSpec("availability","LANCTL",availability,10,1,True));self.session_manager=SessionManager(self.session_repo);self.incidents=IncidentManager(self.incident_repo);self.scheduler=None;self.evaluator=None
    def start(self,session,profile_id="default"):
        profile=self.config.profile(profile_id);self.evaluator=StateEvaluator(profile);self.scheduler=MonitorScheduler(MonitorWorkerPool(profile.workers,max(profile.workers,profile.workers*8)),self.clock,profile.jitter)
        session.status="active";self.session_repo.save(session);self._history("monitor.started",session,"success","Monitor iniciado")
        if self.assignments:
            for target in self.assignments.targets(session):self.scheduler.schedule(f"monitor.{target.device_id}.availability",target.device_id,"availability",profile.presence_interval,profile.timeout,lambda _id,timeout,t=target:self._run_check("availability",t,timeout,session))
        return session
    def _run_check(self,check_id,target,timeout,session):
        result=self.registry.get(check_id).handler(target,timeout);self.metrics.write(result,session.sessionId);state,changed,before=self.evaluator.evaluate(result)
        database=getattr(self.metrics,"db",None)
        if database:
            with database.connection:database.execute("INSERT INTO device_state(device_id,presence,health,latency_ms,updated_at,session_id) VALUES(?,?,?,?,?,?) ON CONFLICT(device_id) DO UPDATE SET presence=excluded.presence,health=excluded.health,latency_ms=excluded.latency_ms,updated_at=excluded.updated_at,session_id=excluded.session_id",(state.deviceId,state.presence,state.health,result.latencyMs,state.updatedAt,session.sessionId))
        if changed:
            if state.presence=="offline":self.incidents.open(state.deviceId,"critical","device.offline","monitor.state.evaluate",session.runId,session.sessionId);self._history("device.offline",session,"error",f"{state.deviceId} está offline")
            elif state.presence=="online":self.incidents.resolve(state.deviceId,"device.offline");self._history("device.recovered" if before[0]=="offline" else "device.online",session,"success",f"{state.deviceId} está online")
        return result
    def cycle(self):
        if not self.scheduler:return 0
        expired=self.session_manager.expire()
        if expired:
            if self.scheduler:self.scheduler.close();self.scheduler=None
            self.reports.completed(expired);self._history("monitor.session.stopped",expired,"success","Sesión expirada");return 0
        return self.scheduler.tick()
    def foreground(self,poll=.2,stop_event=None):
        while not (stop_event and stop_event.is_set()):self.cycle();time.sleep(poll)
    def stop(self,status="completed"):
        if self.scheduler:self.scheduler.close();self.scheduler=None
        try:session=self.session_manager.stop(status)
        except RuntimeError:return None
        self.reports.completed(session);self._history("monitor.stopped",session,"success","Monitor detenido");return session
    def _history(self,event_type,session,result,summary):
        try:HistoryService().write(HistoryEvent(event_type,"lanctl.monitor","local",result,summary,correlationId=session.runId,runId=session.runId,taskId="monitor.management",operationId="monitor.history.write",details={"sessionId":session.sessionId,"mode":session.mode,"authority":session.authority}))
        except (ValueError,OSError):pass
