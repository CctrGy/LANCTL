from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from lanctl.core.config import load_config
from lanctl.core.credentials import CredentialStore
from lanctl.core.database import DeviceDatabase
from lanctl.core.plugin_storage import PluginStorage
from lanctl.core.plugins.smb_runtime import SMBError, SMBService
from lanctl.shared.i18n import t

ACTIONS = (
    "scan",
    "info",
    "shares",
    "open",
    "printers",
    "workgroups",
    "connect",
    "disconnect",
    "status",
    "printer",
)


def register_smb_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "smb", help=t("LANCTL.UI.HELP.DISCOVER_AND_OPEN_WINDOWS_SMB_RESOURCES")
    )
    command.add_argument(
        "name", nargs="?", help=t("LANCTL.UI.HELP.SERVER_DEVICE_NO_ACTION_DEFAULTS_TO_INFO")
    )
    command.add_argument(
        "action",
        nargs="?",
        help=t(
            "LANCTL.UI.HELP.SCAN_INFO_SHARES_OPEN_PRINTERS_WORKGROUPS_CONNECT_DISCONNECT_STATUS_OR_PRINTER"
        ),
    )
    command.add_argument("resource", nargs="?", help=t("LANCTL.UI.HELP.SHARED_FOLDER_OR_PRINTER"))
    command.add_argument(
        "resource_action",
        nargs="?",
        choices=("open", "queue", "connect"),
        help=t("LANCTL.UI.HELP.PRINTER_ACTION"),
    )
    command.add_argument(
        "--network",
        action="store_true",
        help=t("LANCTL.UI.HELP.EXAMINE_THE_ENTIRE_LANCTL_INVENTORY"),
    )
    command.add_argument("--group", help=t("LANCTL.UI.HELP.LIMIT_THE_SCAN_TO_A_LANCTL_GROUP"))
    command.add_argument(
        "--timeout",
        type=float,
        default=config["timeout"],
        help=t("LANCTL.UI.HELP.TCP_PROBE_TIMEOUT"),
    )
    command.add_argument(
        "--workers",
        type=int,
        default=min(32, int(config["workers"])),
        help=t("LANCTL.UI.HELP.MAXIMUM_NUMBER_OF_CONCURRENT_PROBES"),
    )
    command.add_argument(
        "--anonymous",
        action="store_true",
        help=t("LANCTL.UI.HELP.DO_NOT_LOAD_ASSOCIATED_CREDENTIALS"),
    )
    command.add_argument(
        "--include-system",
        action="store_true",
        help=t("LANCTL.UI.HELP.INCLUDE_ADMINISTRATIVE_AND_SPECIAL_RESOURCES"),
    )
    command.add_argument(
        "--dry-run",
        action="store_true",
        help=t("LANCTL.UI.HELP.SHOW_THE_PLAN_WITHOUT_AUTHENTICATING_OPENING_OR_CHANGING_ANYTHING"),
    )
    command.add_argument(
        "--yes", action="store_true", help=t("LANCTL.UI.HELP.CONFIRM_A_PRINTER_CONNECTION")
    )
    command.add_argument(
        "--json", action="store_true", help=t("LANCTL.UI.HELP.OUTPUT_STRUCTURED_JSON")
    )
    command.add_argument(
        "--database", default=config["database"], help=t("LANCTL.UI.HELP.INVENTORY_JSON_FILE")
    )
    command.add_argument(
        "--store", default=config["credentials"], help=t("LANCTL.UI.HELP.DPAPI_CREDENTIAL_STORE")
    )
    command.add_argument(
        "--storage",
        default=config["smbStorage"],
        help=t("LANCTL.UI.HELP.PLUGIN_OBSERVATIONS_DIRECTORY"),
    )
    command.set_defaults(handler=run_smb)


def _grammar(args):
    name, action = args.name, args.action
    if name and name.casefold() in ACTIONS:
        action, name = name.casefold(), action
    elif action:
        action = action.casefold()
    else:
        action = "info" if name else "scan"
    if action not in ACTIONS:
        raise ValueError(f"acción SMB no soportada: {action}")
    return name, action


def _credential(device, args):
    reference = device.credentials.get("smb")
    if args.anonymous or not reference:
        return None
    value = CredentialStore(args.store).get(reference)
    if value.get("deviceId") != device.device_id or value.get("protocol") != "smb":
        raise PermissionError("la credencial SMB no pertenece al dispositivo autorizado")
    return {"username": value["username"], "password": value["password"]}


def run_smb(args: argparse.Namespace) -> int:
    name, action = _grammar(args)
    database = DeviceDatabase(args.database)
    service = SMBService()
    storage = PluginStorage(args.storage, "lanctl.discovery.windows-smb")
    try:
        if action == "workgroups":
            groups = sorted(
                {
                    str(o.get("smb", {}).get("workgroup") or o.get("smb", {}).get("domain") or "")
                    for o in storage.load()["observations"].values()
                }
                - {""}
            )
            return _emit(args, {"workgroups": groups})
        if action == "scan":
            devices = database.load()
            if name:
                devices = [database.resolve(name)]
            if args.group:
                devices = [d for d in devices if d.in_group(args.group)]
            rows = []
            errors = []
            observations = {}

            def inspect(device):
                return device, service.inspect(
                    device,
                    timeout=args.timeout,
                    include_system=args.include_system,
                    credential=_credential(device, args),
                )

            with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 64))) as executor:
                futures = {executor.submit(inspect, device): device for device in devices}
                for future in as_completed(futures):
                    device = futures[future]
                    try:
                        _, (observation, trace) = future.result()
                        observations[device.device_id] = observation
                        rows.append({**observation, "trace": trace})
                    except SMBError as error:
                        errors.append(
                            {
                                "deviceId": device.device_id,
                                "host": device.name or device.ip,
                                "state": error.state,
                                "error": {
                                    "code": error.code,
                                    "origin": "smb.scan",
                                    "message": str(error),
                                },
                            }
                        )
                    except OSError as error:
                        errors.append(
                            {
                                "deviceId": device.device_id,
                                "host": device.name or device.ip,
                                "state": "error",
                                "error": {
                                    "code": "SMB.SCAN.ERROR",
                                    "origin": "smb.scan",
                                    "message": str(error),
                                },
                            }
                        )
            storage.put_observations(observations)
            return _emit(
                args,
                {
                    "servers": rows,
                    "errors": errors,
                    "summary": {"processed": len(devices), "available": len(rows)},
                },
            )
        if not name:
            raise ValueError(f"smb {action} requiere un servidor")
        device = database.resolve(name)
        observations = storage.load()["observations"]
        observation = observations.get(device.device_id)
        if action in {"info", "shares", "printers", "status"}:
            if not observation:
                observation, _ = service.inspect(
                    device,
                    timeout=args.timeout,
                    include_system=args.include_system,
                    credential=_credential(device, args),
                )
                storage.put_observation(device.device_id, observation)
            if action == "info" or action == "status":
                payload = observation
            else:
                wanted = "printer" if action == "printers" else None
                resources = [
                    r for r in observation["smb"]["shares"] if wanted is None or r["type"] == wanted
                ]
                payload = {
                    "deviceId": device.device_id,
                    "host": observation["host"],
                    "resources": resources,
                }
            return _emit(args, payload)
        if action == "open":
            if not args.resource:
                raise ValueError("indica la carpeta compartida")
            return _emit(
                args,
                service.open_share(
                    device.name or device.ip,
                    args.resource,
                    dry_run=args.dry_run,
                    credential=_credential(device, args),
                ),
            )
        if action == "printer":
            if not args.resource:
                raise ValueError("indica la impresora")
            return _emit(
                args,
                service.printer(
                    device.name or device.ip,
                    args.resource,
                    args.resource_action or "open",
                    yes=args.yes,
                    credential=_credential(device, args),
                ),
            )
        if action == "connect":
            credential = _credential(device, args)
            if not credential:
                raise SMBError(
                    "SMB.AUTH.REQUIRED",
                    "el dispositivo no tiene credencial SMB",
                    state="authentication-required",
                )
            service.native.connect(
                device.name or device.ip, credential["username"], credential["password"]
            )
            return _emit(args, {"status": "connected", "host": device.name or device.ip})
        if action == "disconnect":
            service.native.disconnect(device.name or device.ip)
            return _emit(args, {"status": "disconnected", "host": device.name or device.ip})
    except SMBError as error:
        if args.json:
            print(
                json.dumps(
                    {
                        "status": error.state,
                        "error": {"code": error.code, "origin": "smb", "message": str(error)},
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 2
        raise ValueError(str(error)) from error
    return 0


def _emit(args, payload):
    print(
        json.dumps(payload, ensure_ascii=False, indent=2)
        if args.json or isinstance(payload, dict)
        else payload
    )
    return 0
