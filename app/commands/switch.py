from __future__ import annotations

import argparse
import os
import shlex
import sys
from collections.abc import Callable
from dataclasses import replace
import re

from colorama import Fore, Style

from app.cisco.adapters import FakeCiscoAdapter
from app.cisco.catalog import CATALOG
from app.cisco.context import CiscoContext
from app.cisco.executor import CiscoExecutor
from app.cisco.models import CommandPlan, Risk
from app.cisco.planner import CiscoPlanner
from app.cisco.profiles import PROFILE_PATH, load_profile
from app.core.config import load_config
from app.core.console import ok
from app.core.database import DeviceDatabase
from app.core.logger import write_log
from app.core.parser import colorize_help
from app.core.layout import fit_text, shrink_widths, terminal_columns


HELP = """Comandos Cisco gestionados:
  show COMANDO
  port list
  port label PUERTO NOMBRE
  port unlabel PUERTO
  port show [PUERTO] status|description|config|errors|vlan
  port set [PUERTO] description|speed|duplex VALOR
  port enable|disable|reset [PUERTO]
  start|stop|reset [PUERTO]
  save-config
  terminal

Opciones globales: --profile PERFIL --dry-run --yes
Esta fase utiliza un adaptador simulado y no conecta con el switch."""


def register_switch_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "switch",
        help="Planifica comandos Cisco filtrados, remapeados y clasificados.",
        description=HELP,
    )
    command.add_argument("selector", help="IP, MAC o alias del switch.")
    command.add_argument("--profile", help="Perfil Cisco que remapea los puertos.")
    command.add_argument(
        "--profiles",
        default=config.get("ciscoProfiles", str(PROFILE_PATH)),
        help="Archivo JSON que contiene los perfiles Cisco.",
    )
    command.add_argument(
        "--database",
        default=config["database"],
        help="Archivo JSON de elementos.",
    )
    command.add_argument("--dry-run", action="store_true", help="Solo muestra el plan.")
    command.add_argument("--yes", action="store_true", help="Confirma cambios sin preguntar.")
    command.add_argument(
        "arguments",
        nargs=argparse.REMAINDER,
        metavar="COMANDO",
        help="Acción Cisco gestionada que se quiere planificar.",
    )
    command.set_defaults(handler=run_switch)


def _profile_id(device, requested: str | None) -> str:
    options = device.protocol_options.get("cisco-cli", {})
    return requested or str(options.get("profile", "cisco-s300-24"))


def _device_profile(device, profile):
    labels = device.protocol_options.get("cisco-cli", {}).get("portLabels", {})
    if not isinstance(labels, dict):
        raise ValueError("portLabels del elemento debe ser un objeto")
    ports = tuple(
        replace(port, label=str(labels.get(port.id, port.label)))
        for port in profile.ports
    )
    return replace(profile, ports=ports)


def _extract_options(args: argparse.Namespace) -> list[str]:
    """Permite opciones LANCTL antes o después del selector con REMAINDER."""
    tokens = list(args.arguments)
    command: list[str] = []
    index = 0
    value_options = {"--profile": "profile", "--profiles": "profiles", "--database": "database"}
    while index < len(tokens):
        token = tokens[index]
        if token == "--dry-run":
            args.dry_run = True
        elif token == "--yes":
            args.yes = True
        elif token in value_options:
            if index + 1 >= len(tokens):
                raise ValueError(f"falta el valor de {token}")
            index += 1
            setattr(args, value_options[token], tokens[index])
        else:
            command.append(token)
        index += 1
    return command


def _print_ports(profile, selected=None) -> None:
    alias_width = max(5, *(len(",".join(port.aliases)) for port in profile.ports))
    native_width = max(6, *(len(port.native) for port in profile.ports))
    widths, stacked = shrink_widths(
        {"sel": 3, "id": 7, "alias": alias_width, "native": native_width, "label": max(5, *(len(port.label or "-") for port in profile.ports))},
        {"sel": 3, "id": 5, "alias": 5, "native": 6, "label": 5},
        ("sel", "id", "alias", "native", "label"), terminal_columns(),
        ("label", "alias", "native", "id"), gap=2,
    )
    if stacked:
        for index, port in enumerate(profile.ports):
            if index:
                print("-" * (terminal_columns() or 40))
            print(f"sel    : {'>' if selected and port.id == selected.id else '-'}")
            print(f"id     : {port.id}")
            print(f"alias  : {','.join(port.aliases)}")
            print(f"native : {port.native}")
            print(f"label  : {port.label or '-'}")
        return
    alias_width, native_width = widths["alias"], widths["native"]
    print(f"sel  {'id':<{widths['id']}}  {'alias':<{alias_width}}  {'native':<{native_width}}  label")
    print(f"---  {'-' * widths['id']}  {'-' * alias_width}  {'-' * native_width}  {'-' * widths['label']}")
    for port in profile.ports:
        aliases = ",".join(port.aliases)
        marker = " > " if selected and port.id == selected.id else "   "
        print(f"{marker}  {fit_text(port.id, widths['id']):<{widths['id']}}  {fit_text(aliases, alias_width):<{alias_width}}  {fit_text(port.native, native_width):<{native_width}}  {fit_text(port.label or '-', widths['label'])}")


def _paint_risk(risk: Risk) -> str:
    colors = {
        Risk.READ_ONLY: Fore.CYAN,
        Risk.CONFIG_CHANGE: Fore.YELLOW,
        Risk.DISRUPTIVE: Fore.RED + Style.BRIGHT,
        Risk.PERSIST_CONFIG: Fore.MAGENTA,
    }
    if not sys.stdout.isatty() or "NO_COLOR" in os.environ:
        return risk.value
    return f"{colors[risk]}{risk.value}{Style.RESET_ALL}"


def render_plan(plan: CommandPlan, simulated: bool = True) -> None:
    print(f"\n[PLAN CISCO] {plan.command_id}")
    print(f"  Dispositivo : {plan.device_label} ({plan.endpoint})")
    if plan.target:
        print(f"  Objetivo    : {plan.target} -> {plan.native_target}")
    print(f"  Riesgo      : {_paint_risk(plan.risk)}")
    print(f"  Transporte  : {'SIMULADO' if simulated else 'Cisco adapter'}")
    print("  Comandos:")
    for number, command in enumerate(plan.native_commands, 1):
        print(f"    {number:>2}. {command}")


def _confirm(plan: CommandPlan, input_fn: Callable[[str], str] = input) -> bool:
    answer = input_fn(f"Confirmar {plan.risk.value} sobre {plan.device_label}? [s/N]: ")
    return answer.strip().casefold() in ("s", "si", "sí", "y", "yes")


def _process(
    planner: CiscoPlanner,
    context: CiscoContext,
    tokens: list[str],
    *,
    dry_run: bool,
    assume_yes: bool,
    adapter: FakeCiscoAdapter,
    input_fn: Callable[[str], str] = input,
) -> int:
    if [part.casefold() for part in tokens] == ["port", "list"]:
        _print_ports(context.profile, context.selected_port)
        return 0
    plan = planner.plan(tokens, context.selected_port)
    render_plan(plan)
    write_log(
        f"CISCO PLAN device={plan.device_id} command={plan.command_id} "
        f"risk={plan.risk.value} target={plan.target or '-'}"
    )
    executor = CiscoExecutor(adapter)
    if dry_run:
        executor.execute(plan, dry_run=True)
        sys.stdout.flush()
        ok("DRY-RUN", "Plan validado; no se ha ejecutado ningún comando.")
        return 0
    approved = not plan.confirmation_required or assume_yes or _confirm(plan, input_fn)
    if not approved:
        ok("CANCELADO", "El plan no se ha enviado al adaptador.")
        return 1
    result = executor.execute(plan, approved=approved)
    print("\n" + "\n".join(result.output))
    sys.stdout.flush()
    ok("SIMULADO", "Plan aceptado por FakeCiscoAdapter; no existe conexión de red.")
    return 0


def run_managed_terminal(
    planner: CiscoPlanner,
    context: CiscoContext,
    *,
    dry_run: bool,
    assume_yes: bool,
    input_fn: Callable[[str], str] = input,
) -> int:
    adapter = FakeCiscoAdapter()
    print("Terminal Cisco gestionada (adaptador simulado). Escribe help o exit.")
    while True:
        selected = f"/{context.selected_port.id}" if context.selected_port else ""
        try:
            raw = input_fn(f"{planner.device.alias or planner.device.ip}/switch{selected}> ").strip()
        except EOFError:
            print()
            return 0
        if not raw:
            continue
        try:
            tokens = shlex.split(raw)
            lowered = [token.casefold() for token in tokens]
            if lowered[0] in ("exit", "quit", "salir"):
                return 0
            if lowered[0] in ("help", "?"):
                print(colorize_help(HELP), end="")
                continue
            if lowered[:2] == ["port", "select"] and len(tokens) == 3:
                port = context.select(tokens[2])
                ok("SELECCIONADO", f"{port.id} -> {port.native}")
                continue
            if lowered == ["port", "deselect"]:
                context.deselect()
                ok("DESELECCIONADO", "Ningún puerto seleccionado.")
                continue
            _process(planner, context, tokens, dry_run=dry_run, assume_yes=assume_yes, adapter=adapter, input_fn=input_fn)
        except ValueError as error:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {error}")


def run_switch(args: argparse.Namespace) -> int:
    tokens = _extract_options(args)
    database = DeviceDatabase(args.database)
    device = database.resolve(args.selector)
    profile_id = _profile_id(device, args.profile)
    profile = _device_profile(device, load_profile(profile_id, args.profiles))
    if not tokens:
        print(colorize_help(HELP), end="")
        print(f"\nPerfil: {profile.id} | {profile.model}")
        return 0
    lowered = [token.casefold() for token in tokens]
    if lowered[:2] == ["profile", "show"]:
        print(f"{profile.id} | {profile.model} | {len(profile.ports)} puertos")
        return 0
    if lowered[:2] == ["profile", "set"]:
        if len(tokens) != 3:
            raise ValueError("usa: switch ELEMENTO profile set PERFIL")
        selected = load_profile(tokens[2], args.profiles)
        options = dict(device.protocol_options.get("cisco-cli", {}))
        options["profile"] = selected.id
        database.configure_protocol(args.selector, "cisco-cli", options)
        ok("PERFIL", f"{device.alias or device.ip} -> {selected.id}")
        return 0
    if lowered[:2] == ["port", "label"]:
        if len(tokens) != 4 or not re.fullmatch(r"[A-Za-z0-9_.-]{1,32}", tokens[3]):
            raise ValueError("usa: switch ELEMENTO port label PUERTO NOMBRE (1-32 caracteres)")
        port = profile.resolve_port(tokens[2])
        # Valida que el nombre nuevo no colisione con otra referencia.
        for other in profile.ports:
            if other.id != port.id and any(
                tokens[3].casefold() == value.casefold()
                for value in other.references() if value
            ):
                raise ValueError(f"la etiqueta ya identifica {other.id}: {tokens[3]}")
        options = dict(device.protocol_options.get("cisco-cli", {}))
        labels = dict(options.get("portLabels", {}))
        labels[port.id] = tokens[3]
        options.update({"profile": profile.id, "portLabels": labels})
        database.configure_protocol(args.selector, "cisco-cli", options)
        ok("ETIQUETA", f"{tokens[3]} -> {port.id} -> {port.native}")
        return 0
    if lowered[:2] == ["port", "unlabel"]:
        if len(tokens) != 3:
            raise ValueError("usa: switch ELEMENTO port unlabel PUERTO")
        port = profile.resolve_port(tokens[2])
        options = dict(device.protocol_options.get("cisco-cli", {}))
        labels = dict(options.get("portLabels", {}))
        labels.pop(port.id, None)
        options.update({"profile": profile.id, "portLabels": labels})
        database.configure_protocol(args.selector, "cisco-cli", options)
        ok("ETIQUETA", f"Eliminada de {port.id} ({port.native})")
        return 0
    planner = CiscoPlanner(device, profile)
    context = CiscoContext(profile)
    if lowered == ["terminal"]:
        return run_managed_terminal(
            planner, context, dry_run=args.dry_run, assume_yes=args.yes
        )
    if lowered[:2] in (["port", "select"], ["port", "deselect"]):
        raise ValueError("la selección de puerto requiere: switch ELEMENTO terminal")
    return _process(
        planner, context, tokens, dry_run=args.dry_run, assume_yes=args.yes,
        adapter=FakeCiscoAdapter(),
    )
