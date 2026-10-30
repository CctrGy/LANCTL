#!/bin/sh
# Cierre de emergencia de LANCTL en Linux; no necesita dependencias del proyecto.
exec python3 - "$@" <<'PY'
import argparse
import os
from pathlib import Path
import signal
import sys
import time

parser = argparse.ArgumentParser(description=(
    "Cierra todas las instancias LANCTL del usuario y sus procesos secundarios. "
    "Envía SIGTERM y, tras 2 segundos, SIGKILL. Puede perder cambios sin guardar."
))
parser.add_argument("--dry-run", action="store_true", help="Muestra los procesos sin cerrarlos.")
args = parser.parse_args()
launchers = {"lanctl", "lanip", "als", "lanwire", "lanwre", "lanrack", "lanaccess", "lanmon"}


def read_process(pid):
    try:
        base = Path("/proc") / str(pid)
        if base.stat().st_uid != os.getuid():
            return None
        stat = (base / "stat").read_text().rsplit(")", 1)[1].split()
        command = [part.decode(errors="replace") for part in (base / "cmdline").read_bytes().split(b"\0") if part]
        return int(stat[1]), stat[19], stat[0], command
    except (OSError, ValueError, IndexError):
        return None


def is_lanctl(command):
    if not command:
        return False
    executable = Path(command[0]).name
    if executable in launchers:
        return True
    if not executable.startswith(("python", "pypy")):
        return False
    if len(command) > 2 and command[1] == "-m":
        return command[2] == "lanctl" or command[2].startswith("lanctl.")
    return len(command) > 1 and Path(command[1]).name in {
        name + ".py" for name in launchers
    } | launchers


processes = {}
for entry in Path("/proc").iterdir():
    if entry.name.isdecimal():
        info = read_process(int(entry.name))
        if info:
            processes[int(entry.name)] = info
# Nunca cerrar el propio lanzador ni la terminal desde la que se invoca.
excluded = {os.getpid()}
pid = os.getpid()
while pid in processes:
    pid = processes[pid][0]
    if pid in excluded:
        break
    excluded.add(pid)
targets = {pid for pid, info in processes.items() if is_lanctl(info[3])} - excluded
while True:
    children = {pid for pid, info in processes.items() if info[0] in targets} - excluded
    expanded = targets | children
    if expanded == targets:
        break
    targets = expanded
if not targets:
    print("No hay procesos LANCTL en ejecución para tu usuario.")
    sys.exit(0)
for pid in sorted(targets):
    print(f"PID {pid}: {processes[pid][3]!r}")
if args.dry_run:
    sys.exit(0)
failed = set()


def active(pid):
    current = read_process(pid)
    return current and current[1] == processes[pid][1] and current[2] != "Z"


def send(pid, sig):
    # pidfd evita enviar señales a un PID reutilizado entre la lectura y kill.
    try:
        fd = os.pidfd_open(pid)
        try:
            if active(pid):
                signal.pidfd_send_signal(fd, sig)
        finally:
            os.close(fd)
    except ProcessLookupError:
        pass
    except OSError as exc:
        failed.add(pid)
        print(f"No se pudo cerrar PID {pid}: {exc}", file=sys.stderr)


for pid in sorted(targets, reverse=True):
    send(pid, signal.SIGTERM)
deadline = time.monotonic() + 2
while any(active(pid) for pid in targets) and time.monotonic() < deadline:
    time.sleep(0.05)
for pid in targets:
    if active(pid):
        send(pid, signal.SIGKILL)
deadline = time.monotonic() + 1
while any(active(pid) for pid in targets) and time.monotonic() < deadline:
    time.sleep(0.05)
remaining = {pid for pid in targets if active(pid)}
if remaining:
    print(f"Siguen activos: {sorted(remaining)}", file=sys.stderr)
print(f"Procesos cerrados: {len(targets - remaining)} de {len(targets)}.")
sys.exit(1 if remaining or failed else 0)
PY
