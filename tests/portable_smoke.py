"""Explicit Windows portable smoke for freshly built, isolated executables.

Usage: python tests/portable_smoke.py PATH_TO_TEST_BUILD
Writes test data only under PATH_TO_TEST_BUILD/data/lanctl.
"""

import ctypes
import os
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path

from gui_coordination_smoke import wait_for, window_for_process


def main(directory):
    from lanctl import __version__

    root = Path(directory).resolve()
    (root / "LANCTL.portable").write_text("LANCTL-PORTABLE-V1\n", encoding="ascii")
    data = root / "data/lanctl"
    os.environ["LANCTL_DATA_DIR"] = str(data)
    from lanctl.core.file_transaction import atomic_write_text

    atomic_write_text(data / "config/migration-v2.complete", "LANCTL-DATA-V2\n")
    from lanctl.core.config import load_config, save_config
    from lanctl.core.coordination import Coordinator
    from lanctl.core.data_migration import ensure_data_layout

    ensure_data_layout()
    config = load_config()
    config.update(pluginSafeMode=True, projectsDirectory=str(data / "test-projects"))
    save_config(config)
    env = dict(os.environ)
    env.pop("LANCTL_DATA_DIR", None)  # Exercise real portable path resolution.
    env.pop("LANCTL_SECRET_DIR", None)
    options = dict(env=env, cwd=root, creationflags=subprocess.CREATE_NO_WINDOW)

    def run(launcher, *args, stdin=None):
        result = subprocess.run(
            [str(root / f"{launcher}.exe"), *args],
            input=stdin,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=45,
            **options,
        )
        assert result.returncode == 0, (launcher, args, result.stdout, result.stderr)
        return result.stdout

    for name in ("LANCTL", "lanip", "lanwire", "lanrack", "lanaccess", "lanmon"):
        assert __version__ in run(name, "--version")
    for mode in ("cli", "tui", "gui"):
        run("LANCTL", "settings", "--startup-interface", mode, "--close-gui-on-launch", "off")
        assert f'"{mode}"' in run("LANCTL", "settings", "--get", "startup.interface")
        assert "LANCTL" in run("LANCTL", "--cli", stdin="exit\n")
        if mode != "gui":
            assert "LANCTL" in run("LANCTL", stdin="exit\n")
    children, logs = [], []
    coordinator = Coordinator()

    def start(name, *args):
        log = (root / f"smoke-{len(children)}.log").open("wb")
        logs.append(log)
        process = subprocess.Popen(
            [str(root / f"{name}.exe"), *args], stdout=log, stderr=subprocess.STDOUT, **options
        )
        children.append(process)
        return process

    def close(launcher):
        for session in coordinator.sessions():
            if session["launcher"] == launcher and (handle := window_for_process(session["pid"])):
                ctypes.windll.user32.PostMessageW(wintypes.HWND(handle), 0x10, 0, 0)

    try:
        # Simultaneous no-argument invocations exercise the executable's GUI preference and lock.
        start("LANCTL")
        start("LANCTL")
        wait_for(
            lambda: (
                len(
                    [
                        s
                        for s in coordinator.sessions()
                        if s["launcher"] == "lanctl" and s["controls"]
                    ]
                )
                == 1
            ),
            40,
        )
        wait_for(lambda: sum(p.poll() is not None for p in children) == 1, 40)
        assert [p.returncode for p in children if p.poll() is not None] == [0]
        first = next(s for s in coordinator.sessions() if s["launcher"] == "lanctl")
        handle = wait_for(lambda: window_for_process(first["pid"]))
        ctypes.windll.user32.ShowWindow(wintypes.HWND(handle), 6)
        wait_for(lambda: ctypes.windll.user32.IsIconic(wintypes.HWND(handle)))
        run("LANCTL")
        wait_for(lambda: not ctypes.windll.user32.IsIconic(wintypes.HWND(handle)))
        child = start("lanip", "--gui")
        wait_for(
            lambda: any(s["launcher"] == "lanip" and s["controls"] for s in coordinator.sessions()),
            40,
        )
        assert {s["launcher"] for s in coordinator.sessions()} == {"lanctl", "lanip"}
        close("lanctl")
        wait_for(lambda: all(s["launcher"] != "lanctl" for s in coordinator.sessions()))
        assert child.poll() is None
        close("lanip")
        wait_for(lambda: not coordinator.sessions())
        print(
            "PASS: six portable launchers, CLI/TUI/GUI preference, explicit CLI override, concurrent GUI lock, restore, independent close"
        )
    finally:
        close("lanctl")
        close("lanip")
        for process in children:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=10)
        for log in logs:
            log.close()


if __name__ == "__main__":
    main(sys.argv[1])
