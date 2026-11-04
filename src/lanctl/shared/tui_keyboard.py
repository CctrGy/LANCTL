"""Pure key binding preferences; terminal input decoding stays in its adapter."""

from __future__ import annotations

DEFAULT_TUI_KEY_BINDINGS = {
    "help": "F1",
    "info": "F2",
    "ping": "F3",
    "refresh": "F5",
    "plugins": "F7",
    "projects": "F9",
    "settings": "F12",
    "history": "CTRL_H",
    "search": "CTRL_F",
    "reload": "CTRL_R",
    "edit": "CTRL_E",
    "groups": "CTRL_G",
    "ports": "CTRL_P",
    "open": "CTRL_O",
    "save": "CTRL_S",
    "differences": "CTRL_D",
    "copyLine": "CTRL_X",
    "copyJson": "CTRL_J",
    "console": "CTRL_L",
    "quit": "CTRL_Q",
    "deviceHistory": None,
    "scanSelected": None,
    "filterActive": None,
    "filterDisconnected": None,
    "filterAll": None,
    "ssh": None,
    "terminal": None,
    "credentials": None,
    "wakeOnLan": None,
    "copyIp": None,
    "copyMac": None,
    "projectStatus": None,
}

CONFIGURABLE_TUI_KEYS = (
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
    "CTRL_H",
    "CTRL_J",
    "CTRL_D",
    "CTRL_E",
    "CTRL_F",
    "CTRL_G",
    "CTRL_L",
    "CTRL_O",
    "CTRL_P",
    "CTRL_Q",
    "CTRL_R",
    "CTRL_S",
    "CTRL_X",
)

DEFAULT_VISIBLE_FOOTER_ACTIONS = (
    "help",
    "info",
    "ping",
    "refresh",
    "plugins",
    "projects",
    "settings",
    "select",
)

FOOTER_ACTIONS = (
    *DEFAULT_TUI_KEY_BINDINGS,
    "select",
    "execute",
    "exit",
)


def normalize_key_bindings(value: object) -> dict[str, str | None]:
    configured = value if isinstance(value, dict) else {}
    result = dict(DEFAULT_TUI_KEY_BINDINGS)
    for action in result:
        raw = configured.get(action, result[action])
        if raw is None or str(raw).strip().casefold() in {"none", "null", "off", "-"}:
            result[action] = None
            continue
        key = str(raw).strip().upper().replace("+", "_")
        if key in CONFIGURABLE_TUI_KEYS:
            result[action] = key
    return result


def validate_key_bindings(value: dict[str, str | None]) -> dict[str, str | None]:
    result = normalize_key_bindings(value)
    assigned = [key for key in result.values() if key]
    duplicates = {key for key in assigned if assigned.count(key) > 1}
    if duplicates:
        shown = ", ".join(sorted(key.replace("_", "+") for key in duplicates))
        raise ValueError(f"cada acción TUI debe usar una tecla distinta; duplicadas: {shown}")
    return result


def normalize_footer_actions(value: object) -> list[str]:
    if isinstance(value, str):
        values = [part.strip() for part in value.split(",")]
    elif isinstance(value, (list, tuple)):
        values = [str(part).strip() for part in value]
    else:
        values = list(DEFAULT_VISIBLE_FOOTER_ACTIONS)
    if any(item.casefold() == "all" for item in values):
        return list(FOOTER_ACTIONS)
    aliases = {item.casefold(): item for item in FOOTER_ACTIONS}
    result = []
    for item in values:
        action = aliases.get(item.casefold())
        if action and action not in result:
            result.append(action)
    return result
