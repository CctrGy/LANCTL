from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date

from app.core.history import HistoryService


def register_history_command(commands: argparse._SubParsersAction) -> None:
    command=commands.add_parser("history",help="Consulta eventos estructurados del proyecto VLF activo.")
    command.add_argument("selector",nargs="?",help="DeviceId, alias, nombre, MAC, IP actual o histórica.")
    command.add_argument("--all",action="store_true",help="Incluye eventos generales de toda la LAN.")
    command.add_argument("--commands",action="store_true",help="En CLI interactiva muestra los comandos de la sesión.")
    command.add_argument("--today",action="store_true",help="Limita la consulta al día local actual.")
    command.add_argument("--from",dest="date_from",type=date.fromisoformat,metavar="FECHA",help="Fecha inicial YYYY-MM-DD.")
    command.add_argument("--to",dest="date_to",type=date.fromisoformat,metavar="FECHA",help="Fecha final YYYY-MM-DD.")
    command.add_argument("--type",dest="types",action="append",default=[],help="Tipo canónico; se puede repetir.")
    command.add_argument("--source",help="Filtra por origen."); command.add_argument("--result",help="Filtra por resultado.")
    command.add_argument("--errors",action="store_true",help="Muestra únicamente errores."); command.add_argument("--search",help="Busca texto seguro.")
    command.add_argument("--limit",type=int,default=100,help="Máximo de eventos (1..10000)."); command.add_argument("--reverse",action="store_true",help="Orden descendente.")
    command.add_argument("--format",choices=("table","json","csv"),default="table",help="Formato de salida.")
    command.set_defaults(handler=run_history)


def run_history(args:argparse.Namespace)->int:
    if args.commands: raise ValueError("--commands solo está disponible dentro de la CLI interactiva")
    if not args.selector and not args.all: raise ValueError("indica NAME o usa --all")
    today=date.today() if args.today else None
    rows=HistoryService().query(None if args.all else args.selector,date_from=today or args.date_from,date_to=today or args.date_to,types=args.types,source=args.source,result=args.result,errors=args.errors,search=args.search,limit=args.limit,reverse=args.reverse)
    values=[event.to_dict() for event in rows]
    if args.format=="json": print(json.dumps(values,indent=2,ensure_ascii=False)); return 0
    if args.format=="csv":
        writer=csv.writer(sys.stdout); writer.writerow(("timestamp","device","source","type","result","summary"))
        for e in rows: writer.writerow((e.timestamp,e.device.label if e.device else "",e.source,e.type,e.result,e.summary))
        return 0
    print(f"HISTORIAL — {args.selector or 'LAN'}"); print("FECHA | ELEMENTO | EVENTO | RESULTADO | RESUMEN")
    for e in rows: print(f"{e.timestamp} | {e.device.label if e.device else '-'} | {e.type} | {e.result} | {e.summary}")
    return 0
