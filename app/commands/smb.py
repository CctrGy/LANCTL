from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.core.config import load_config
from app.core.credentials import CredentialStore
from app.core.database import DeviceDatabase
from app.core.plugin_storage import PluginStorage
from app.plugins.smb_runtime import SMBError, SMBService


ACTIONS = ("scan", "info", "shares", "open", "printers", "workgroups", "connect", "disconnect", "status", "printer")


def register_smb_command(commands: argparse._SubParsersAction) -> None:
    config=load_config(); command=commands.add_parser("smb", help="Descubre y abre recursos SMB de Windows.")
    command.add_argument("name", nargs="?", help="Servidor/dispositivo (sin acción equivale a info).")
    command.add_argument("action", nargs="?", help="scan, info, shares, open, printers, workgroups, connect, disconnect, status o printer.")
    command.add_argument("resource", nargs="?", help="Carpeta o impresora compartida.")
    command.add_argument("resource_action", nargs="?", choices=("open","queue","connect"), help="Acción sobre la impresora.")
    command.add_argument("--network", action="store_true", help="Examina todo el inventario LANCTL.")
    command.add_argument("--group", help="Limita el escaneo a un grupo LANCTL."); command.add_argument("--timeout", type=float, default=config["timeout"], help="Tiempo máximo del probe TCP.")
    command.add_argument("--workers", type=int, default=min(32, int(config["workers"])), help="Número máximo de probes concurrentes.")
    command.add_argument("--anonymous", action="store_true", help="No carga credenciales asociadas."); command.add_argument("--include-system", action="store_true", help="Incluye recursos administrativos y especiales.")
    command.add_argument("--dry-run", action="store_true", help="Muestra el plan sin autenticar, abrir ni mutar."); command.add_argument("--yes", action="store_true", help="Confirma una conexión de impresora.")
    command.add_argument("--json", action="store_true", help="Emite JSON estructurado."); command.add_argument("--database", default=config["database"], help="Archivo JSON del inventario.")
    command.add_argument("--store", default=config["credentials"], help="Almacén DPAPI de credenciales."); command.add_argument("--storage", default=config["smbStorage"], help="Directorio de observaciones de plugins.")
    command.set_defaults(handler=run_smb)


def _grammar(args):
    name, action = args.name, args.action
    if name and name.casefold() in ACTIONS:
        action, name = name.casefold(), action
    elif action: action=action.casefold()
    else: action="info" if name else "scan"
    if action not in ACTIONS: raise ValueError(f"acción SMB no soportada: {action}")
    return name, action


def _credential(device, args):
    reference=device.credentials.get("smb")
    if args.anonymous or not reference: return None
    value=CredentialStore(args.store).get(reference)
    if value.get("deviceId") != device.device_id or value.get("protocol") != "smb":
        raise PermissionError("la credencial SMB no pertenece al dispositivo autorizado")
    return {"username":value["username"],"password":value["password"]}


def run_smb(args: argparse.Namespace) -> int:
    name, action=_grammar(args); database=DeviceDatabase(args.database); service=SMBService(); storage=PluginStorage(args.storage,"lanctl.discovery.windows-smb")
    try:
        if action == "workgroups":
            groups=sorted({str(o.get("smb",{}).get("workgroup") or o.get("smb",{}).get("domain") or "")
                           for o in storage.load()["observations"].values()} - {""})
            return _emit(args,{"workgroups":groups})
        if action == "scan":
            devices=database.load()
            if name: devices=[database.resolve(name)]
            if args.group: devices=[d for d in devices if args.group.upper() in d.groups]
            rows=[]; errors=[]
            def inspect(device):
                return device, service.inspect(device,timeout=args.timeout,include_system=args.include_system,credential=_credential(device,args))
            with ThreadPoolExecutor(max_workers=max(1,min(args.workers,64))) as executor:
              futures={executor.submit(inspect,device):device for device in devices}
              for future in as_completed(futures):
                device=futures[future]
                try:
                    _, (observation, trace)=future.result()
                    storage.put_observation(device.device_id,observation); rows.append(observation); rows[-1]["trace"]=trace
                except SMBError as error:
                    errors.append({"deviceId":device.device_id,"host":device.name or device.ip,"state":error.state,
                                   "error":{"code":error.code,"origin":"smb.scan","message":str(error)}})
                except OSError as error:
                    errors.append({"deviceId":device.device_id,"host":device.name or device.ip,"state":"error",
                                   "error":{"code":"SMB.SCAN.ERROR","origin":"smb.scan","message":str(error)}})
            return _emit(args,{"servers":rows,"errors":errors,"summary":{"processed":len(devices),"available":len(rows)}})
        if not name: raise ValueError(f"smb {action} requiere un servidor")
        device=database.resolve(name); observations=storage.load()["observations"]; observation=observations.get(device.device_id)
        if action in {"info","shares","printers","status"}:
            if not observation:
                observation,_=service.inspect(device,timeout=args.timeout,include_system=args.include_system,credential=_credential(device,args)); storage.put_observation(device.device_id,observation)
            if action == "info" or action == "status": payload=observation
            else:
                wanted="printer" if action == "printers" else None
                resources=[r for r in observation["smb"]["shares"] if wanted is None or r["type"]==wanted]
                payload={"deviceId":device.device_id,"host":observation["host"],"resources":resources}
            return _emit(args,payload)
        if action == "open":
            if not args.resource: raise ValueError("indica la carpeta compartida")
            return _emit(args,service.open_share(device.name or device.ip,args.resource,dry_run=args.dry_run))
        if action == "printer":
            if not args.resource: raise ValueError("indica la impresora")
            return _emit(args,service.printer(device.name or device.ip,args.resource,args.resource_action or "open",yes=args.yes))
        if action == "connect":
            credential=_credential(device,args)
            if not credential: raise SMBError("SMB.AUTH.REQUIRED","el dispositivo no tiene credencial SMB",state="authentication-required")
            service.native.connect(device.name or device.ip,credential["username"],credential["password"])
            return _emit(args,{"status":"connected","host":device.name or device.ip})
        if action == "disconnect":
            service.native.disconnect(device.name or device.ip); return _emit(args,{"status":"disconnected","host":device.name or device.ip})
    except SMBError as error:
        if args.json: print(json.dumps({"status":error.state,"error":{"code":error.code,"origin":"smb","message":str(error)}},ensure_ascii=False,indent=2)); return 2
        raise ValueError(str(error)) from error
    return 0


def _emit(args, payload):
    print(json.dumps(payload,ensure_ascii=False,indent=2) if args.json or isinstance(payload,dict) else payload)
    return 0
