"""Windows native GUI coordination smoke, isolated from the user's data.

Run explicitly: python tests/gui_coordination_smoke.py
Creates and closes only its own LANCTL/LANIP test windows.
"""

import ctypes
import os
import subprocess
import tempfile
import time
from ctypes import wintypes
from pathlib import Path
from threading import Event


def wait_for(check, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = check()
        if value:
            return value
        time.sleep(0.1)
    raise AssertionError("Native GUI check timed out")


def window_for_process(pid):
    user32 = ctypes.windll.user32
    matches = []
    callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def visit(handle, _):
        owner = wintypes.DWORD()
        user32.GetWindowThreadProcessId(handle, ctypes.byref(owner))
        if owner.value == pid and user32.IsWindowVisible(handle):
            matches.append(handle)
        return True

    user32.EnumWindows(callback(visit), 0)
    return matches[0] if matches else None


def main():
    if os.name != "nt":
        print("This smoke requires a Windows desktop session")
        return 2
    with tempfile.TemporaryDirectory(prefix="lanctl-coordination-smoke-") as directory:
        os.environ["LANCTL_DATA_DIR"] = directory
        from lanctl.core.file_transaction import atomic_write_text

        atomic_write_text(Path(directory) / "config/migration-v2.complete", "LANCTL-DATA-V2\n")
        from lanctl.core.config import load_config, save_config
        from lanctl.core.data_migration import ensure_data_layout

        ensure_data_layout()
        config = load_config()
        config.update(
            pluginSafeMode=True,
            closeGuiOnLaunch=False,
            startupInterface="gui",
            projectsDirectory=str(Path(directory) / "projects-test"),
        )
        save_config(config)
        import webview

        from lanctl.apps.suite.processes import launcher_command, process_options
        from lanctl.bootstrap.lanctl import main as launch
        from lanctl.core.coordination import Coordinator

        coordinator = Coordinator()
        original = webview.create_window
        outcome = []
        children = []
        verified = Event()
        popen = subprocess.Popen

        def track(*args, **kwargs):
            process = popen(*args, **kwargs)
            children.append(process)
            return process

        def create(*args, **kwargs):
            window = original(*args, **kwargs)
            api = kwargs["js_api"]
            closed = Event()
            window.events.closed += closed.set

            def verify():
                handle = None
                try:
                    wait_for(lambda: window.evaluate_js("Boolean(state.version)"))
                    result = api.launch_gui("lanip")
                    assert result["ok"] and not result.get("closed"), result
                    sessions = coordinator.sessions()
                    assert {s["launcher"] for s in sessions} == {"lanctl", "lanip"}
                    child = next(s for s in sessions if s["launcher"] == "lanip")
                    handle = wait_for(lambda: window_for_process(child["pid"]))
                    ctypes.windll.user32.ShowWindow(wintypes.HWND(handle), 6)  # minimize own child
                    wait_for(lambda: ctypes.windll.user32.IsIconic(wintypes.HWND(handle)))
                    duplicate = subprocess.run(
                        launcher_command("lanip", "--gui"),
                        creationflags=subprocess.CREATE_NO_WINDOW,
                        timeout=20,
                        capture_output=True,
                        **process_options(),
                    )
                    assert duplicate.returncode == 0, duplicate.stderr
                    wait_for(lambda: not ctypes.windll.user32.IsIconic(wintypes.HWND(handle)))
                    foreground = ctypes.windll.user32.GetForegroundWindow
                    foreground.restype = wintypes.HWND
                    wait_for(lambda: foreground() == handle)
                    assert len([s for s in coordinator.sessions() if s["launcher"] == "lanip"]) == 1
                    wait_for(
                        lambda: window.evaluate_js("state.sessions.some(s=>s.launcher==='lanip')")
                    )
                    ctypes.windll.user32.PostMessageW(wintypes.HWND(handle), 0x10, 0, 0)
                    wait_for(lambda: all(s["launcher"] != "lanip" for s in coordinator.sessions()))
                    wait_for(
                        lambda: window.evaluate_js("!state.sessions.some(s=>s.launcher==='lanip')")
                    )
                    assert any(s["launcher"] == "lanctl" for s in coordinator.sessions())
                    from lanctl.core.config import update_config

                    update_config(lambda settings: settings.update(closeGuiOnLaunch=True))
                    result = api.launch_gui("lanip")
                    assert result["ok"] and result["closed"], result
                    assert closed.wait(10), "LANCTL did not close after opening its launcher"
                    assert children[-1].poll() is None, "Closing LANCTL stopped the launcher"
                    child = next(s for s in coordinator.sessions() if s["launcher"] == "lanip")
                    handle = wait_for(lambda: window_for_process(child["pid"]))
                    outcome.append(
                        "PASS: default GUI, simultaneous launchers, duplicate focus, restore, close feedback, child survives parent"
                    )
                except Exception as error:
                    outcome.append(f"FAIL: {type(error).__name__}: {error}")
                finally:
                    if handle:
                        ctypes.windll.user32.PostMessageW(wintypes.HWND(handle), 0x10, 0, 0)
                    if not closed.is_set():
                        window.destroy()
                    verified.set()

            window.events.loaded += verify
            return window

        webview.create_window = create
        # Track only children spawned during this isolated test for bounded cleanup.
        subprocess.Popen = track
        try:
            launch([])
            assert verified.wait(30), "GUI verification did not finish"
        finally:
            subprocess.Popen = popen
            for process in children:
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=10)
        print("\n".join(outcome))
        return 0 if outcome and outcome[0].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
