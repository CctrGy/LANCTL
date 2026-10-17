"""Local GUI process adapters; never interpolate commands into a shell."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from collections import deque
from pathlib import Path
from threading import Lock, Thread

from lanctl.core.paths import application_directory


def launcher_command(launcher="lanctl", *arguments):
    if launcher not in {"lanctl", "lanip", "lanwire", "lanrack", "lanaccess", "lanmon"}:
        raise ValueError("launcher gráfico no disponible")
    if getattr(sys, "frozen", False):
        suffix = ".exe" if sys.platform == "win32" else ""
        return [str(Path(sys.executable).with_name(launcher + suffix)), *arguments]
    if launcher == "lanctl":
        return [sys.executable, "-m", "lanctl", *arguments]
    if launcher == "lanip":
        return [sys.executable, "-m", "lanctl.apps.ip", *arguments]
    return [sys.executable, "-m", "lanctl", launcher, *arguments]


def process_options(context_launcher=None):
    env = dict(os.environ, PYTHONUNBUFFERED="1", PYTHONIOENCODING="utf-8")
    if not getattr(sys, "frozen", False):
        source = str(application_directory() / "src")
        env["PYTHONPATH"] = source + os.pathsep + env.get("PYTHONPATH", "")
    if context_launcher:
        from lanctl.core.config import load_config
        from lanctl.core.session_context import child_environment

        env = child_environment(context_launcher, load_config(), env)
    return {"cwd": str(application_directory()), "env": env}


def open_system_cli(launcher="lanctl"):
    command = launcher_command(launcher, "--cli")
    options = process_options(context_launcher=launcher)
    if sys.platform == "win32":
        # CREATE_NEW_CONSOLE respects the user's Windows default terminal host.
        subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE, **options)
    elif sys.platform.startswith("linux"):
        terminal = shutil.which("x-terminal-emulator") or shutil.which("xterm")
        if not terminal:
            raise RuntimeError(
                "No hay terminal predeterminada: instala x-terminal-emulator o xterm."
            )
        subprocess.Popen([terminal, "-e", *command], **options)
    else:
        raise RuntimeError("El CLI externo de la GUI admite Windows y Linux.")


class EmbeddedCli:
    """Own one real root CLI; bounded output and no command execution in the GUI process."""

    def __init__(self):
        self._process = None
        self._output = deque(maxlen=20000)
        self._lock = Lock()

    def start(self):
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                return
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            self._process = subprocess.Popen(
                launcher_command("lanctl", "--cli"),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=flags,
                **process_options(),
            )
            Thread(target=self._read, args=(self._process,), daemon=True).start()

    def _read(self, process):
        try:
            for char in iter(lambda: process.stdout.read(1), ""):
                with self._lock:
                    self._output.append(char)
        finally:
            process.stdout.close()

    def send(self, line):
        if not isinstance(line, str) or len(line) > 4096 or any(c in line for c in "\n\r\x00"):
            raise ValueError("entrada de consola no válida")
        with self._lock:
            if self._process is None or self._process.poll() is not None:
                raise RuntimeError("La consola está cerrada. Vuelve a abrir Terminal.")
            self._process.stdin.write(line + "\n")
            self._process.stdin.flush()

    def output(self):
        with self._lock:
            text = "".join(self._output)
            self._output.clear()
            return {
                "text": text,
                "running": self._process is not None and self._process.poll() is None,
            }

    def close(self):
        with self._lock:
            process = self._process
            self._process = None
        if process is not None:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
            if process.stdin:
                process.stdin.close()
