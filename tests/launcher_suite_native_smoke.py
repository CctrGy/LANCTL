"""Windows native GUI coordination smoke, isolated from the user's data.

Run explicitly: python tests/launcher_suite_native_smoke.py
Creates and closes only its own LANCTL and specialized test windows.
"""

import ctypes
import os
import subprocess
import tempfile
import time
from ctypes import wintypes
from pathlib import Path
from threading import Event, Thread


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
                    print("BOOTSTRAP", api.bootstrap().get("error", "OK"), flush=True)
                    wait_for(
                        lambda: window.evaluate_js(
                            "Boolean(document.querySelector('#version').textContent)"
                        )
                    )
                    handles = []
                    for launcher in ("lanwire", "lanrack", "lanaccess", "lanmon"):
                        print("CLICK", launcher, flush=True)
                        window.evaluate_js(
                            "document.querySelector('[data-launch=\"" + launcher + "\"]').click()"
                        )
                        child = wait_for(
                            lambda: next(
                                (
                                    s
                                    for s in coordinator.sessions()
                                    if s["launcher"] == launcher and s["controls"]
                                ),
                                None,
                            ),
                            timeout=25,
                        )
                        print("READY", launcher, child["pid"], flush=True)
                        handle = wait_for(lambda: window_for_process(child["pid"]))
                        handles.append(handle)
                        print(
                            "HANDLE",
                            handle,
                            "STATUS",
                            window.evaluate_js("document.querySelector('#status').textContent"),
                            flush=True,
                        )
                        wait_for(
                            lambda: window.evaluate_js(
                                "activity.some(text=>text.includes('GUI de "
                                + launcher.upper()
                                + " abierta'))"
                            )
                        )
                    assert {s["launcher"] for s in coordinator.sessions()} == {
                        "lanctl",
                        "lanwire",
                        "lanrack",
                        "lanaccess",
                        "lanmon",
                    }
                    for child_handle in handles:
                        ctypes.windll.user32.PostMessageW(wintypes.HWND(child_handle), 0x10, 0, 0)
                    wait_for(lambda: len(coordinator.sessions()) == 1, timeout=25)
                    outcome.append(
                        "PASS: all four LANCTL buttons open real simultaneous GUIs, ready IPC and clean native close"
                    )
                except Exception as error:
                    print(
                        "SESSIONS",
                        coordinator.sessions(),
                        "STATUS",
                        window.evaluate_js("document.querySelector('#status').textContent"),
                        "CHILDREN",
                        [(p.pid, p.poll()) for p in children],
                        flush=True,
                    )
                    outcome.append(f"FAIL: {type(error).__name__}: {error}")
                finally:
                    if handle:
                        ctypes.windll.user32.PostMessageW(wintypes.HWND(handle), 0x10, 0, 0)
                    if not closed.is_set():
                        api._desktop._closing = True
                        window.destroy()
                    verified.set()

            window.events.loaded += lambda: Thread(target=verify, daemon=True).start()
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
