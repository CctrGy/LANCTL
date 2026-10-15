"""Manual native WebView smoke check, using an isolated empty data directory."""

import os
import tempfile
import time
from pathlib import Path


def main():
    with tempfile.TemporaryDirectory(prefix="lanip-native-smoke-") as directory:
        os.environ["LANCTL_DATA_DIR"] = directory
        from lanctl.core.file_transaction import atomic_write_text

        atomic_write_text(Path(directory) / "config/migration-v2.complete", "LANCTL-DATA-V2\n")
        from lanctl.core.config import load_config, save_config
        from lanctl.core.data_migration import ensure_data_layout

        ensure_data_layout()
        config = load_config()
        config.update(pluginSafeMode=True, projectsDirectory=str(Path(directory) / "vlf"))
        save_config(config)

        import webview

        from lanctl.apps.ip.interfaces.gui import desktop

        create_window = webview.create_window
        outcome = []

        def create(*args, **kwargs):
            window = create_window(*args, **kwargs)
            api = kwargs["js_api"]

            def verify():
                try:
                    deadline = time.monotonic() + 20
                    while time.monotonic() < deadline:
                        ready = window.evaluate_js(
                            "document.querySelector('#status-message').textContent.includes('Inventario conectado')"
                        )
                        if ready:
                            break
                        time.sleep(0.1)
                    assert ready, "desktop bridge did not initialize"
                    payload = api.bootstrap()
                    assert payload["ok"], payload
                    created = api.create_project("Smoke")
                    assert created["ok"] and not created["devices"], created
                    device = api._database().upsert(
                        [{"IP": "192.0.2.10", "MAC": "02:00:00:00:00:10"}]
                    )[0]
                    edited = api.update_device(device.device_id, {"alias": "TEST", "name": "Smoke"})
                    assert edited["ok"], edited
                    assert api.group_action("create", "LAB")["ok"]
                    assert api.group_action("add", "LAB", device.device_id)["ok"]
                    saved = api.save_project()
                    assert saved["ok"], saved
                    first = saved["activeProject"]
                    second = api.create_project("Other")
                    assert second["ok"] and not second["devices"], second
                    restored = api.use_project(first)
                    assert restored["ok"] and restored["devices"][0]["alias"] == "TEST", restored
                    assert "LAB" in restored["devices"][0]["groups"]
                    assert api.update_device(device.device_id, {"alias": "DISCARD"})["ok"]
                    assert api.use_project(second["activeProject"], discard=True)["ok"]
                    restored = api.use_project(first)
                    assert restored["devices"][0]["alias"] == "TEST", restored
                    outcome.append(
                        "PASS: native bridge, empty project, edit, groups, save, switch, restore, close"
                    )
                except Exception as error:
                    outcome.append(f"FAIL: {error}")
                finally:
                    # Exercises the native closing event and JS/RPC close handshake.
                    window.destroy()

            window.events.loaded += verify
            return window

        webview.create_window = create
        desktop.run_gui()
        print("\n".join(outcome))
        return 0 if outcome and outcome[0].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
