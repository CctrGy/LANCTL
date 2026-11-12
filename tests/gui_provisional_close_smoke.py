"""Opt-in single-window Qt check of the provisional native-close adapter.

Uses temporary data, one small WebView, no network and no real user projects.
This verifies the adapter's real RPC/state/closed events, not launcher startup.
"""

import argparse
import json
import os
import tempfile
import time
from pathlib import Path
from threading import Event, RLock


def wait_for(check, timeout=15):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if result := check():
            return result
        time.sleep(0.05)
    raise AssertionError("Provisional native close check timed out")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision", choices=("save", "discard"), default="discard")
    parser.add_argument("--peer", action="store_true")
    parser.add_argument("--reject", action="store_true")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="lanctl-draft-native-") as temporary:
        root = Path(temporary)
        os.environ["LANCTL_DATA_DIR"] = str(root)
        marker = root / "config/migration-v2.complete"
        marker.parent.mkdir(parents=True)
        marker.write_text("LANCTL-DATA-V2\n")
        import webview

        from lanctl.apps.suite.native_close import NativeClose, ProvisionalClose
        from lanctl.core.config import load_config
        from lanctl.core.coordination import Coordinator
        from lanctl.core.database import DeviceDatabase
        from lanctl.core.projects.provisional import (
            claim_provisional_close,
            join_provisional_workspace,
            prepare_provisional_close,
            prepare_provisional_workspace,
            provisional_operation,
        )

        coordinator = Coordinator(root / "coordinator.db")
        owner = coordinator.register("lanip", "gui")
        draft = prepare_provisional_workspace(root=root / "drafts")
        join_provisional_workspace(draft, owner, coordinator=coordinator)
        if args.peer:
            peer = coordinator.register("lanwire", "gui")
            join_provisional_workspace(draft, peer, coordinator=coordinator)
        with provisional_operation(
            draft, owner, coordinator=coordinator, base=load_config()
        ) as cfg:
            DeviceDatabase(cfg["database"]).add_manual_device(idf="PC-001")
        claim = claim_provisional_close(draft, owner, coordinator=coordinator)
        destination = root / "Saved.vlf"
        prepared = prepare_provisional_close(
            draft,
            owner,
            claim["token"],
            coordinator=coordinator,
            decision=args.decision,
            destination=destination,
            name="Saved",
            base=load_config(),
        )
        assert prepared["ready"]
        manager = None
        window = None

        class Api:
            def __init__(self):
                self._lock = RLock()

            def prepare_native_close(self):
                return manager.prepare(args.decision)

        api = Api()
        window = webview.create_window(
            "Provisional close check",
            html="<html><body>Temporary close check</body></html>",
            js_api=api,
            hidden=True,
        )
        calls = []

        def close(decision):
            state = json.loads((draft.root / "workspace.json").read_text())
            assert owner in state["owners"] and "closeLease" in state
            calls.append(decision)
            if args.reject:
                return {"ok": False, "closed": False, "errorId": "controlled-rejection"}
            window.destroy()
            return {"ok": True, "closed": True}

        manager = NativeClose(window, api, close)
        manager.provisional = ProvisionalClose(
            draft, owner, claim["token"], coordinator, args.decision
        )
        finished = Event()
        failures = []

        def verify():
            try:
                assert window.events.loaded.wait(15)
                wait_for(
                    lambda: window.evaluate_js(
                        "Boolean(window.pywebview?.api?.prepare_native_close)"
                    )
                )
                window.evaluate_js(
                    "window.pywebview.api.prepare_native_close().then(result=>{"
                    "window.pywebview.state.lanctl_close_receipt=result.token;});void 0"
                )

                def resolved():
                    state = json.loads((draft.root / "workspace.json").read_text())
                    return state if "closeLease" not in state else None

                state = wait_for(resolved)
                assert calls == [args.decision]
                assert DeviceDatabase(cfg["database"]).load()[0].idf == "PC-001"
                if args.reject:
                    assert owner in state["owners"] and not window.events.closed.is_set()
                    error = wait_for(lambda: getattr(window.state, "lanctl_close_error", None))
                    assert error["errorId"] == "controlled-rejection"
                    with provisional_operation(draft, owner, coordinator=coordinator, base={}):
                        pass
                else:
                    assert window.events.closed.is_set() and owner not in state["owners"]
                    assert bool(state.get("closed")) == (not args.peer)
                if args.decision == "save" and not args.peer:
                    from lanctl.core.projects.workspace import prepare_project_workspace

                    reopened = prepare_project_workspace(destination, root=root / "reopen")
                    assert DeviceDatabase(reopened.database).load()[0].idf == "PC-001"
            except Exception as exc:
                failures.append(repr(exc))
            finally:
                finished.set()
                if not window.events.closed.is_set():
                    window.destroy()

        webview.start(verify, gui="qt", debug=False)
        assert finished.wait(20), "Verification thread did not finish"
        assert not failures, failures
        print(json.dumps({"nativeDraftCloseChecked": True, **vars(args)}))


if __name__ == "__main__":
    main()
