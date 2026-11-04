"""Internal shortcut plans; presentation adapters must translate validation codes.

Only explicit interface switches are accepted: credentials and arbitrary commands
cannot accidentally become persistent shortcut arguments. No settings are read
or changed by this service.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

LAUNCHERS = frozenset({"lanctl", "lanip", "lanwire", "lanrack", "lanaccess", "lanmon"})
MODES = frozenset({"cli", "tui", "gui"})


def _single_line(value: str) -> bool:
    return bool(value.strip()) and not any(ord(char) < 32 or ord(char) == 127 for char in value)


def _value(value: str) -> str:
    return value.replace("\\", "\\\\").replace(" ", "\\s")


def _exec_token(value: str) -> str:
    # Exec quoting is applied before the Desktop Entry string escaping layer.
    escaped = "".join("\\" + char if char in '\\"`$' else char for char in value)
    return _value('"' + escaped.replace("%", "%%") + '"')


@dataclass(frozen=True)
class LinuxShortcutPlan:
    executable: Path
    arguments: tuple[str, ...]
    working_directory: Path
    target: Path
    icon: Path | None
    name: str
    terminal: bool

    def content(self) -> str:
        fields = [
            "[Desktop Entry]",
            "Type=Application",
            f"Name={_value(self.name)}",
            "Exec="
            + " ".join(_exec_token(part) for part in (str(self.executable), *self.arguments)),
            f"Path={_value(str(self.working_directory))}",
            f"Terminal={str(self.terminal).lower()}",
            "Categories=Network;Utility;",
            "X-LANCTL-Shortcut-Version=1",
        ]
        if self.icon is not None:
            fields.append(f"Icon={_value(str(self.icon))}")
        return "\n".join(fields) + "\n"


def plan_linux_shortcut(
    distribution: Path,
    launcher: str,
    mode: str,
    name: str,
    *,
    destination: Path | None = None,
    working_directory: Path | None = None,
    icon: Path | None = None,
    gui_available: bool = True,
) -> LinuxShortcutPlan:
    """Plan an explicit mode shortcut from a caller-resolved distribution folder.

    Never infer an installation path from cwd or a PyInstaller extraction folder.
    The caller supplies component availability from its installation inventory.
    """
    if launcher not in LAUNCHERS or mode not in MODES:
        raise ValueError("SHORTCUT.INVALID_LAUNCH_MODE")
    if mode == "gui" and not gui_available:
        raise ValueError("SHORTCUT.GUI_UNAVAILABLE")
    if (
        not _single_line(name)
        or name != name.strip()
        or any(char in name for char in "/\\")
        or name in {".", ".."}
    ):
        raise ValueError("SHORTCUT.INVALID_NAME")
    distribution = distribution.resolve(strict=True)
    executable = distribution / launcher
    if not executable.is_file() or not os.access(executable, os.X_OK):
        raise ValueError("SHORTCUT.EXECUTABLE_UNAVAILABLE")
    directory = (destination if destination is not None else distribution).resolve(strict=True)
    working = (working_directory if working_directory is not None else distribution).resolve(
        strict=True
    )
    if not directory.is_dir() or not working.is_dir():
        raise ValueError("SHORTCUT.INVALID_DIRECTORY")
    icon = icon.resolve(strict=True) if icon is not None else None
    if icon is not None and not icon.is_file():
        raise ValueError("SHORTCUT.INVALID_ICON")
    # Gio checks executable existence before decoding %% in its command line.
    # Reject this path rather than creating a valid-looking but unusable shortcut.
    values = [str(executable), str(working), str(directory)] + ([str(icon)] if icon else [])
    if any(not _single_line(value) for value in values) or any(
        char in str(executable) for char in "=%"
    ):
        raise ValueError("SHORTCUT.INVALID_PATH")
    return LinuxShortcutPlan(
        executable,
        (f"--{mode}",),
        working,
        directory / f"{name}.desktop",
        icon,
        name,
        mode != "gui",
    )


def create_linux_shortcut(plan: LinuxShortcutPlan) -> Path:
    """Publish a complete file without replacing existing files or symlinks.

    A same-directory hard link provides atomic, no-clobber publication. A caller
    handles permission/unsupported-filesystem errors at its presentation boundary.
    Replacement and repair are deliberately not supported by this first adapter.
    """
    if os.name != "posix":
        raise OSError("SHORTCUT.UNSUPPORTED_PLATFORM")
    descriptor, temporary = tempfile.mkstemp(prefix=".lanctl-shortcut-", dir=plan.target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(plan.content())
            stream.flush()
            os.fchmod(stream.fileno(), 0o755)
            os.fsync(stream.fileno())
        os.link(temporary, plan.target)
    finally:
        os.unlink(temporary)
    return plan.target


def plan_shortcut(*args, **kwargs):
    """Select the native adapter without changing preferences or project state."""
    import sys

    if sys.platform == "win32":
        from lanctl.core.shortcuts_windows import plan_windows_shortcut

        return plan_windows_shortcut(*args, **kwargs)
    if sys.platform.startswith("linux"):
        return plan_linux_shortcut(*args, **kwargs)
    raise ValueError("SHORTCUT.UNSUPPORTED_PLATFORM")


def create_shortcut(plan):
    if isinstance(plan, LinuxShortcutPlan):
        return create_linux_shortcut(plan)
    from lanctl.core.shortcuts_windows import WindowsShortcutPlan, create_windows_shortcut

    if isinstance(plan, WindowsShortcutPlan):
        return create_windows_shortcut(plan)
    raise ValueError("SHORTCUT.INVALID_PLAN")
