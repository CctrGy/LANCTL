"""Read-only diagnostics and explicit, addressed interface control."""

from __future__ import annotations

import json
import time

from lanctl.core.coordination import Coordinator
from lanctl.core.parser import LANCTLArgumentParser


def build_parser():
    parser = LANCTLArgumentParser(
        prog="LANCTL backend", description="Coordinación local entre launchers."
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="status",
        choices=("status", "sessions", "events", "tasks", "refresh"),
    )
    parser.add_argument("--session", help="ID exacto de la interfaz que se actualizará.")
    parser.add_argument("--after", type=int, default=0, help="Cursor de eventos (seq).")
    parser.add_argument("--limit", type=int, default=100, help="Máximo de eventos, 1-1000.")
    parser.add_argument(
        "--follow", action="store_true", help="Sigue eventos en vivo; Ctrl+C termina."
    )
    return parser


def run(argv):
    parser = build_parser()
    args = parser.parse_args(argv)
    coordinator = Coordinator()
    if args.follow:
        if args.action != "events":
            parser.error("--follow requiere events")
        try:
            cursor = args.after
            while True:
                for row in coordinator.events(cursor, args.limit):
                    cursor = row["seq"]
                    print(json.dumps(row, ensure_ascii=False), flush=True)
                time.sleep(0.5)
        except KeyboardInterrupt:
            return 0
    if args.action == "refresh":
        if not args.session:
            parser.error("refresh requiere --session ID; nunca se elige una ventana arbitraria")
        result = {"queued": coordinator.enqueue(args.session, "refresh")}
    elif args.action == "sessions":
        result = coordinator.sessions()
    elif args.action == "tasks":
        result = coordinator.tasks()
    elif args.action == "events":
        result = coordinator.events(args.after, args.limit)
    else:
        result = {
            "transport": "sqlite-local",
            "path": str(coordinator.path),
            "sessions": coordinator.sessions(),
            "schemaVersion": 1,
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0
