"""Explicit native smoke for specialized GUIs; all storage is temporary."""

import importlib
import os
import sys
import tempfile
import time
from pathlib import Path


def main(launcher):
    modules = {
        "lanwire": "lanctl.apps.wire.cli.main",
        "lanrack": "lanctl.apps.rack.cli",
        "lanaccess": "lanctl.apps.access.manager_cli",
        "lanmon": "lanctl.bootstrap.lanmon",
    }
    with tempfile.TemporaryDirectory(prefix=launcher + "-gui-native-") as temporary:
        root = Path(temporary)
        os.environ["LANCTL_DATA_DIR"] = str(root)
        os.environ["LANCTL_SECRET_DIR"] = str(root / "secrets")
        marker = root / "config/migration-v2.complete"
        marker.parent.mkdir(parents=True)
        marker.write_text("LANCTL-DATA-V2\n")
        from lanctl.core.config import load_config, save_config
        from lanctl.core.database import DeviceDatabase
        from lanctl.core.projects.vlf import create_project

        config = load_config()
        config.update(
            database=str(root / "devices.json"),
            groups=str(root / "groups.json"),
            physicalDatabase=str(root / "physical.db"),
            credentials=str(root / "access.vault"),
            monitorDatabase=str(root / "monitor.db"),
            monitorLock=str(root / "monitor.lock"),
            pluginSafeMode=True,
        )
        project = root / "Office.vlf"
        create_project(project, name="Office", config=config, initialize_reserved=False)
        config.update(activeProject=str(project), projectWorkspace=None)
        save_config(config)
        device = DeviceDatabase(config["database"]).upsert(
            [{"IP": "192.0.2.10", "MAC": "02:00:00:00:00:10"}]
        )[0]
        from lanctl.apps.wire.gui_service import WireGuiService

        physical = WireGuiService(config["physicalDatabase"])
        rack = physical.create({"prefix": "RK", "kind": "rack", "name": "Principal", "units": 24})[
            "id"
        ]
        switch = physical.create(
            {"prefix": "SW", "kind": "switch.5ports", "name": "Switch oficina"}
        )["id"]
        record = next(r for r in physical.snapshot()["records"] if r["id"] == switch)
        physical.update(switch, record["revision"], {"rack": rack, "unit": 18})
        import webview

        original = webview.create_window
        outcome = []

        def create(*args, **kwargs):
            window = original(*args, **kwargs)
            api = kwargs["js_api"]

            def verify():
                try:
                    deadline = time.monotonic() + 20
                    while time.monotonic() < deadline:
                        if window.evaluate_js(
                            "document.querySelector('#connection').textContent==='Sesión local'"
                        ):
                            break
                        time.sleep(0.1)
                    else:
                        raise AssertionError("WebView bridge timeout")
                    payload = api.bootstrap()
                    assert payload["ok"], payload
                    assert payload["launcher"] == launcher
                    if launcher == "lanwire":
                        result = api.wire_create(
                            {"prefix": "WL", "kind": "wire.copper", "name": "Cable nativo"}
                        )
                        assert result["ok"], result
                        row = next(x for x in api.bootstrap()["records"] if x["id"] == result["id"])
                        assert api.wire_connect(
                            row["id"], row["revision"], [{"device": switch, "port": "X1"}]
                        )["ok"]
                    elif launcher == "lanrack":
                        assert payload["records"][0]["occupants"][0]["unit"] == 18
                    elif launcher == "lanaccess":
                        assert api.access_set(
                            device.device_id, "ssh", "native", "native-secret", "native-secret"
                        )["ok"]
                        assert "native-secret" not in str(api.bootstrap())
                    else:
                        assert payload["session"] is None
                        assert api.monitor_samples(device.device_id)["ok"]
                    outcome.append(
                        "PASS: "
                        + launcher
                        + " native bridge, real services, project context and close"
                    )
                except Exception as error:
                    outcome.append("FAIL: " + launcher + " " + str(error))
                finally:
                    api._closing = True
                    window.destroy()

            window.events.loaded += verify
            return window

        webview.create_window = create
        result = importlib.import_module(modules[launcher]).main(["--gui"])
        print("\n".join(outcome))
        return result or (0 if outcome and outcome[0].startswith("PASS") else 1)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
