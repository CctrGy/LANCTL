"""Local GUI adapter: preview is required before creating a desktop shortcut."""

from __future__ import annotations

import importlib.util
import secrets
import sys
from pathlib import Path

from lanctl.core.shortcuts import LAUNCHERS, MODES, create_shortcut, plan_shortcut
from lanctl.shared.i18n import t


class ShortcutGuiMixin:
    def _shortcut_respond(self, action, operation):
        result = self._respond(action, operation)
        if not result.get("ok"):
            # The canonical event and original exception stay in errorDetails.
            result["error"] = t("LANCTL.SHORTCUT.FAILED")
        return result

    def shortcut_options(self):
        def operation():
            from lanctl.core.paths import application_directory

            return {
                "supported": sys.platform.startswith("linux") or sys.platform == "win32",
                "distribution": str(application_directory())
                if getattr(sys, "frozen", False)
                else "",
                "launchers": sorted(LAUNCHERS),
                "modes": sorted(MODES),
                "guiAvailable": importlib.util.find_spec("webview") is not None,
            }

        return self._shortcut_respond("ShortcutOptions", operation)

    def select_shortcut_path(self, kind):
        def operation():
            import webview

            if kind not in {"distribution", "destination", "working_directory", "icon"}:
                raise ValueError("SHORTCUT.INVALID_PATH_KIND")
            window = self._desktop._window
            if window is None:
                raise RuntimeError("SHORTCUT.WINDOW_UNAVAILABLE")
            selected = window.create_file_dialog(
                webview.OPEN_DIALOG if kind == "icon" else webview.FOLDER_DIALOG,
                allow_multiple=False,
            )
            return {"path": str(selected[0]) if selected else "", "cancelled": not bool(selected)}

        return self._shortcut_respond("ShortcutSelectPath", operation)

    def preview_shortcut(self, values):
        def operation():
            self._shortcut_preview = None
            if not (sys.platform.startswith("linux") or sys.platform == "win32"):
                raise ValueError("SHORTCUT.UNSUPPORTED_PLATFORM")
            if not isinstance(values, dict) or any(
                not isinstance(value, str) for value in values.values()
            ):
                raise ValueError("SHORTCUT.INVALID_FORM")
            distribution = values.get("distribution", "")
            if not distribution:
                from lanctl.core.paths import application_directory

                if not getattr(sys, "frozen", False):
                    raise ValueError("SHORTCUT.DISTRIBUTION_REQUIRED")
                distribution = str(application_directory())
            optional = {
                key: Path(values[key]) if values.get(key) else None
                for key in ("destination", "working_directory", "icon")
            }
            plan = plan_shortcut(
                Path(distribution),
                values.get("launcher", ""),
                values.get("mode", ""),
                values.get("name", ""),
                gui_available=importlib.util.find_spec("webview") is not None,
                **optional,
            )
            token = secrets.token_urlsafe(24)
            self._shortcut_preview = (token, plan)
            return {
                "token": token,
                "executable": str(plan.executable),
                "arguments": list(plan.arguments),
                "workingDirectory": str(plan.working_directory),
                "target": str(plan.target),
                "icon": str(plan.icon) if plan.icon else "",
                "terminal": plan.terminal,
            }

        return self._shortcut_respond("ShortcutPreview", operation)

    def create_shortcut(self, token):
        def operation():
            preview = getattr(self, "_shortcut_preview", None)
            if (
                not isinstance(token, str)
                or preview is None
                or not secrets.compare_digest(token, preview[0])
            ):
                raise ValueError("SHORTCUT.PREVIEW_REQUIRED")
            # Consume before writing: retries always need a new explicit preview.
            self._shortcut_preview = None
            path = create_shortcut(preview[1])
            return {"path": str(path), "message": t("LANCTL.SHORTCUT.CREATED", path=str(path))}

        return self._shortcut_respond("ShortcutCreate", operation)
