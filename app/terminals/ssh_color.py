from __future__ import annotations

import re

from colorama import Fore, Style


RESET = Style.RESET_ALL
ANSI_PATTERN = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
TOKEN_PATTERN = re.compile(
    r"(?P<mac>\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b)"
    r"|(?P<ip>\b(?:\d{1,3}\.){3}\d{1,3}\b)"
    r"|(?P<interface>\b(?:Gi|GigabitEthernet|Fa|FastEthernet|Te|Eth|Vlan|x)"
    r"[A-Za-z0-9/.-]*\b)"
    r"|(?P<good>\b(?:up|enabled|connected|active|success|ok)\b)"
    r"|(?P<bad>\b(?:down|disabled|disconnected|failed|error|invalid)\b)",
    re.IGNORECASE,
)


def colorize_ssh_output(value: str, theme: str = "generic") -> str:
    """Añade color sin modificar el contenido recibido del dispositivo."""
    if not value or ANSI_PATTERN.search(value):
        return value
    return "".join(_colorize_line(line, theme) for line in value.splitlines(keepends=True))


def _colorize_line(line: str, theme: str) -> str:
    body = line.rstrip("\r\n")
    ending = line[len(body):]
    lowered = body.strip().casefold()
    if not body:
        return line
    if re.search(r"(?:^|\s)(?:error|failed|invalid|denied|unknown)(?:\s|:|$)", lowered):
        return f"{Style.BRIGHT}{Fore.LIGHTRED_EX}{body}{RESET}{ending}"
    if re.search(r"(?:^|\s)(?:warning|warn|caution)(?:\s|:|$)", lowered):
        return f"{Style.BRIGHT}{Fore.LIGHTYELLOW_EX}{body}{RESET}{ending}"
    if body.rstrip().endswith((">", "#", "$")):
        prompt_color = Fore.LIGHTCYAN_EX if theme == "cisco" else Fore.LIGHTGREEN_EX
        return f"{Style.BRIGHT}{prompt_color}{body}{RESET}{ending}"

    colors = {
        "mac": Fore.LIGHTMAGENTA_EX,
        "ip": Fore.LIGHTBLUE_EX,
        "interface": Fore.LIGHTCYAN_EX,
        "good": Fore.LIGHTGREEN_EX,
        "bad": Fore.LIGHTRED_EX,
    }
    output: list[str] = []
    position = 0
    for match in TOKEN_PATTERN.finditer(body):
        output.append(body[position:match.start()])
        output.append(f"{Style.BRIGHT}{colors[match.lastgroup]}{match.group(0)}{RESET}")
        position = match.end()
    output.append(body[position:])
    return "".join(output) + ending


def terminal_theme(options: dict) -> str:
    adapter = str(options.get("terminalAdapter", "")).casefold()
    driver = str(options.get("driver", "")).casefold()
    if "cisco" in driver:
        return "cisco"
    if "esp" in adapter:
        return "esp"
    return "generic"
