"""Explicit preview/create adapter for native desktop shortcuts."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from lanctl.core.shortcuts import LAUNCHERS, MODES, create_shortcut, plan_shortcut
from lanctl.shared.i18n import t


def register_shortcut_command(subparsers):
    parser = subparsers.add_parser("shortcut", help=t("LANCTL.SHORTCUT.HELP"))
    parser.add_argument(
        "--launcher",
        choices=sorted(LAUNCHERS),
        default="lanctl",
        help=t("LANCTL.SHORTCUT.LAUNCHER"),
    )
    parser.add_argument(
        "--mode", choices=sorted(MODES), required=True, help=t("LANCTL.SHORTCUT.MODE")
    )
    parser.add_argument("--name", required=True, help=t("LANCTL.SHORTCUT.NAME"))
    for flag, key in (
        ("distribution", "DISTRIBUTION"),
        ("destination", "DESTINATION"),
        ("working-directory", "WORKING"),
        ("icon", "ICON"),
    ):
        parser.add_argument(f"--{flag}", type=Path, help=t(f"LANCTL.SHORTCUT.{key}"))
    parser.add_argument("--create", action="store_true", help=t("LANCTL.SHORTCUT.CREATE"))
    return parser


def run_shortcut(args):
    try:
        if not (sys.platform.startswith("linux") or sys.platform == "win32"):
            raise ValueError("SHORTCUT.UNSUPPORTED_PLATFORM")
        distribution = args.distribution
        if distribution is None:
            if not getattr(sys, "frozen", False):
                raise ValueError("SHORTCUT.DISTRIBUTION_REQUIRED")
            from lanctl.core.paths import application_directory

            distribution = application_directory()
        plan = plan_shortcut(
            distribution,
            args.launcher,
            args.mode,
            args.name,
            destination=args.destination,
            working_directory=args.working_directory,
            icon=args.icon,
            gui_available=importlib.util.find_spec("webview") is not None,
        )
        # The same JSON is emitted before either preview or publication; no prompt
        # can block scripts or SSH. --create is explicit consent to create only.
        print(
            json.dumps(
                {
                    "executable": str(plan.executable),
                    "arguments": plan.arguments,
                    "workingDirectory": str(plan.working_directory),
                    "target": str(plan.target),
                    "icon": str(plan.icon) if plan.icon else None,
                    "terminal": plan.terminal,
                },
                ensure_ascii=False,
            )
        )
        if args.create:
            create_shortcut(plan)
            print(t("LANCTL.SHORTCUT.CREATED", path=str(plan.target)))
        else:
            print(t("LANCTL.SHORTCUT.PREVIEW"))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        from lanctl.core.errors import errors

        errors.from_exception(
            exc, origin="LANCTL.Suite.Shortcut.Create", code="SHORTCUT.CREATE.FAILED", level=43
        )
        print(t("LANCTL.SHORTCUT.FAILED"), file=sys.stderr)
        return 2
