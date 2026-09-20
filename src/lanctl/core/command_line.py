from __future__ import annotations

import os
import shlex


def split_command_chain(command: str) -> list[str]:
    """Divide órdenes separadas por ``;`` sin romper texto entre comillas."""

    commands: list[str] = []
    current: list[str] = []
    quote = ""
    for character in command:
        if character in ('"', "'"):
            if not quote:
                quote = character
            elif quote == character:
                quote = ""
        if character == ";" and not quote:
            value = "".join(current).strip()
            if value:
                commands.append(value)
            current = []
        else:
            current.append(character)
    if quote:
        raise ValueError("hay una comilla sin cerrar en la línea de comandos")
    value = "".join(current).strip()
    if value:
        commands.append(value)
    return commands


def split_command_line(command: str) -> list[str]:
    """Divide una orden interactiva respetando las rutas nativas de Windows."""

    if os.name != "nt":
        return shlex.split(command, posix=True)

    # shlex POSIX interpreta las barras inversas de una ruta como escapes. El
    # modo no POSIX las conserva, aunque mantiene las comillas exteriores.
    parts = shlex.split(command, posix=False)
    return [
        part[1:-1] if len(part) >= 2 and part[0] == part[-1] and part[0] in {'"', "'"} else part
        for part in parts
    ]
