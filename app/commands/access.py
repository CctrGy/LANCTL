from __future__ import annotations
import base64,getpass,hashlib,json,subprocess,sys,platform,os,signal,ssl
from dataclasses import asdict
from pathlib import Path
from app.access.keys import generate_certificate,generate_host_key
from app.access.models import PERMISSIONS,ROLE_PERMISSIONS
from app.access.service import AccessService
from app.core.config import load_config
from app.core.paths import application_path

def register_access_command(commands):
    config=load_config();command=commands.add_parser("access",help="Configura acceso remoto LAN seguro por SSH y HTTPS.")
    command.add_argument("words",nargs="*",help="init, status, enable, disable, configure, user, role, session, web o certificate.")
    command.add_argument("--bind");command.add_argument("--cidr");command.add_argument("--port",type=int);command.add_argument("--password-auth",choices=("on","off"));command.add_argument("--role",action="append",default=[]);command.add_argument("--ssh-key",action="append",default=[]);command.add_argument("--expires");command.add_argument("--permission",action="append",default=[]);command.add_argument("--certificate");command.add_argument("--private-key");command.add_argument("--common-name");command.add_argument("--yes",action="store_true");command.add_argument("--json",action="store_true")
    command.add_argument("--config",default=config["accessConfig"],help="Configuración remota separada.");command.add_argument("--users",default=config["accessUsers"],help="Almacén de usuarios remotos.");command.set_defaults(handler=run_access)
    for item in command._actions:
        if item.help is None:item.help="Opción de acceso remoto."
def run_access(args):
    service=AccessService(application_path(args.config),application_path(args.users));words=args.words;action=words[0].casefold() if words else "status"
    if action=="init":payload=service.initialize()
    elif action=="setup-wizard":payload=_setup_wizard(service)
    elif action=="status":payload=service.status()
    elif action in {"enable","disable"}:
        if len(words)!=2:raise ValueError(f"access {action} requiere ssh o https")
        protocol=words[1].casefold()
        if action=="enable":
            payload=service.enable(protocol);process=_start_service_process(service,protocol);payload={**payload,"status":"starting","processId":process.pid}
        else:
            config=service.config();pid=config[protocol].get("processId")
            if pid:
                from app.monitor.lifecycle import _process_alive
                try:_process_alive(int(pid));os.kill(int(pid),signal.SIGTERM)
                except OSError:pass
            payload=service.disable(protocol);config=service.config();config[protocol].pop("processId",None);service.save_config(config)
    elif action=="configure":
        if len(words)!=2 or not args.bind or not args.cidr:raise ValueError("usa access configure ssh|https --bind IP --cidr CIDR")
        payload=service.configure(words[1].casefold(),bind=args.bind,cidr=args.cidr,port=args.port or (2222 if words[1].casefold()=="ssh" else 8443),password_authentication=args.password_auth=="on" if args.password_auth else None)
    elif action=="user":payload=_user(service,args,words[1:])
    elif action=="role":payload=_role(service,args,words[1:])
    elif action=="session":
        verb=words[1].casefold() if len(words)>1 else "list"
        payload=[_public_session(x) for x in service.store.sessions()] if verb=="list" else _public_session(service.auth.revoke(words[2])) if verb=="revoke" else (_ for _ in ()).throw(ValueError("acción de sesión no válida"))
    elif action=="web" and len(words)>2 and words[1].casefold()=="pair":payload={"code":service.auth.create_pairing(service.auth.user(words[2]).userId),"expiresIn":300}
    elif action=="certificate":
        cert,key=generate_certificate(args.certificate or application_path("data/lc/access/tls.crt"),args.private_key or application_path("data/lc/access/tls.key"),args.common_name or args.bind or "lanctl.local");config=service.config();config["https"].update({"certificate":cert,"privateKey":key});service.save_config(config);payload={"certificate":cert,"warning":"Certificado autofirmado; verifica su huella"}
    elif action=="rotate-host-key":
        if not args.yes:raise ValueError("rotate-host-key requiere --yes")
        path=generate_host_key(application_path("data/lc/access/ssh_host_ed25519_key"));config=service.config();config["ssh"]["hostKey"]=path;service.save_config(config);payload={"hostKey":path,"warning":"Los clientes deberán confirmar la nueva huella"}
    elif action=="serve":
        protocol=words[1].casefold();config=service.config();settings=config[protocol]
        if not settings.get("enabled"):raise RuntimeError(f"{protocol} no está habilitado")
        if protocol=="ssh":
            from app.access.ssh_server import SshAccessServer
            server=SshAccessServer(settings["bind"],settings["port"],settings["cidr"],settings["hostKey"],service.auth,settings.get("passwordAuthentication",False))
        else:
            from app.access.https_server import HttpsAccessServer
            server=HttpsAccessServer(settings["bind"],settings["port"],settings["cidr"],settings["certificate"],settings["privateKey"],service.auth,service.status)
        try:server.serve_forever()
        except KeyboardInterrupt:pass
        finally:server.stop()
        payload={"status":"stopped","protocol":protocol}
    elif action in {"recover","reset"}:raise PermissionError("la recuperación requiere ejecución local específica; no existe puerta trasera")
    else:raise ValueError("acción access no válida")
    print(json.dumps(payload,indent=2,ensure_ascii=False));return 0
def _user(service,args,words):
    verb=words[0].casefold() if words else "list"
    if verb=="list":return [{"userId":x.userId,"username":x.username,"roles":x.roles,"enabled":x.enabled,"expiresAt":x.expiresAt,"lockedUntil":x.lockedUntil} for x in service.store.users()]
    if verb=="show":
        x=service.auth.user(words[1]);return {"userId":x.userId,"username":x.username,"roles":x.roles,"enabled":x.enabled,"expiresAt":x.expiresAt,"sshKeys":x.sshKeys}
    if verb=="add":
        password=None
        if args.password_auth=="on":
            password=getpass.getpass("Contraseña web: ");confirmation=getpass.getpass("Repite la contraseña web: ")
            if password!=confirmation:raise ValueError("las contraseñas no coinciden")
        keys=[Path(path).read_text(encoding="utf-8").strip() for path in args.ssh_key];return asdict(service.auth.add_user(words[1],args.role or ["viewer"],password,keys,args.expires))
    user=service.auth.user(words[1])
    if verb in {"enable","disable"}:
        user.enabled=verb=="enable";service.store.save_user(user);service._audit(f"access.user.{verb}d",user,"success");return {verb+"d":user.userId}
    if verb=="rotate-password":
        password=getpass.getpass("Nueva contraseña web: ");confirmation=getpass.getpass("Repite la contraseña web: ")
        if password!=confirmation:raise ValueError("las contraseñas no coinciden")
        from app.access.auth import hash_password
        user.passwordHash=hash_password(password);service.store.save_user(user);service._audit("access.user.authenticator.rotated",user,"success");return {"rotated":user.userId}
    if verb=="delete":service.store.delete_user(user.userId);service._audit("access.user.deleted",user,"success");return {"deleted":user.userId}
    raise ValueError("acción de usuario no válida")
def _public_session(session):
    return {"sessionId":session.sessionId,"userId":session.userId,"authenticator":session.authenticator,"sourceIp":session.sourceIp,"createdAt":session.createdAt,"expiresAt":session.expiresAt,"revokedAt":session.revokedAt}
def _lanctl_command(*arguments):
    return [sys.executable,*arguments] if getattr(sys,"frozen",False) else [sys.executable,str(Path(__file__).resolve().parents[2]/"main.py"),*arguments]
def _start_service_process(service,protocol):
    command=_lanctl_command("access","serve",protocol,"--config",str(service.config_path),"--users",str(service.store.path));flags=getattr(subprocess,"CREATE_NO_WINDOW",0) if platform.system()=="Windows" else 0
    process=subprocess.Popen(command,creationflags=flags,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);config=service.config();config[protocol]["processId"]=process.pid;service.save_config(config);return process
def _setup_wizard(service):
    """Asistente exclusivamente local; nunca recibe secretos mediante argumentos."""
    service.initialize();config=service.config();created_user=None;started=[];firewall_rules=[]
    config["ssh"]["enabled"]=False;config["https"]["enabled"]=False;service.save_config(config)
    try:
        print("ACCESO REMOTO LANCTL (SSH/HTTPS permanecen apagados hasta la confirmación final)")
        bind=input("IPv4 de la interfaz LAN: ").strip();cidr=input("CIDR permitido (ej. 192.168.1.0/24): ").strip()
        ssh_port=int(input("Puerto SSH [2222]: ").strip() or "2222");https_port=int(input("Puerto HTTPS [8443]: ").strip() or "8443")
        service.configure("ssh",bind=bind,cidr=cidr,port=ssh_port,password_authentication=False)
        service.configure("https",bind=bind,cidr=cidr,port=https_port)
        username=input("Cuenta administradora: ").strip();public_key_path=input("Clave pública SSH (ruta, opcional): ").strip()
        keys=[Path(public_key_path).read_text(encoding="utf-8").strip()] if public_key_path else []
        use_web=input("¿Crear autenticador web? [s/N]: ").strip().casefold() in {"s","si","sí","y","yes"}
        password=None
        if use_web:
            password=getpass.getpass("Contraseña web: ");confirmation=getpass.getpass("Repite la contraseña web: ")
            if password!=confirmation:raise ValueError("las contraseñas no coinciden")
        created_user=service.auth.add_user(username,["administrator"],password,keys)
        host_key=generate_host_key(application_path("data/lc/access/ssh_host_ed25519_key"))
        certificate,private_key=generate_certificate(application_path("data/lc/access/tls.crt"),application_path("data/lc/access/tls.key"),bind)
        config=service.config();config["ssh"]["hostKey"]=host_key;config["https"].update({"certificate":certificate,"privateKey":private_key});service.save_config(config)
        enable_ssh=input("¿Activar SSH restringido? [s/N]: ").strip().casefold() in {"s","si","sí","y","yes"}
        enable_https=input("¿Activar HTTPS? [s/N]: ").strip().casefold() in {"s","si","sí","y","yes"}
        manage_firewall=input("¿Crear reglas de firewall limitadas al CIDR? [s/N]: ").strip().casefold() in {"s","si","sí","y","yes"}
        if input("¿Confirmas el bind/CIDR y la activación indicada? [s/N]: ").strip().casefold() not in {"s","si","sí","y","yes"}:raise PermissionError("configuración cancelada")
        if enable_ssh:service.enable("ssh");started.append(_start_service_process(service,"ssh"))
        if enable_https:service.enable("https");started.append(_start_service_process(service,"https"))
        if manage_firewall:
            from app.access.firewall import FirewallManager
            manager=FirewallManager()
            if enable_ssh:firewall_rules.append(manager.add("ssh",bind,cidr,ssh_port))
            if enable_https:firewall_rules.append(manager.add("https",bind,cidr,https_port))
            config=service.config();config["firewall"]={"managed":True,"rules":[rule.__dict__ for rule in firewall_rules]};service.save_config(config)
        ssh_fingerprint=_ssh_host_fingerprint(host_key);cert_fingerprint=_certificate_fingerprint(certificate)
        return {"ssh":{"enabled":enable_ssh,"bind":bind,"port":ssh_port,"fingerprint":ssh_fingerprint},"https":{"enabled":enable_https,"url":f"https://{bind}:{https_port}","fingerprint":cert_fingerprint},"firewall":{"managed":bool(firewall_rules),"cidr":cidr}}
    except Exception:
        if firewall_rules:
            from app.access.firewall import FirewallManager
            manager=FirewallManager()
            for rule in reversed(firewall_rules):
                try:manager.remove(rule)
                except (OSError,RuntimeError):pass
        for process in started:
            try:process.terminate()
            except OSError:pass
        config=service.config();config["ssh"]["enabled"]=False;config["https"]["enabled"]=False;service.save_config(config)
        if created_user is not None:service.store.delete_user(created_user.userId)
        raise
def _ssh_host_fingerprint(path):
    import paramiko
    key=paramiko.Ed25519Key.from_private_key_file(str(path));return "SHA256:"+base64.b64encode(hashlib.sha256(key.asbytes()).digest()).decode().rstrip("=")
def _certificate_fingerprint(path):
    pem=Path(path).read_text(encoding="ascii");der=ssl.PEM_cert_to_DER_cert(pem);return "SHA256:"+hashlib.sha256(der).hexdigest().upper()
def _role(service,args,words):
    verb=words[0].casefold() if words else "list";value=service.store.load()
    if verb=="list":return {**{k:sorted(v) for k,v in ROLE_PERMISSIONS.items()},**value.get("roles",{})}
    if verb in {"create","update"}:
        unknown=set(args.permission)-PERMISSIONS
        if unknown:raise ValueError("permisos desconocidos: "+", ".join(sorted(unknown)))
        value.setdefault("roles",{})[words[1]]=sorted(set(args.permission));service.store.save(value);return {"role":words[1],"permissions":sorted(set(args.permission))}
    if verb=="delete":value.setdefault("roles",{}).pop(words[1],None);service.store.save(value);return {"deleted":words[1]}
    raise ValueError("acción de rol no válida")
