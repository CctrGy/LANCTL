"""Comandos compartidos por el CLI externo y la consola del TUI."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass

from lanctl.apps.wire.graph import topology_lines
from lanctl.apps.wire.idf.database import IDFDatabaseManager
from lanctl.apps.wire.idf.sample_topology import seed_sample_topology
from lanctl.apps.wire.log import write_exception
from lanctl.apps.wire.topology import NEW_IDF_PROFILES, build_new_idf_data


@dataclass(frozen=True)
class CommandResult:
    lines: tuple[str, ...] = ()
    refresh: bool = False
    exit_requested: bool = False
    list_prefix: str | None = None
    list_group: str | None = None
    view_id: str | None = None
    graph: bool = False


class CommandProcessor:
    def __init__(self, database: IDFDatabaseManager) -> None:
        self.database = database

    def execute(self, command: str, *, selected_id: str | None = None) -> CommandResult:
        try:
            from lanctl.core.command_line import split_command_line

            parts = split_command_line(command)
        except ValueError as error:
            return CommandResult((f"Error de sintaxis: {error}",))
        return self.execute_parts(parts, selected_id=selected_id)

    def execute_parts(self, parts: list[str], *, selected_id: str | None = None) -> CommandResult:
        """Ejecuta argumentos ya separados, sin volver a interpretar sus comillas."""
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
            if action in ("graph", "map"):
                return CommandResult(tuple(topology_lines(self.database.all())), graph=True)
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
                    raise ValueError("usa: list [PREFIJO|@GRUPO]")
                selector = parts[1] if len(parts) == 2 else ""
                group = selector[1:].upper() if selector.startswith("@") else None
                prefix = selector.upper() if selector and group is None else None
                records = self.database.list_group(group) if group else self.database.list(prefix)
                lines = tuple(
                    f"{record['id']:<10} {json.dumps(record['data'], ensure_ascii=False)}"
                    for record in records
                )
                empty = (
                    f"No hay elementos con grupo {group}."
                    if group
                    else f"No hay elementos con prefijo {prefix}."
                    if prefix
                    else "La base de datos IDF está vacía."
                )
                return CommandResult(lines or (empty,), list_prefix=prefix, list_group=group)
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
            if action == "element":
                return self._element_command(parts[1:])
            if action == "idf":
                return self._idf_command(parts[1:])
            if action == "prefix":
                return self._prefix_command(parts[1:])
            if action == "add" and len(parts) >= 2:
                number_width, amount = self._add_options(parts[2:])
                records = [
                    self.database.create(parts[1], number_width=number_width) for _ in range(amount)
                ]
                names = ", ".join(record["id"] for record in records)
                message = f"Creado {names}" if amount == 1 else f"Creados {names}"
                return CommandResult((message,), refresh=True)
            if action == "reserve" and len(parts) >= 2:
                record = self.database.add(parts[1], self._parse_data(parts[2:]))
                return CommandResult((f"Reservado {record['id']}",), refresh=True)
            if action in ("delete", "del") and len(parts) == 2:
                record = self.database.delete(parts[1])
                return CommandResult((f"Eliminado {record['id']}",), refresh=True)
            return CommandResult((f"Comando desconocido: {' '.join(parts)}", "Escribe 'help'."))
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            code = (
                "LANWIRE_ELEMENT_COMMAND_FAILED"
                if action == "element"
                else "LANWIRE_COMMAND_FAILED"
            )
            reported = write_exception(
                error,
                caused="lanwire.cli.commands",
                code=code,
                context={"action": action},
            )
            return CommandResult((f"Error [{reported.code}]: {reported.text}",))

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

    def _idf_command(self, parts: list[str]) -> CommandResult:
        if parts and parts[0].casefold() == "types":
            if len(parts) != 1:
                raise ValueError("usa: idf types")
            profiles = sorted({profile[0] for profile in NEW_IDF_PROFILES.values()})
            return CommandResult(tuple(profiles))
        if parts and parts[0].casefold() in {"show", "edit", "delete", "del"}:
            operation = parts[0].casefold()
            if len(parts) < 2:
                raise ValueError(f"usa: idf {operation} PREFIJO|IDF [opciones]")
            code = parts[1]
            is_record = "-" in code
            if operation == "show":
                if len(parts) != 2:
                    raise ValueError("usa: idf show PREFIJO|IDF")
                value = self.database.get(code) if is_record else self.database.get_prefix(code)
                label = "IDF" if is_record else "Prefijo"
                return CommandResult(
                    (json.dumps(value, indent=2, ensure_ascii=False),)
                    if value
                    else (f"{label} no encontrado: {code.upper()}",)
                )
            if operation in {"delete", "del"}:
                if len(parts) != 2 or not is_record:
                    raise ValueError(
                        "usa: idf delete IDF; para un prefijo usa prefix delete LETRAS"
                    )
                record = self.database.delete(code)
                return CommandResult((f"Eliminado {record['id']}",), refresh=True)
            if is_record:
                if len(parts) < 3:
                    raise ValueError("usa: idf edit IDF CAMPO=VALOR [...]")
                return self._element_command(parts[1:])
            if len(parts) < 4:
                raise ValueError("usa: idf edit PREFIJO -type TIPO|-name NOMBRE|-description TEXTO")
            definition = self.database.get_prefix(code)
            if definition is None:
                raise ValueError(f"prefijo no definido: {code.upper()}")
            values = self._idf_options(parts[2:])
            profile = values.get("-type") or definition.get("type_profile")
            name = values.get("-name") or values.get("-alias") or definition["name"]
            description = values.get("-description", definition.get("description", ""))
            updated = (
                self.database.define_prefix_profile(
                    code, profile, name=name, description=description
                )
                if profile
                else self.database.define_prefix(code, name, description)
            )
            return CommandResult(
                (
                    f"Prefijo {updated['prefix']} actualizado a {updated.get('type_profile', 'sin perfil')}",
                ),
                refresh=True,
            )
        if parts and parts[0].casefold() == "list":
            if len(parts) > 2:
                raise ValueError("usa: idf list [PREFIJO]")
            if len(parts) == 2:
                prefix = parts[1].upper()
                records = self.database.list(prefix)
                lines = tuple(
                    f"{record['id']:<10} {json.dumps(record['data'], ensure_ascii=False)}"
                    for record in records
                )
                return CommandResult(
                    lines or (f"No hay elementos con prefijo {prefix}.",),
                    list_prefix=prefix,
                )
            definitions = {item["prefix"]: item for item in self.database.prefixes()}
            counts: dict[str, int] = {}
            for record in self.database.all():
                prefix = record["prefix"]
                counts[prefix] = counts.get(prefix, 0) + 1
            lines = tuple(
                f"{prefix:<5} {definitions.get(prefix, {}).get('type_profile', 'sin perfil'):<18} "
                f"{counts.get(prefix, 0)} IDF"
                for prefix in sorted(definitions.keys() | counts.keys())
            )
            return CommandResult(lines or ("No hay prefijos IDF.",))
        if len(parts) < 2 or parts[0].casefold() not in {"new", "add"}:
            raise ValueError("usa: idf types|list|show|new|add|edit|delete [argumentos]")
        operation = parts[0].casefold()
        code = parts[1]
        values = self._idf_options(parts[2:])
        if operation == "new":
            if "-" in code:
                raise ValueError("idf new espera solo letras; usa idf add para un IDF concreto")
            if "-type" not in values:
                raise ValueError("idf new PREFIJO requiere -type TIPO")
            definition = self.database.define_prefix_profile(
                code,
                values["-type"],
                name=values.get("-name", "") or values.get("-alias", ""),
                description=values.get("-description", ""),
            )
            return CommandResult(
                (f"Prefijo {definition['prefix']} definido como {definition['type_profile']}",),
                refresh=True,
            )
        if "-" not in code:
            raise ValueError("idf add requiere un IDF concreto; por ejemplo BR-00")
        if "-type" in values:
            raise ValueError("el tipo se asigna al prefijo con idf new; idf add no admite -type")
        prefix = code.split("-", 1)[0].upper()
        definition = self.database.get_prefix(prefix)
        profile = definition.get("type_profile") if definition else None
        if not profile:
            raise ValueError(f"el prefijo {prefix} no tiene tipo; usa idf new {prefix} -type TIPO")
        data = build_new_idf_data(
            profile,
            alias=values.get("-alias", ""),
            description=values.get("-description", ""),
        )
        if values.get("-name", "").strip():
            data["name"] = values["-name"].strip()
        record = self.database.add(code, data)
        return CommandResult((f"Creado {record['id']} ({data['subtype']})",), refresh=True)

    @staticmethod
    def _idf_options(parts: list[str]) -> dict[str, str]:
        values: dict[str, str] = {}
        index = 0
        while index < len(parts):
            flag = parts[index].casefold()
            if flag == "-descriptionn":
                flag = "-description"
            if flag not in {"-type", "-name", "-alias", "-description"}:
                raise ValueError(f"opción desconocida: {parts[index]}")
            if flag in values:
                raise ValueError(f"opción repetida: {parts[index]}")
            if index + 1 >= len(parts) or parts[index + 1].startswith("-"):
                raise ValueError(f"falta el valor de {parts[index]}")
            values[flag] = parts[index + 1]
            index += 2
        return values

    def _element_command(self, parts: list[str]) -> CommandResult:
        """Edita por CLI exactamente los campos editables de un elemento.

        ``element IDF`` consulta el registro. Para modificarlo se reciben
        pares ``campo=valor``; los puertos usan ``port.NOMBRE.campo=valor``.
        """
        if not parts:
            raise ValueError("usa: element IDF [campo=valor ...]")
        record = self.database.get(parts[0])
        if record is None:
            raise ValueError(f"IDF no encontrado: {parts[0].upper()}")
        if len(parts) == 1:
            return CommandResult((json.dumps(record["data"], indent=2, ensure_ascii=False),))

        assignments = self._parse_data(parts[1:])
        data = deepcopy(record.get("data") or {})
        # Importación diferida: el paquete TUI publica también su aplicación,
        # que a su vez usa CommandProcessor.
        from lanctl.apps.wire.tui.editor import editable_fields, set_field

        changed: list[str] = []
        for supplied, value in assignments.items():
            label, selected_port = self._element_field_label(supplied, data)
            fields = editable_fields({"data": data}, selected_port)
            field = next(
                (item for item in fields if item.label.casefold() == label.casefold()), None
            )
            if field is None:
                allowed = ", ".join(self._element_field_names(fields, selected_port))
                raise ValueError(f"campo no editable: {supplied}. Usa: {allowed}")
            set_field(data, field, value)
            changed.append(field.label)

        self.database.update(record["id"], data)
        return CommandResult((f"Actualizado {record['id']}: {', '.join(changed)}",), refresh=True)

    @staticmethod
    def _element_field_label(supplied: str, data: dict) -> tuple[str, str | None]:
        aliases = {
            "ports": "portCount",
            "portcount": "portCount",
            "portnaming": "portNaming",
            "templatekind": "portTemplate.kind",
            "templatepoe": "portTemplate.poe",
            "templatespeeds": "portTemplate.speeds",
        }
        normalized = supplied.strip()
        lowered = normalized.casefold()
        if lowered.startswith("port."):
            pieces = normalized.split(".", 2)
            if len(pieces) != 3 or not pieces[1] or pieces[2] not in {"kind", "poe", "speeds"}:
                raise ValueError("un puerto usa: port.NOMBRE.kind|poe|speeds=VALOR")
            ports = data.get("ports") or {}
            port = next((name for name in ports if name.casefold() == pieces[1].casefold()), None)
            if port is None:
                raise ValueError(f"puerto no encontrado: {pieces[1]}")
            return f"{port}.{pieces[2]}", port
        return aliases.get(lowered, normalized), None

    @staticmethod
    def _element_field_names(fields, selected_port: str | None) -> tuple[str, ...]:
        names = [field.label for field in fields if not field.label.startswith("end")]
        if selected_port:
            names = [name for name in names if not name.startswith(f"{selected_port}.")]
        return (*names, "port.NOMBRE.kind", "port.NOMBRE.poe", "port.NOMBRE.speeds")

    @staticmethod
    def _add_options(parts: list[str]) -> tuple[int | None, int]:
        """Acepta solo opciones de creación; los metadatos se editan desde el TUI."""
        remaining = list(parts)
        number_width = None
        amount = 1
        if "--digits" in remaining:
            position = remaining.index("--digits")
            if position + 1 >= len(remaining) or remaining.count("--digits") != 1:
                raise ValueError("usa --digits con un valor entre 2 y 5")
            try:
                number_width = int(remaining[position + 1])
            except ValueError as error:
                raise ValueError("--digits debe ser un número entre 2 y 5") from error
            del remaining[position : position + 2]
        more_flags = [
            item
            for item in remaining
            if item in {"-more", "--more"} or item.startswith(("-more=", "--more="))
        ]
        if more_flags:
            if len(more_flags) != 1:
                raise ValueError("usa -more con un número mayor que cero")
            flag = more_flags[0]
            position = remaining.index(flag)
            try:
                if "=" in flag:
                    amount = int(flag.split("=", 1)[1])
                    del remaining[position]
                else:
                    if position + 1 >= len(remaining):
                        raise ValueError
                    amount = int(remaining[position + 1])
                    del remaining[position : position + 2]
            except ValueError as error:
                raise ValueError("-more debe ser un número mayor que cero") from error
        if remaining:
            raise ValueError("add no admite CLAVE=VALOR; edita el elemento desde el TUI")
        if number_width is not None and not 2 <= number_width <= 5:
            raise ValueError("--digits debe estar entre 2 y 5")
        if amount < 1:
            raise ValueError("-more debe ser mayor que cero")
        return number_width, amount

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
            "graph                        Abre una vista gráfica de la topología",
            "list [PREFIJO|@GRUPO]        Lista IDF, prefijo o grupo lógico",
            "show                         Abre el elemento seleccionado en el TUI",
            "show IDF                     Muestra un registro explícito",
            'prefix set XX "NOMBRE" "DESC" Define un juego de letras',
            "prefix list                  Lista los juegos de letras",
            "add PREFIJO [-more N] [--digits 2-5] Crea uno o varios IDF libres",
            "idf new PREFIJO -type TIPO   Asigna un perfil al juego de letras",
            "idf list [PREFIJO]          Lista prefijos o los IDF de uno de ellos",
            "idf types                   Lista los perfiles físicos disponibles",
            "idf show PREFIJO|IDF        Consulta el perfil o los datos de un IDF",
            "idf edit IDF CAMPO=VALOR    Edita datos y puertos de un IDF",
            "idf edit PREFIJO -type TIPO Cambia el perfil de futuros IDF del prefijo",
            "idf delete IDF              Elimina un IDF; no elimina el prefijo",
            'idf add IDF [-name NOMBRE] [-description "TEXTO"] Crea un IDF del perfil asignado',
            "  tipos: wire.copper wire.fiber wire.dac router.otg router.gateway",
            "         switch.5Ports switch.12Ports switch.24Ports switch.48Ports",
            "reserve IDF [CLAVE=VALOR]     Reserva un IDF concreto",
            "element IDF [CAMPO=VALOR]    Consulta o edita datos físicos; ports=N cambia RJ45",
            "  campos: type name alias description groups lanipDevice ip speeds rack unit",
            "  puertos: ports portNaming templateKind templatePoe templateSpeeds",
            "  excepción: port.LAN1.kind|poe|speeds=VALOR",
            "delete IDF                   Elimina un IDF",
            "clear                        Limpia la salida del TUI",
            "exit                         Cierra la TUI",
        )
