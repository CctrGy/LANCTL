from __future__ import annotations
import argparse,json,platform,sys,subprocess,signal,threading,os
from dataclasses import asdict
from pathlib import Path
from app.core.conditions import duration
from app.core.config import load_config,save_config
from app.core.paths import application_path
from app.monitor.identity import IdentityResolver,NetworkIdentity
from app.monitor.incidents import IncidentManager
from app.monitor.lifecycle import SingletonLock
from app.monitor.repositories import JsonIncidentRepository,JsonSessionRepository
from app.monitor.sessions import SessionManager
from app.monitor.service import MonitorService
from app.core.database import DeviceDatabase
from app.monitor.operations import BoundedRunner,identify_target,ping_targets,scan_target
from app.monitor.database import MetricsStore
from app.core.history import HistoryService
import time
from app.monitor.configuration import AssignmentManager,MonitorProfile,ProfileManager,parse_duration,validate_monitor_settings
from app.monitor.database import IncidentRepository as SqlIncidentRepository,MonitorDatabase,SessionRepository as SqlSessionRepository
from app.monitor.reports import ReportBuilder
from app.core.database import DeviceDatabase

def register_monitor_command(commands):
    config=load_config();command=commands.add_parser("monitor",help="Opera sesiones y checks del monitor LAN.")
    command.add_argument("words",nargs="*",help="attach, detach, status, once, session, incidents, incident, service o foreground.")
    command.add_argument("--project");command.add_argument("--permanent",action="store_true");command.add_argument("--duration");command.add_argument("--mode",choices=("permanent","temporary","diagnostic","once"),default="temporary");command.add_argument("--authority",choices=("observe","operate","administer"),default="observe")
    command.add_argument("--json",action="store_true");command.add_argument("--yes",action="store_true");command.add_argument("--interval");command.add_argument("--every");command.add_argument("--group");command.add_argument("--type",choices=("presence","services","ports","identity","smb","full"));command.add_argument("--fast",action="store_true");command.add_argument("--unknown",action="store_true");command.add_argument("--follow",action="store_true")
    command.add_argument("--sessions",default=config["monitorRuntime"],help="Estado runtime de sesiones.");command.add_argument("--incidents-store",default=config["monitorIncidents"],help="Estado runtime de incidencias.");command.add_argument("--lock",default=config["monitorLock"],help="Lock singleton del monitor.")
    command.add_argument("--monitor-db",default=config["monitorDatabase"],help="Repositorio SQLite del monitor.");command.add_argument("--profiles",default=config["monitorProfiles"],help="Perfiles personalizados.");command.add_argument("--assignments-store",default=config["monitorAssignments"],help="Asignaciones persistentes.")
    command.add_argument("--profile",help="Perfil monitor.");command.add_argument("--priority",choices=("low","normal","high","critical"),default="normal",help="Prioridad de asignación.");command.add_argument("--check",action="append",default=[],help="Check ping, arp o port:NN.");command.add_argument("--presence",help="Intervalo de presencia.");command.add_argument("--discovery",help="Intervalo de descubrimiento.");command.add_argument("--services",help="Intervalo de servicios.");command.add_argument("--deep",help="Intervalo profundo.");command.add_argument("--workers",type=int,help="Workers del perfil.");command.add_argument("--timeout",type=float,help="Timeout del perfil.")
    for action in command._actions:
        if action.help is None:action.help="Opción operativa del monitor."
    command.set_defaults(handler=run_monitor)

def _database(args):return MonitorDatabase(application_path(args.monitor_db))
def _manager(args):return SessionManager(SqlSessionRepository(_database(args)))
def run_monitor(args):
    words=[x.casefold() for x in args.words];action=words[0] if words else "status";sessions=_manager(args)
    if action in {"attach","start"} or action=="session" and len(words)>1 and words[1]=="start":
        project=args.project or (args.words[1] if action=="attach" and len(args.words)>1 else load_config().get("activeProject"))
        if not project:raise ValueError("indica --project o un proyecto activo")
        if args.authority != "observe":raise PermissionError("operate/administer requiere una identidad de LAN confirmada por el proveedor de configuración")
        seconds=duration(args.duration) if args.duration else None;mode="permanent" if args.permanent else args.mode
        session=sessions.start(platform.node() or "manager",str(project),mode=mode,authority=args.authority,duration=seconds)
        command=[sys.executable,str(Path(__file__).resolve().parents[2]/"main.py"),"virtual","monitor","foreground","--monitor-db",args.monitor_db,"--profiles",args.profiles,"--assignments-store",args.assignments_store,"--lock",args.lock]
        flags=getattr(subprocess,"CREATE_NO_WINDOW",0) if platform.system()=="Windows" else 0
        process=subprocess.Popen(command,creationflags=flags,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        payload={**asdict(session),"processId":process.pid}
    elif action in {"detach","stop"} or action=="session" and len(words)>1 and words[1]=="stop":
        lock=SingletonLock(application_path(args.lock));state=lock.status()
        if state.get("running"):os.kill(state["pid"],signal.SIGTERM)
        payload=asdict(sessions.stop("cancelled"))
    elif action=="status":
        active=sessions.repository.active();lock=SingletonLock(application_path(args.lock)).status();payload={"status":asdict(active) if active else None,"process":lock}
    elif action=="once":
        if args.authority!="observe":raise PermissionError("monitor once solo permite observe sin identidad de LAN confirmada")
        project=args.project or load_config().get("activeProject") or "-";session=sessions.start(platform.node() or "manager",str(project),mode="once",authority=args.authority)
        from app.monitor.checks import availability
        store=MetricsStore(sessions.repository.db);results=[]
        for device in DeviceDatabase(load_config()["database"]).load():
            if not device.ip or device.ip=="-":continue
            checked=availability(device,float(load_config().get("timeout",.8)));store.write(checked,session.sessionId);results.append(asdict(checked))
        session.status="completed";sessions.repository.save(session)
        report=ReportBuilder(sessions.repository.db,sessions.repository,SqlIncidentRepository(sessions.repository.db),load_config().get("activeProject")).completed(session)
        payload={"session":asdict(session),"checks":results,"report":report}
    elif action in {"incidents","incident"}:
        manager=IncidentManager(SqlIncidentRepository(_database(args)))
        if action=="incidents":payload=[asdict(x) for x in manager.repository.list()]
        elif len(args.words)==2:payload=asdict(next((x for x in manager.repository.list() if x.incidentId==args.words[1]),None) or (_ for _ in ()).throw(ValueError("incidencia no encontrada")))
        elif len(args.words)>=3:payload=asdict(manager.acknowledge(args.words[1]) if words[2]=="acknowledge" else manager.close(args.words[1]) if words[2]=="close" else (_ for _ in ()).throw(ValueError("acción de incidencia no válida")))
    elif action=="configure":
        config=load_config();monitor=dict(config.get("monitor",{}));mode=words[1] if len(words)>1 else args.mode
        if mode=="temporary":mode="diagnostic"
        monitor.update({"enabled":True,"mode":mode,"authority":args.authority})
        if args.profile:monitor["profile"]=args.profile
        if args.duration:monitor["duration"]=args.duration
        if args.workers:monitor["workers"]=args.workers
        if args.timeout:monitor["timeout"]=args.timeout
        validate_monitor_settings(monitor);config["monitor"]=monitor;save_config(config);payload={"monitor":monitor}
    elif action=="profile":
        manager=ProfileManager(application_path(args.profiles));verb=words[1] if len(words)>1 else "list"
        if verb=="list":payload=[asdict(x) for x in manager.list()]
        elif verb=="show":payload=asdict(manager.profile(words[2]))
        elif verb in {"create","update"}:
            name=words[2];base=manager.profile(name) if verb=="update" else MonitorProfile(name)
            profile=MonitorProfile(name,parse_duration(args.presence) if args.presence else base.presence_interval,base.critical_interval,parse_duration(args.discovery) if args.discovery else base.discovery_interval,parse_duration(args.services) if args.services else base.services_interval,parse_duration(args.deep) if args.deep else base.deep_interval,args.timeout or base.timeout,args.workers or base.workers,base.jitter,base.failure_threshold,base.recovery_threshold);manager.save(profile);payload=asdict(profile)
        elif verb=="delete":manager.delete(words[2]);payload={"deleted":words[2]}
        else:raise ValueError("acción de perfil no válida")
    elif action in {"assign","unassign","assignments"}:
        manager=AssignmentManager(application_path(args.assignments_store))
        if action=="assignments":payload=[asdict(x) for x in manager.list()]
        elif action=="unassign":manager.unassign(args.words[1]);payload={"deleted":args.words[1]}
        else:
            selector=args.words[1] if len(args.words)>1 else "";group=args.group or "";device_id=""
            if not group:device_id=DeviceDatabase(load_config()["database"]).resolve(selector).device_id
            checks=[]
            for item in args.check:
                kind,_,argument=item.partition(":");spec={"type":"port" if kind=="port" else kind,"interval":args.every or "60s"}
                if argument:spec["args"]={"port":int(argument)}
                checks.append(spec)
            payload=asdict(manager.assign(selector or group,device_id=device_id,group=group,priority=args.priority,profile=args.profile or "",checks=checks))
    elif action=="report" or action=="session" and len(words)>1 and words[1] in {"list","report"}:
        with MonitorDatabase(application_path(args.monitor_db)) as database:
            repository=SqlSessionRepository(database);builder=ReportBuilder(database,repository,SqlIncidentRepository(database),load_config().get("activeProject"))
            if action=="session" and words[1]=="list":payload=[asdict(x) for x in repository.list()]
            else:
                rows=repository.list();identity=words[2] if action=="session" else words[1] if len(words)>1 and words[1]!="latest" else rows[0].sessionId
                report=builder.build(repository.get(identity));payload=report if args.json else {"report":builder.human(report),"data":report}
    elif action=="service":payload=asdict(_platform().service(words[1] if len(words)>1 else "status",confirm=args.yes,executable=sys.executable,project=args.project or load_config().get("activeProject") or ""))
    elif action=="foreground":
        active=sessions.repository.active()
        if not active:raise RuntimeError("no hay una sesión pendiente para foreground")
        class Assignments:
            def targets(self,_session):
                inventory=DeviceDatabase(load_config()["database"]);configured=AssignmentManager(application_path(args.assignments_store)).list()
                if not configured:return inventory.load()
                selected=[]
                for assignment in configured:
                    if assignment.deviceId:
                        try:selected.append(inventory.resolve(assignment.deviceId))
                        except ValueError:continue
                    else:selected.extend(device for device in inventory.load() if assignment.group.casefold() in (group.casefold() for group in device.groups))
                return list({device.device_id:device for device in selected}.values())
        stop_event=threading.Event()
        def stopping(*_):stop_event.set()
        signal.signal(signal.SIGTERM,stopping)
        if hasattr(signal,"SIGINT"):signal.signal(signal.SIGINT,stopping)
        database=sessions.repository.db;service=MonitorService(config=__import__('app.monitor.configuration',fromlist=['ConfigProvider']).ConfigProvider(),assignments=Assignments(),metrics=__import__('app.monitor.database',fromlist=['MetricsStore']).MetricsStore(database),sessions=sessions.repository,incidents=SqlIncidentRepository(database),reports=ReportBuilder(database,sessions.repository,SqlIncidentRepository(database),load_config().get("activeProject")))
        from app.plugins.manager import get_plugin_manager
        get_plugin_manager().monitor_service=service
        with SingletonLock(application_path(args.lock)):
            service.start(active)
            try:service.foreground(stop_event=stop_event)
            finally:service.stop("cancelled" if stop_event.is_set() else "completed")
        payload={"status":"completed","sessionId":active.sessionId}
    elif action=="ping":
        inventory=DeviceDatabase(load_config()["database"]);targets=_targets(inventory,args.words[1] if len(args.words)>1 else None,args.group)
        interval=parse_duration(args.interval or "2s");span=parse_duration(args.duration or "10m")
        session=sessions.repository.active();owned=False
        if not session:session=sessions.start(platform.node() or "manager",str(load_config().get("activeProject") or "-"),mode="diagnostic",authority="observe",duration=span);owned=True
        try:payload=ping_targets(targets,MetricsStore(sessions.repository.db),session.sessionId,interval=interval,duration=span,timeout=float(load_config().get("timeout",.8)))
        except KeyboardInterrupt:payload={"status":"cancelled","samples":0}
        if owned:session.status="cancelled" if payload["status"]=="cancelled" else "completed";sessions.repository.save(session)
    elif action=="scan":
        scan_type=args.type or "presence"
        if scan_type=="smb":
            manager=__import__('app.plugins.manager',fromlist=['get_plugin_manager']).get_plugin_manager();plugin=manager.get("lanctl.discovery.windows-smb") if "lanctl.discovery.windows-smb" in {x.manifest.plugin_id for x in manager.list()} else None
            if not plugin or plugin.state.value!="ENABLED":payload={"status":"unsupported","operationId":"monitor.scan.smb","message":"El proveedor SMB no está habilitado"}
            else:
                from app.plugins.smb_runtime import SMBService
                targets=_targets(DeviceDatabase(load_config()["database"]),args.words[1] if len(args.words)>1 else None,args.group);service=SMBService();payload={"status":"completed","results":[service.inspect(target,timeout=float(load_config().get("timeout",.8)))[0] for target in targets]}
        else:
            targets=_targets(DeviceDatabase(load_config()["database"]),args.words[1] if len(args.words)>1 else None,args.group);every=parse_duration(args.every) if args.every else 1;span=parse_duration(args.duration) if args.duration else 0;results=[]
            try:BoundedRunner().run(lambda:results.extend(scan_target(target,scan_type,float(load_config().get("timeout",.8)),int(load_config().get("workers",32))) for target in targets) or True,interval=every,duration=span)
            except KeyboardInterrupt:payload={"status":"cancelled","results":results}
            else:payload={"status":"completed","type":scan_type,"results":results}
    elif action=="identify":
        inventory=DeviceDatabase(load_config()["database"]);timeout=min(float(load_config().get("timeout",.8)),.5 if args.fast else 2)
        if len(args.words)>1:targets=[inventory.resolve(args.words[1])]
        elif args.unknown:
            from app.services.lan_scanner import LanScanner,resolve_network
            config=load_config();scanner=LanScanner(resolve_network(config.get("range")),min(int(config.get("workers",32)),64),timeout,int(config.get("maxHosts",4096)),config.get("scanOrder","ascending"))
            discovered=scanner.scan(include_unknown=True,resolve_names=not args.fast,discovery="hybrid",include_arp_cache=True)
            known_macs={device.mac.casefold() for device in inventory.load() if device.mac};targets=[device for device in discovered if not device.mac or device.mac.casefold() not in known_macs]
        else:targets=inventory.load()
        results=[identify_target(target,timeout) for target in targets]
        if args.unknown:results=[x for x in results if x["confidence"] in {"unknown","conflict","medium"}]
        payload={"status":"completed","operationId":"monitor.network.identify","results":results}
    elif action=="health":
        selector=args.words[1] if len(args.words)>1 else None;database=sessions.repository.db
        if selector:
            device=DeviceDatabase(load_config()["database"]).resolve(selector);state=database.execute("SELECT * FROM device_state WHERE device_id=?",(device.device_id,)).fetchone();samples=database.execute("SELECT COUNT(*) samples,AVG(presence)*100 availability,MIN(latency_ms) latencyMin,AVG(latency_ms) latencyAvg,MAX(latency_ms) latencyMax FROM samples WHERE device_id=?",(device.device_id,)).fetchone();incidents=[dict(x) for x in database.execute("SELECT * FROM incidents WHERE device_id=? AND status IN ('open','acknowledged')",(device.device_id,))];payload={"deviceId":device.device_id,"state":dict(state) if state else None,"metrics":dict(samples),"incidents":incidents}
        else:
            from app.monitor.reports import monitor_view
            payload=monitor_view(database)
    elif action=="events":
        def recent():return [event.to_dict() for event in HistoryService().query(source="lanctl.monitor",limit=100,reverse=True)]
        if not args.follow:payload={"status":"completed","events":recent()}
        else:
            seen=set();events=[]
            try:
                while True:
                    for event in recent():
                        if event["eventId"] not in seen:seen.add(event["eventId"]);events.append(event);print(json.dumps(event,ensure_ascii=False),flush=True)
                    time.sleep(1)
            except KeyboardInterrupt:payload={"status":"cancelled","events":events}
    elif action=="restart":
        active=sessions.repository.active();state=SingletonLock(application_path(args.lock)).status()
        if not active or not state.get("running"):payload={"status":"not-running","message":"No hay un monitor activo que reiniciar"}
        else:
            old_pid=state["pid"];os.kill(old_pid,signal.SIGTERM);deadline=time.monotonic()+5
            while time.monotonic()<deadline and SingletonLock(application_path(args.lock)).status().get("running"):time.sleep(.1)
            if SingletonLock(application_path(args.lock)).status().get("running"):payload={"status":"error","message":"El proceso monitor no se detuvo dentro del límite"}
            else:
                replacement=sessions.start(active.managerId,active.projectId,active.network,active.interface,active.localIp,active.mode,active.authority,None)
                command=[sys.executable,str(Path(__file__).resolve().parents[2]/"main.py"),"virtual","monitor","foreground","--monitor-db",args.monitor_db,"--profiles",args.profiles,"--assignments-store",args.assignments_store,"--lock",args.lock];flags=getattr(subprocess,"CREATE_NO_WINDOW",0) if platform.system()=="Windows" else 0;process=subprocess.Popen(command,creationflags=flags,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);payload={"status":"restarted","previousPid":old_pid,"processId":process.pid,"sessionId":replacement.sessionId}
    else:raise ValueError("acción monitor no válida")
    print(json.dumps(payload,indent=2,ensure_ascii=False) if args.json or isinstance(payload,(dict,list)) else payload)
    database=getattr(sessions.repository,"db",None)
    if database:database.close()
    return 0 if not isinstance(payload,dict) or payload.get("status")!="unsupported" else 1

def _platform():
    if platform.system()=="Linux":
        from app.platform.linux import LinuxPlatform;return LinuxPlatform()
    if platform.system()=="Windows":
        from app.platform.windows import WindowsPlatform;return WindowsPlatform()
    from app.platform.base import PlatformAdapter;return PlatformAdapter()

def _targets(database,selector=None,group=None):
    if selector:return [database.resolve(selector)]
    rows=database.load()
    if group:rows=[device for device in rows if group.casefold() in (item.casefold() for item in device.groups)]
    if not rows:raise ValueError("no hay dispositivos para la operación monitor")
    return rows
