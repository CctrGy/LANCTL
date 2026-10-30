from __future__ import annotations

import argparse
import os
import re
import sys
from collections.abc import Callable
from dataclasses import replace

from colorama import Fore, Style

from lanctl.apps.ip.infrastructure.cisco.adapters import FakeCiscoAdapter
from lanctl.apps.ip.infrastructure.cisco.context import CiscoContext
from lanctl.apps.ip.infrastructure.cisco.executor import CiscoExecutor
from lanctl.apps.ip.infrastructure.cisco.models import CommandPlan, Risk
from lanctl.apps.ip.infrastructure.cisco.planner import CiscoPlanner
from lanctl.apps.ip.infrastructure.cisco.profiles import PROFILE_PATH, load_profile
from lanctl.core.config import load_config
from lanctl.core.console import ok
from lanctl.core.database import DeviceDatabase
from lanctl.core.layout import fit_text, shrink_widths, terminal_columns
from lanctl.core.logger import write_log
from lanctl.core.parser import colorize_help
from lanctl.shared.i18n import t, translate_label

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
        help=t("LANCTL.UI.HELP.PLAN_FILTERED_REMAPPED_AND_CLASSIFIED_CISCO_COMMANDS"),
        description=translate_label(HELP),
    )
    command.add_argument("selector", help=t("LANCTL.UI.HELP.SWITCH_IP_MAC_OR_ALIAS"))
    command.add_argument("--profile", help=t("LANCTL.UI.HELP.CISCO_PROFILE_THAT_REMAPS_PORTS"))
    command.add_argument(
        "--profiles",
        default=config.get("ciscoProfiles", str(PROFILE_PATH)),
        help=t("LANCTL.UI.HELP.JSON_FILE_CONTAINING_CISCO_PROFILES"),
    )
    command.add_argument(
        "--database",
        default=config["database"],
        help=t("LANCTL.UI.HELP.ELEMENT_JSON_FILE"),
    )
    command.add_argument(
        "--dry-run", action="store_true", help=t("LANCTL.UI.HELP.SHOW_THE_PLAN_ONLY")
    )
    command.add_argument(
        "--yes", action="store_true", help=t("LANCTL.UI.HELP.CONFIRM_CHANGES_WITHOUT_ASKING")
    )
    command.add_argument(
        "arguments",
        nargs=argparse.REMAINDER,
        metavar="COMANDO",
        help=t("LANCTL.UI.HELP.MANAGED_CISCO_ACTION_TO_PLAN"),
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
        replace(port, label=str(labels.get(port.id, port.label))) for port in profile.ports
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
        {
            "sel": 3,
            "id": 7,
            "alias": alias_width,
            "native": native_width,
            "label": max(5, *(len(port.label or "-") for port in profile.ports)),
        },
        {"sel": 3, "id": 5, "alias": 5, "native": 6, "label": 5},
        ("sel", "id", "alias", "native", "label"),
        terminal_columns(),
        ("label", "alias", "native", "id"),
        gap=2,
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
    print(
        f"sel  {'id':<{widths['id']}}  {'alias':<{alias_width}}  {'native':<{native_width}}  label"
    )
    print(
        f"---  {'-' * widths['id']}  {'-' * alias_width}  {'-' * native_width}  {'-' * widths['label']}"
    )
    for port in profile.ports:
        aliases = ",".join(port.aliases)
        marker = " > " if selected and port.id == selected.id else "   "
        print(
            f"{marker}  {fit_text(port.id, widths['id']):<{widths['id']}}  {fit_text(aliases, alias_width):<{alias_width}}  {fit_text(port.native, native_width):<{native_width}}  {fit_text(port.label or '-', widths['label'])}"
        )


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
    print(
        t(
            "LANCTL.UI.DETAIL.DEVICE_VALUE_VALUE",
            value0=f"{plan.device_label}",
            value1=f"{plan.endpoint}",
        )
    )
    if plan.target:
        print(
            t(
                "LANCTL.UI.DETAIL.TARGET_VALUE_VALUE",
                value0=f"{plan.target}",
                value1=f"{plan.native_target}",
            )
        )
    print(t("LANCTL.UI.DETAIL.RISK_VALUE", value0=f"{_paint_risk(plan.risk)}"))
    print(
        t(
            "LANCTL.UI.DETAIL.TRANSPORT_VALUE",
            value0=f"{('SIMULADO' if simulated else 'Cisco adapter')}",
        )
    )
    print(t("LANCTL.UI.PRESENTATION.COMMANDS"))
    for number, command in enumerate(plan.native_commands, 1):
        print(f"    {number:>2}. {command}")


def _confirm(plan: CommandPlan, input_fn: Callable[[str], str] = input) -> bool:
    answer = input_fn(
        t(
            "LANCTL.UI.MESSAGE.CONFIRM_VALUE_ON_VALUE_S_N",
            value0=f"{plan.risk.value}",
            value1=f"{plan.device_label}",
        )
    )
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
        ok("DRY-RUN", t("LANCTL.UI.PROMPT.PLAN_VALIDATED_NO_COMMAND_WAS_EXECUTED"))
        return 0
    approved = not plan.confirmation_required or assume_yes or _confirm(plan, input_fn)
    if not approved:
        ok(
            t("LANCTL.UI.STATUS.CANCELLED"),
            t("LANCTL.UI.PROMPT.THE_PLAN_WAS_NOT_SENT_TO_THE_ADAPTER"),
        )
        return 1
    result = executor.execute(plan, approved=approved)
    print("\n" + "\n".join(result.output))
    sys.stdout.flush()
    ok(
        t("LANCTL.UI.STATUS.SIMULATED"),
        t("LANCTL.UI.PROMPT.PLAN_ACCEPTED_BY_FAKECISCOADAPTER_NO_NETWORK_CONNECTION_EXISTS"),
    )
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
    print(t("LANCTL.UI.PROMPT.MANAGED_CISCO_TERMINAL_SIMULATED_ADAPTER_TYPE_HELP_OR_EXIT"))
    while True:
        selected = f"/{context.selected_port.id}" if context.selected_port else ""
        try:
            raw = input_fn(
                f"{planner.device.alias or planner.device.ip}/switch{selected}> "
            ).strip()
        except EOFError:
            print()
            return 0
        if not raw:
            continue
        try:
            from lanctl.core.command_line import split_command_line

            tokens = split_command_line(raw)
            lowered = [token.casefold() for token in tokens]
            if lowered[0] in ("exit", "quit", "salir"):
                return 0
            if lowered[0] in ("help", "?"):
                print(colorize_help(translate_label(HELP)), end="")
                continue
            if lowered[:2] == ["port", "select"] and len(tokens) == 3:
                port = context.select(tokens[2])
                ok(t("LANCTL.CLI.STATUS.SELECTED"), f"{port.id} -> {port.native}")
                continue
            if lowered == ["port", "deselect"]:
                context.deselect()
                ok(t("LANCTL.UI.STATUS.DESELECTED"), t("LANCTL.UI.PROMPT.NO_PORT_SELECTED"))
                continue
            _process(
                planner,
                context,
                tokens,
                dry_run=dry_run,
                assume_yes=assume_yes,
                adapter=adapter,
                input_fn=input_fn,
            )
        except ValueError as error:
            print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {error}")


def run_switch(args: argparse.Namespace) -> int:
    tokens = _extract_options(args)
    database = DeviceDatabase(args.database)
    device = database.resolve(args.selector)
    profile_id = _profile_id(device, args.profile)
    profile = _device_profile(device, load_profile(profile_id, args.profiles))
    if not tokens:
        print(colorize_help(translate_label(HELP)), end="")
        print(
            t(
                "LANCTL.UI.DETAIL.PROFILE_VALUE_VALUE",
                value0=f"{profile.id}",
                value1=f"{profile.model}",
            )
        )
        return 0
    lowered = [token.casefold() for token in tokens]
    if lowered[:2] == ["profile", "show"]:
        print(
            t(
                "LANCTL.UI.SUMMARY.VALUE_VALUE_VALUE_PORTS",
                value0=f"{profile.id}",
                value1=f"{profile.model}",
                value2=f"{len(profile.ports)}",
            )
        )
        return 0
    if lowered[:2] == ["profile", "set"]:
        if len(tokens) != 3:
            raise ValueError("usa: switch ELEMENTO profile set PERFIL")
        selected = load_profile(tokens[2], args.profiles)
        options = dict(device.protocol_options.get("cisco-cli", {}))
        options["profile"] = selected.id
        database.configure_protocol(args.selector, "cisco-cli", options)
        ok(t("LANCTL.UI.STATUS.PROFILE"), f"{device.alias or device.ip} -> {selected.id}")
        return 0
    if lowered[:2] == ["port", "label"]:
        if len(tokens) != 4 or not re.fullmatch(r"[A-Za-z0-9_.-]{1,32}", tokens[3]):
            raise ValueError("usa: switch ELEMENTO port label PUERTO NOMBRE (1-32 caracteres)")
        port = profile.resolve_port(tokens[2])
        # Valida que el nombre nuevo no colisione con otra referencia.
        for other in profile.ports:
            if other.id != port.id and any(
                tokens[3].casefold() == value.casefold() for value in other.references() if value
            ):
                raise ValueError(f"la etiqueta ya identifica {other.id}: {tokens[3]}")
        options = dict(device.protocol_options.get("cisco-cli", {}))
        labels = dict(options.get("portLabels", {}))
        labels[port.id] = tokens[3]
        options.update({"profile": profile.id, "portLabels": labels})
        database.configure_protocol(args.selector, "cisco-cli", options)
        ok(t("LANCTL.UI.STATUS.LABEL"), f"{tokens[3]} -> {port.id} -> {port.native}")
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
        ok(
            t("LANCTL.UI.STATUS.LABEL"),
            t(
                "LANCTL.UI.MESSAGE.DELETED_FROM_VALUE_VALUE",
                value0=f"{port.id}",
                value1=f"{port.native}",
            ),
        )
        return 0
    planner = CiscoPlanner(device, profile)
    context = CiscoContext(profile)
    if lowered == ["terminal"]:
        return run_managed_terminal(planner, context, dry_run=args.dry_run, assume_yes=args.yes)
    if lowered[:2] in (["port", "select"], ["port", "deselect"]):
        raise ValueError("la selección de puerto requiere: switch ELEMENTO terminal")
    return _process(
        planner,
        context,
        tokens,
        dry_run=args.dry_run,
        assume_yes=args.yes,
        adapter=FakeCiscoAdapter(),
    )
