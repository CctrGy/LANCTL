"""Opt-in native Qt regression for the RPC bridge of all six GUI launchers.

Run: QT_QPA_PLATFORM=offscreen QTWEBENGINE_DISABLE_SANDBOX=1 \
     python tests/gui_project_bridge_smoke.py
Uses temporary data and closes only its own windows. No network probes are sent.
For a smaller native check, add --launcher lanip (or another launcher).
Single-launcher mode does not certify cross-window synchronization.
Add --close-decision save|discard|cancel to exercise the real close form with
a dirty temporary project (discard is currently available on LANIP only).
Add --scan-fixture no-project|project with --launcher lanip to exercise the
scan button through Qt/RPC/CLI with controlled discovery; --scan-failure
checks the recovery path. These options never certify physical LAN discovery.
"""

import argparse
import faulthandler
import ipaddress
import json
import os
import tempfile
import time
import traceback
import zipfile
from contextlib import ExitStack
from pathlib import Path
from threading import Event, current_thread
from threading import enumerate as active_threads
from unittest.mock import patch


def wait_for(check, timeout=20):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = check()
        if result:
            return result
        time.sleep(0.05)
    raise AssertionError("Native GUI bridge check timed out")


def project_data(path):
    # HistoryWriter appends audit events to VLF even while inventory is dirty.
    # A cancelled close must preserve project data, not suppress that audit log.
    with zipfile.ZipFile(path) as archive:
        result = {
            name: archive.read(name)
            for name in archive.namelist()
            if not name.endswith("/")
            and not name.startswith("logs/")
            and name not in {"project.info", "meta/checksum"}
        }
        info = json.loads(archive.read("project.info"))
        for key in ("updated", "contentHash"):
            info.pop(key, None)
        result["project.info"] = info
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--launcher",
        choices=("lanctl", "lanip", "lanwire", "lanrack", "lanaccess", "lanmon"),
        help="Check one native window only; omit for the original six-window context checks.",
    )
    parser.add_argument(
        "--close-decision",
        choices=("save", "discard", "cancel"),
        help="Exercise native close with dirty temporary data; requires --launcher.",
    )
    parser.add_argument(
        "--close-peer",
        action="store_true",
        help="Keep a second launcher alive during close; requires --close-decision.",
    )
    parser.add_argument(
        "--scan-fixture",
        choices=("no-project", "project"),
        help="Check LANIP scan through native Qt with controlled discovery and temporary data.",
    )
    parser.add_argument(
        "--scan-failure",
        action="store_true",
        help="Inject a controlled discovery error; requires --scan-fixture.",
    )
    args = parser.parse_args()
    if args.close_decision and not args.launcher:
        parser.error("--close-decision requires --launcher")
    if args.close_peer and not args.close_decision:
        parser.error("--close-peer requires --close-decision")
    if args.close_decision == "discard" and args.launcher != "lanip":
        parser.error("The discard close form is currently available on LANIP only")
    if args.scan_fixture and (args.launcher != "lanip" or args.close_decision):
        parser.error(
            "--scan-fixture requires --launcher lanip and cannot combine with --close-decision"
        )
    if args.scan_failure and not args.scan_fixture:
        parser.error("--scan-failure requires --scan-fixture")
    selected = (
        (args.launcher,)
        if args.launcher
        else ("lanctl", "lanip", "lanwire", "lanrack", "lanaccess", "lanmon")
    )
    if args.close_peer:
        selected = (*selected, "lanmon" if args.launcher != "lanmon" else "lanwire")
    with tempfile.TemporaryDirectory(prefix="lanctl-bridge-") as directory, ExitStack() as patches:
        os.environ["LANCTL_DATA_DIR"] = directory
        marker = Path(directory) / "config/migration-v2.complete"
        marker.parent.mkdir(parents=True)
        marker.write_text("LANCTL-DATA-V2\n", encoding="utf-8")

        import webview

        from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
        from lanctl.apps.suite.gui import SuiteApi
        from lanctl.apps.suite.launcher_gui import LauncherApi
        from lanctl.core.resources import bundled_path

        scan_calls = []
        if args.scan_fixture:
            from lanctl.apps.ip.domain.models import Device
            from lanctl.core.config import load_config, save_config

            settings = load_config()
            settings.update(range="192.0.2.0/24", workers=1, timeout=0.1)
            save_config(settings)

            def discover(scanner, **options):
                scan_calls.append({"network": str(scanner.network), **options})
                if args.scan_failure:
                    raise OSError("controlled discovery failure")
                device = Device(
                    ip="192.0.2.42", mac="02:00:00:00:00:42", alias="Native scan", cnf="O"
                )
                scanner._mark_discovery(device.ip, device.mac, "ARP")
                scanner.response_times_ms[device.ip] = {"arp": 1.25}
                return [device]

            patches.enter_context(
                patch(
                    "lanctl.apps.ip.infrastructure.services.lan_scanner.LanScanner.scan", discover
                )
            )
            patches.enter_context(
                patch(
                    "lanctl.apps.ip.interfaces.cli.commands.list.local_ipv4",
                    return_value=ipaddress.IPv4Address("192.0.2.5"),
                )
            )

        project = None
        original_project = None
        if args.close_decision:
            from lanctl.core.config import load_config
            from lanctl.core.database import DeviceDatabase

            created = SuiteApi().create_project("Native Close", directory)
            assert created["ok"], created
            project = Path(load_config()["activeProject"])
            original_project = project_data(project)
            DeviceDatabase(load_config()["database"]).add_manual_device(alias="Pending close")

        if args.scan_fixture == "project":
            from lanctl.core.config import load_config

            created = SuiteApi().create_project("Native Scan", directory)
            assert created["ok"], created
            project = Path(load_config()["activeProject"])

        if args.scan_failure:
            from lanctl.core.config import load_config
            from lanctl.core.database import DeviceDatabase

            DeviceDatabase(load_config()["database"]).add_manual_device(alias="Preserved device")
            if project:
                original_project = project_data(project)

        with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
            apis = [
                (
                    name,
                    SuiteApi()
                    if name == "lanctl"
                    else DesktopApi()
                    if name == "lanip"
                    else LauncherApi(name),
                )
                for name in selected
            ]
        windows = []
        for name, api in apis:
            page = "suite" if name == "lanctl" else "index" if name == "lanip" else "launcher"
            window = webview.create_window(
                name, bundled_path(f"gui/{page}.html").as_uri(), js_api=api, hidden=True
            )
            desktop = (
                api._desktop
                if name == "lanctl"
                else api
                if name == "lanip"
                else api._suite._desktop
            )
            desktop.attach_window(window)
            if name not in {"lanctl", "lanip"}:
                api._window = window
            from lanctl.apps.suite.native_close import install_native_close

            install_native_close(window, api, launcher=name)
            windows.append((name, window))
        results = []
        failures = []
        verified = Event()
        baseline_threads = {thread.ident for thread in active_threads()}

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
                if args.launcher is None:
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
                if "lanctl" in selected:
                    # P94: real Qt page opens the integrated settings catalog.
                    suite_window = next(window for name, window in windows if name == "lanctl")
                    settings = invoke(
                        suite_window,
                        "(async()=>{await openSettingsWindow();return {"
                        "open:document.querySelector('#suite-settings').open,"
                        "count:document.querySelectorAll('#suite-settings .ss-card').length,"
                        "languageSelect:document.querySelector('[data-path=\"localization.language\"] select')!==null,"
                        "languageOptions:Array.from(document.querySelectorAll('[data-path=\"localization.language\"] select option')).map(o=>({value:o.value,label:o.textContent}))}})()",
                    )
                    assert settings["open"] and settings["count"] > 50, settings
                    assert settings["languageSelect"] and settings["languageOptions"], settings
                if args.scan_fixture:
                    from lanctl.core.config import load_config
                    from lanctl.core.database import DeviceDatabase
                    from lanctl.core.projects.workspace import activate_project_workspace

                    window = windows[0][1]
                    wait_for(
                        lambda: window.evaluate_js(
                            "typeof desktopReady !== 'undefined' && desktopReady && !desktopBusy"
                        )
                    )
                    selection = load_config().get("activeProject")
                    before = DeviceDatabase(load_config()["database"]).load()
                    window.evaluate_js(
                        "document.querySelector('#scan-profile').value='fast';window.lanipScanTarget=null;document.querySelector('#scan-network').click();void 0"
                    )
                    wait_for(lambda: bool(scan_calls))
                    wait_for(lambda: window.evaluate_js("!desktopBusy"))
                    assert len(scan_calls) == 1, len(scan_calls)
                    assert scan_calls[0]["network"] == "192.0.2.0/24"
                    assert scan_calls[0]["discovery"] == "arp"
                    assert scan_calls[0]["attempts"] == 1
                    assert not invoke(window, "call('scan_status')")["running"]
                    assert load_config().get("activeProject") == selection
                    assert window.evaluate_js("document.querySelector('#cancel-scan').hidden")
                    assert window.evaluate_js("!document.querySelector('#scan-network').disabled")
                    after = DeviceDatabase(load_config()["database"]).load()
                    if args.scan_failure:
                        assert any(item.alias == "Preserved device" for item in before)
                        assert [item.to_dict() for item in after] == [
                            item.to_dict() for item in before
                        ]
                        if project:
                            assert project_data(project) == original_project
                        assert window.evaluate_js(
                            "document.querySelector('#status-message').textContent.includes('controlled discovery failure')"
                        )
                        assert not window.evaluate_js(
                            "state.devices.some(device=>device.alias==='Native scan')"
                        )
                    else:
                        assert any(device.alias == "Native scan" for device in after)
                        assert window.evaluate_js(
                            "state.devices.some(device=>device.alias==='Native scan' && device.active===true)"
                        )
                        assert window.evaluate_js(
                            "Array.from(document.querySelectorAll('tbody tr')).some(row=>row.textContent.includes('192.0.2.42'))"
                        )
                        if project:
                            saved = invoke(window, "call('save_project')")
                            assert saved["ok"], saved
                            activate_project_workspace(project, refresh=True, discard_changes=True)
                            assert any(
                                device.alias == "Native scan"
                                for device in DeviceDatabase(load_config()["database"]).load()
                            )

                if args.close_decision:
                    name, window = windows[0]
                    from lanctl.core.config import load_config
                    from lanctl.core.database import DeviceDatabase
                    from lanctl.core.projects.save_policy import workspace_is_dirty
                    from lanctl.core.projects.workspace import activate_project_workspace

                    assert invoke(window, "call('project_state')")["dirty"]
                    close_function = (
                        "suiteClose"
                        if name == "lanctl"
                        else "desktopClose"
                        if name == "lanip"
                        else "launcherClose"
                    )
                    window.evaluate_js(f"void {close_function}()")
                    selector = (
                        "#confirmation"
                        if name == "lanctl"
                        else "#save-dialog"
                        if name == "lanip"
                        else "dialog[aria-labelledby='app-notice-title']"
                    )
                    wait_for(
                        lambda: window.evaluate_js(
                            f"Boolean(document.querySelector({json.dumps(selector)})?.open)"
                        )
                    )
                    if name == "lanctl":
                        button = (
                            "#confirmation-cancel"
                            if args.close_decision == "cancel"
                            else "#confirmation-accept"
                        )
                    elif name == "lanip":
                        button = f"#save-dialog [data-decision='{args.close_decision}']"
                    else:
                        button = (
                            "#app-notice-cancel"
                            if args.close_decision == "cancel"
                            else "#app-notice-accept"
                        )
                    window.evaluate_js(
                        f"document.querySelector({json.dumps(button)}).click();void 0"
                    )
                    if args.close_decision == "cancel":
                        wait_for(
                            lambda: window.evaluate_js(
                                f"!document.querySelector({json.dumps(selector)}).open"
                            )
                        )
                        assert not window.events.closed.wait(0.3)
                        assert invoke(window, "call('project_state')")["dirty"]
                        assert project_data(project) == original_project

                    else:
                        assert window.events.closed.wait(20), "Native close was not confirmed"
                        assert not workspace_is_dirty(load_config())
                        if args.close_decision == "discard":
                            assert project_data(project) == original_project
                        activate_project_workspace(project, refresh=True, discard_changes=True)
                        aliases = {
                            device.alias
                            for device in DeviceDatabase(load_config()["database"]).load()
                        }
                        assert ("Pending close" in aliases) == (args.close_decision == "save"), (
                            aliases
                        )
                    if args.close_peer:
                        peer_name, peer = windows[1]
                        assert not peer.events.closed.is_set(), peer_name
                        peer_state = invoke(peer, "call('project_state')")
                        assert peer_state["ok"], peer_state
                        assert peer_state["dirty"] == (args.close_decision == "cancel")
                        assert load_config()["activeProject"] == str(project)
                        assert peer.evaluate_js("state.projectContext[0]") == str(project)
                        assert not peer.events.closed.is_set(), peer_name
            except Exception:
                failures.append(traceback.format_exc())
            finally:
                for _, window in windows:
                    if not window.events.closed.is_set():
                        window.destroy()
                verified.set()

        webview.start(verify, gui="qt")
        assert verified.wait(25), "Native verification did not finish after the window closed"
        # The plugin manager belongs to this isolated test process. Stop its
        # watcher before removing the temporary data tree.
        from lanctl.core.plugins.manager import get_plugin_manager

        get_plugin_manager().close()
        # Window.closed is not enough: pywebview may leave a non-daemon RPC
        # thread waiting for a JS return after the Qt event loop has stopped.
        if args.close_decision:
            remaining = [
                thread
                for thread in active_threads()
                if not thread.daemon
                and thread is not current_thread()
                and thread.ident not in baseline_threads
            ]
            deadline = time.monotonic() + 3
            for thread in remaining:
                thread.join(max(0, deadline - time.monotonic()))
            stuck = [thread.name for thread in remaining if thread.is_alive()]
            if stuck:
                faulthandler.dump_traceback()
            assert not stuck, f"Native close left non-daemon threads: {stuck}"
        assert not failures, failures
        assert len(results) == len(selected), results
        print(
            json.dumps(
                {
                    "passed": results,
                    "checks": "real pages, RPC and context guards",
                    "crossWindowChecked": args.launcher is None,
                    "settingsChecked": "lanctl" in selected,
                    "scanChecked": False,
                    "scanBridgeChecked": args.scan_fixture is not None,
                    "scanFixture": args.scan_fixture,
                    "controlledDiscoveryFailure": args.scan_failure,
                    "closeDecisionsChecked": args.close_decision is not None,
                    "closeDecision": args.close_decision,
                    "closePeerChecked": args.close_peer,
                }
            )
        )


if __name__ == "__main__":
    main()
