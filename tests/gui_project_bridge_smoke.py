"""Opt-in native Qt regression for the RPC bridge of all six GUI launchers.

Run: QT_QPA_PLATFORM=offscreen QTWEBENGINE_DISABLE_SANDBOX=1 \
     python tests/gui_project_bridge_smoke.py
Uses temporary data and closes only its own windows. No network scan is run.
"""

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch


def wait_for(check, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = check()
        if result:
            return result
        time.sleep(0.05)
    raise AssertionError("Native GUI bridge check timed out")


def main():
    with tempfile.TemporaryDirectory(prefix="lanctl-bridge-") as directory:
        os.environ["LANCTL_DATA_DIR"] = directory
        marker = Path(directory) / "config/migration-v2.complete"
        marker.parent.mkdir(parents=True)
        marker.write_text("LANCTL-DATA-V2\n", encoding="utf-8")

        import webview

        from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
        from lanctl.apps.suite.gui import SuiteApi
        from lanctl.apps.suite.launcher_gui import LauncherApi
        from lanctl.core.resources import bundled_path

        with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
            apis = [("lanctl", SuiteApi()), ("lanip", DesktopApi())]
            apis.extend(
                (name, LauncherApi(name)) for name in ("lanwire", "lanrack", "lanaccess", "lanmon")
            )
        windows = []
        for name, api in apis:
            page = "suite" if name == "lanctl" else "index" if name == "lanip" else "launcher"
            window = webview.create_window(
                name, bundled_path(f"gui/{page}.html").as_uri(), js_api=api, hidden=True
            )
            windows.append((name, window))
        results = []
        failures = []

        def invoke(window, expression):
            window.evaluate_js(
                "window.bridgeResult=null;"
                + expression
                + ".then(value=>window.bridgeResult={value})"
                + ".catch(error=>window.bridgeResult={error:String(error)});void 0"
            )
            result = wait_for(lambda: window.evaluate_js("window.bridgeResult"))
            assert "error" not in result, result
            return result["value"]

        def verify():
            try:
                for name, window in windows:
                    assert window.events.loaded.wait(20)
                    wait_for(
                        lambda: window.evaluate_js(
                            "typeof state!=='undefined' && Array.isArray(state.projectActions)"
                        )
                    )
                    # Initial inventory refreshes may legitimately hold the lock.
                    deadline = time.monotonic() + 10
                    while True:
                        result = invoke(
                            window, "call('project_state').catch(e=>({error:e.message}))"
                        )
                        if "operación en curso" not in result.get("error", ""):
                            break
                        assert time.monotonic() < deadline, result
                        time.sleep(0.1)
                    assert result["ok"] and "dirty" in result, (name, result)
                    # The envelope still rejects invalid context and invalid targets.
                    rejected = invoke(
                        window,
                        "window.pywebview.api.project_call(['stale-project'],'project_state',[])",
                    )
                    assert not rejected["ok"], (name, rejected)
                    rejected = invoke(
                        window,
                        "window.pywebview.api.project_call(state.projectContext,'__init__',[])",
                    )
                    assert not rejected["ok"], (name, rejected)
                    results.append(name)
                # P103: selection converges even without RootInterfaceAgent notifications.
                from lanctl.core.config import load_config
                from lanctl.core.database import DeviceDatabase

                suite = apis[0][1]
                lanip_window = next(window for name, window in windows if name == "lanip")
                for label in ("Native First", "Native Second"):
                    created = suite.create_project(label, directory)
                    assert created["ok"], created
                    path = load_config()["activeProject"]
                    DeviceDatabase(load_config()["database"]).add_manual_device(alias=label)
                    wait_for(
                        lambda: lanip_window.evaluate_js(
                            "state.projectContext[0]===" + json.dumps(path)
                        )
                    )
                    # Inventory may be read in the same snapshot just before the add.
                    lanip_window.evaluate_js("window.desktopDataChanged=true")
                    wait_for(
                        lambda: lanip_window.evaluate_js(
                            "state.devices.some(d=>d.alias===" + json.dumps(label) + ")"
                        )
                    )
                    for other_name, other_window in windows:
                        if other_name in {"lanctl", "lanip"}:
                            continue
                        wait_for(
                            lambda other_window=other_window: other_window.evaluate_js(
                                "state.projectContext[0]===" + json.dumps(path)
                            )
                        )
                    assert suite.save_project()["ok"]
                # P94: real Qt page opens the integrated settings catalog.
                suite_window = next(window for name, window in windows if name == "lanctl")
                settings = invoke(
                    suite_window,
                    "(async()=>{await openSettingsWindow();return {"
                    "open:document.querySelector('#suite-settings').open,"
                    "count:document.querySelectorAll('#suite-settings .ss-card').length}})()",
                )
                assert settings["open"] and settings["count"] > 50, settings
            except Exception as exc:
                failures.append(str(exc))
            finally:
                for _, window in windows:
                    window.destroy()

        webview.start(verify, gui="qt")
        assert not failures, failures
        assert len(results) == 6, results
        print(json.dumps({"passed": results, "checks": "real pages, RPC and context guards"}))


if __name__ == "__main__":
    main()
