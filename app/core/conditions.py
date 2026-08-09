from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

_DURATION = re.compile(r"^(\d+)(s|m|h|d)$", re.IGNORECASE)


def duration(value: str) -> float:
    match = _DURATION.fullmatch(value.strip())
    if not match:
        raise ValueError(f"duración no válida: {value}")
    amount = int(match.group(1))
    unit = match.group(2).casefold()
    return amount * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit]


@dataclass(frozen=True)
class Condition:
    text: str
    kind: str
    values: tuple[str, ...]


def parse_condition(text: str) -> Condition:
    clean = " ".join(str(text).strip().split())
    patterns = (
        (r"^(online|offline)$", "state"),
        (r"^offline-for (\d+[smhd])$", "offline-for"),
        (r"^last-seen > (\d+[smhd])$", "last-seen"),
        (r"^(ping|arp) responds$", "probe"),
        (r"^port (\d{1,5}) open$", "port"),
        (r"^time (after|before) (\d{2}:\d{2})$", "time"),
        (r"^time between (\d{2}:\d{2}) (\d{2}:\d{2})$", "between"),
        (r"^weekday ([a-záéíóú-]+)$", "weekday"),
        (r"^device (.+) (online|offline)$", "device"),
        (r"^group (.+) (all-online|any-offline)$", "group"),
        (r"^task ([a-z][a-z0-9._-]*) (success|completed|failed)$", "task"),
        (r"^smb\.(available|unavailable|authentication\.required) (.+)$", "smb-state"),
        (r"^smb\.(share\.exists|share\.unavailable|printer\.exists) (\S+) (.+)$", "smb-resource"),
    )
    for pattern, kind in patterns:
        match = re.fullmatch(pattern, clean, re.IGNORECASE)
        if match:
            if kind == "port" and not 1 <= int(match.group(1)) <= 65535:
                break
            return Condition(clean, kind, tuple(match.groups()))
    raise ValueError(f"condición no soportada: {text}")


class ConditionContext:
    def __init__(
        self,
        *,
        online: Callable[[str], bool],
        target: str,
        last_seen: str = "",
        group_members: Callable[[str], list[str]] | None = None,
        port_open: Callable[[str, int], bool] | None = None,
        task_state: Callable[[str], str | None] | None = None,
        smb_observation: Callable[[str], dict | None] | None = None,
        now: datetime | None = None,
    ):
        self.online, self.target, self.last_seen = online, target, last_seen
        self.group_members = group_members or (lambda _name: [])
        self.port_open = port_open or (lambda _target, _port: False)
        self.task_state = task_state or (lambda _task: None)
        self.smb_observation = smb_observation or (lambda _target: None)
        self.now = now or datetime.now().astimezone()


def evaluate(condition: Condition, context: ConditionContext) -> bool:
    kind, values = condition.kind, condition.values
    if kind == "state":
        return context.online(context.target) == (values[0].casefold() == "online")
    if kind == "probe":
        return context.online(context.target)
    if kind == "port":
        return context.port_open(context.target, int(values[0]))
    if kind == "offline-for":
        if context.online(context.target):
            return False
        return _age(context) >= duration(values[0])
    if kind == "last-seen":
        return _age(context) > duration(values[0])
    if kind == "device":
        return context.online(values[0]) == (values[1].casefold() == "online")
    if kind == "group":
        states = [context.online(item) for item in context.group_members(values[0])]
        return bool(states) and (
            all(states) if values[1].casefold() == "all-online" else any(not x for x in states)
        )
    if kind == "task":
        actual = context.task_state(values[0])
        expected = values[1].casefold()
        return actual == expected or (
            expected == "completed" and actual in {"success", "failed", "error", "timeout"}
        )
    if kind in {"smb-state", "smb-resource"}:
        target = values[1]
        observed = context.smb_observation(target)
        if not observed or not observed.get("observedAt"):
            return False
        if kind == "smb-state":
            state = observed.get("state")
            return (
                state
                == (
                    "authentication-required"
                    if values[0].casefold() == "authentication.required"
                    else "available"
                )
                if values[0].casefold() != "unavailable"
                else state != "available"
            )
        shares = observed.get("smb", {}).get("shares", [])
        resource = values[2].casefold()
        action = values[0].casefold()
        matches = [item for item in shares if str(item.get("name", "")).casefold() == resource]
        if action == "printer.exists":
            return any(item.get("type") == "printer" for item in matches)
        if action == "share.exists":
            return bool(matches)
        return not matches or all(item.get("access") == "denied" for item in matches)
    if kind in {"time", "between"}:
        current = context.now.strftime("%H:%M")
        return (
            current > values[1]
            if values[0].casefold() == "after"
            else current < values[1]
            if kind == "time"
            else values[0] <= current <= values[1]
        )
    if kind == "weekday":
        names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        aliases = {
            "lunes": "monday",
            "martes": "tuesday",
            "miércoles": "wednesday",
            "miercoles": "wednesday",
            "jueves": "thursday",
            "viernes": "friday",
            "sábado": "saturday",
            "sabado": "saturday",
            "domingo": "sunday",
        }
        spec = aliases.get(values[0].casefold(), values[0].casefold())
        current = names[context.now.weekday()]
        if spec == "monday-friday":
            return context.now.weekday() < 5
        return current == spec
    return False


def _age(context: ConditionContext) -> float:
    if not context.last_seen:
        return float("inf")
    seen = datetime.fromisoformat(context.last_seen)
    if seen.tzinfo is None:
        seen = seen.replace(tzinfo=context.now.tzinfo)
    return max(0.0, (context.now - seen).total_seconds())
