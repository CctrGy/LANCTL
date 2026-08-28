"""Comandos compartidos por el CLI externo y la consola del TUI."""

from __future__ import annotations

import json
import shlex
from dataclasses import dataclass

from lanctl.apps.wire.idf.database import IDFDatabaseManager
from lanctl.apps.wire.idf.sample_topology import seed_sample_topology


@dataclass(frozen=True)
class CommandResult:
    lines: tuple[str, ...] = ()
    refresh: bool = False
    exit_requested: bool = False
    list_prefix: str | None = None
    view_id: str | None = None


class CommandProcessor:
    def __init__(self, database: IDFDatabaseManager) -> None:
        self.database = database

    def execute(self, command: str, *, selected_id: str | None = None) -> CommandResult:
        try:
            parts = shlex.split(command)
        except ValueError as error:
            return CommandResult((f"Error de sintaxis: {error}",))
        if not parts:
            return CommandResult()
        action = parts[0].casefold()
        try:
            if action in ("exit", "quit"):
                return CommandResult(("Cerrando LANWIRE…",), exit_requested=True)
            if action in ("help", "?"):
                return CommandResult(self.help_lines())
            if action == "clear":
                return CommandResult(refresh=True)
            if action == "seed":
                created = seed_sample_topology(self.database)
                message = (
                    f"Topología inicial creada: {len(created)} elementos"
                    if created
                    else "La topología inicial ya estaba cargada."
                )
                return CommandResult((message,), refresh=True)
            if action in ("list", "ls"):
                if len(parts) > 2:
                    raise ValueError("usa: list [PREFIJO]")
                prefix = parts[1].upper() if len(parts) == 2 else None
                records = self.database.list(prefix)
                lines = tuple(
                    f"{record['id']:<10} {json.dumps(record['data'], ensure_ascii=False)}"
                    for record in records
                )
                empty = (
                    f"No hay elementos con prefijo {prefix}."
                    if prefix
                    else "La base de datos IDF está vacía."
                )
                return CommandResult(lines or (empty,), list_prefix=prefix)
            if action == "show" and len(parts) in (1, 2):
                identifier = parts[1] if len(parts) == 2 else selected_id
                if not identifier:
                    return CommandResult(("No hay ningún elemento seleccionado.",))
                record = self.database.get(identifier)
                return CommandResult(
                    (json.dumps(record, indent=2, ensure_ascii=False),)
                    if record
                    else (f"IDF no encontrado: {identifier.upper()}",),
                    view_id=record["id"] if record else None,
                )
            if action == "prefix":
                return self._prefix_command(parts[1:])
            if action == "add" and len(parts) >= 2:
                record = self.database.create(parts[1], data=self._parse_data(parts[2:]))
                return CommandResult((f"Creado {record['id']}",), refresh=True)
            if action == "reserve" and len(parts) >= 2:
                record = self.database.add(parts[1], self._parse_data(parts[2:]))
                return CommandResult((f"Reservado {record['id']}",), refresh=True)
            if action in ("delete", "del") and len(parts) == 2:
                record = self.database.delete(parts[1])
                return CommandResult((f"Eliminado {record['id']}",), refresh=True)
            return CommandResult((f"Comando desconocido: {command}", "Escribe 'help'."))
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            return CommandResult((f"Error: {error}",))

    @staticmethod
    def _parse_data(parts: list[str]) -> dict[str, str]:
        data = {}
        for item in parts:
            if "=" not in item:
                raise ValueError(f"se esperaba CLAVE=VALOR: {item}")
            key, value = item.split("=", 1)
            if not key:
                raise ValueError("la clave de datos no puede estar vacía")
            data[key] = value
        return data

    def _prefix_command(self, parts: list[str]) -> CommandResult:
        if not parts or parts[0].casefold() == "list":
            definitions = self.database.prefixes()
            lines = tuple(
                f"{item['prefix']:<4} {item['name']:<20} {item['description']}"
                for item in definitions
            )
            return CommandResult(lines or ("No hay prefijos definidos.",))
        if parts[0].casefold() == "show" and len(parts) == 2:
            definition = self.database.get_prefix(parts[1])
            return CommandResult(
                (json.dumps(definition, indent=2, ensure_ascii=False),)
                if definition
                else (f"Prefijo no definido: {parts[1].upper()}",)
            )
        if parts[0].casefold() == "set" and len(parts) in (3, 4):
            definition = self.database.define_prefix(
                parts[1], parts[2], parts[3] if len(parts) == 4 else ""
            )
            return CommandResult(
                (f"Prefijo {definition['prefix']} definido como {definition['name']}",),
                refresh=True,
            )
        if parts[0].casefold() in ("delete", "del") and len(parts) == 2:
            definition = self.database.delete_prefix(parts[1])
            return CommandResult((f"Definición eliminada: {definition['prefix']}",), refresh=True)
        raise ValueError(
            'usa: prefix list | show LETRAS | set LETRAS "NOMBRE" "DESCRIPCIÓN" | delete LETRAS'
        )

    @staticmethod
    def help_lines() -> tuple[str, ...]:
        return (
            "help                         Muestra esta ayuda",
            "seed                         Carga la topología de pruebas",
            "list [PREFIJO]               Lista todos los IDF o filtra por letras",
            "show                         Abre el elemento seleccionado en el TUI",
            "show IDF                     Muestra un registro explícito",
            'prefix set XX "NOMBRE" "DESC" Define un juego de letras',
            "prefix list                  Lista los juegos de letras",
            "add PREFIJO [CLAVE=VALOR]     Crea el siguiente IDF libre",
            "reserve IDF [CLAVE=VALOR]     Reserva un IDF concreto",
            "delete IDF                   Elimina un IDF",
            "clear                        Limpia la salida del TUI",
            "exit                         Cierra la TUI",
        )
