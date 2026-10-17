"""Stable release discovery only. Call from a background worker, never the GUI thread."""

from __future__ import annotations

import json
import math
import re
import time
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

from lanctl import __version__
from lanctl.core.file_transaction import atomic_write_json, locked_file
from lanctl.core.official_links import get_official_links
from lanctl.core.paths import data_root

DAY = 86400
_VERSION = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def version_key(value):
    if not isinstance(value, str) or not (match := _VERSION.fullmatch(value.removeprefix("v"))):
        raise ValueError("versión semántica no válida")
    prerelease = match[4]
    parts = []
    for part in prerelease.split(".") if prerelease else []:
        if part.isdecimal() and len(part) > 1 and part[0] == "0":
            raise ValueError("identificador numérico de versión no válido")
        parts.append((0, int(part)) if part.isdecimal() else (1, part))
    return (tuple(int(match[i]) for i in (1, 2, 3)), 0 if prerelease else 1, tuple(parts))


def _fetch_releases():
    releases = []
    for page in range(1, 6):
        request = Request(
            f"https://api.github.com/repos/CctrGy/LANCTL/releases?per_page=100&page={page}",
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "LANCTL-update-check",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        # Only the fixed public GitHub HTTPS endpoint is requested.
        with urlopen(request, timeout=3) as response:  # nosec B310
            body = response.read(2 * 1024 * 1024 + 1)
        if len(body) > 2 * 1024 * 1024:
            raise ValueError("respuesta de versiones demasiado grande")
        rows = json.loads(body)
        if not isinstance(rows, list):
            raise ValueError("respuesta de versiones no válida")
        releases.extend(rows)
        if len(rows) < 100:
            return releases
    raise ValueError("catálogo de versiones excede el límite de consulta")


class UpdateService:
    def __init__(self, path=None, *, fetcher=None, clock=None):
        self.path = Path(path) if path is not None else data_root() / "config" / "update-check.json"
        self.fetcher = fetcher or _fetch_releases
        self.clock = clock or time.time

    def _read(self):
        if not self.path.exists():
            return {
                "schemaVersion": 1,
                "checkedAt": None,
                "result": None,
                "deferredVersion": None,
                "deferredUntil": 0,
            }
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if (
            not isinstance(data, dict)
            or type(data.get("schemaVersion")) is not int
            or data["schemaVersion"] != 1
        ):
            raise ValueError("caché de actualizaciones no compatible")
        for key in ("checkedAt", "deferredUntil"):
            value = data.get(key)
            if value is not None and (type(value) not in (int, float) or not math.isfinite(value)):
                raise ValueError("fecha de caché de actualizaciones no válida")
        if data.get("result") is not None and not isinstance(data["result"], dict):
            raise ValueError("resultado de caché de actualizaciones no válido")
        previous = data.get("result")
        if previous:
            if previous.get("schemaVersion") != 1 or previous.get("status") not in {
                "current",
                "available",
                "unavailable",
            }:
                raise ValueError("estado de caché de actualizaciones no válido")
            version_key(previous.get("installed"))
            available = previous.get("available")
            if available is not None:
                version_key(available)
                allowed = {
                    get_official_links()["github"]
                    + "/releases/tag/"
                    + quote(prefix + available, safe="")
                    for prefix in ("", "v")
                }
                if previous.get("url") not in allowed or version_key(available) <= version_key(
                    previous["installed"]
                ):
                    raise ValueError("enlace o versión de caché de actualizaciones no válido")
            elif previous.get("url") is not None or previous.get("status") == "available":
                raise ValueError("caché de actualizaciones inconsistente")
            if not isinstance(previous.get("notes"), str) or len(previous["notes"]) > 8000:
                raise ValueError("notas de caché de actualizaciones no válidas")
        return data

    @staticmethod
    def _empty(now):
        return {
            "schemaVersion": 1,
            "installed": __version__,
            "available": None,
            "url": None,
            "notes": "",
            "checkedAt": now,
            "status": "unavailable",
            "cached": False,
            "deferred": False,
        }

    def check(self, *, manual=False) -> dict:
        now = self.clock()
        result = self._empty(now)
        try:
            if type(manual) is not bool:
                raise ValueError("manual debe ser booleano")
            # A reservation persists before network I/O, limiting retries even on
            # failure, process exit, or a simultaneous second launcher.
            with locked_file(self.path):
                data = self._read()
                checked = data.get("checkedAt")
                if not manual and checked is not None and 0 <= now - checked < DAY:
                    previous = data.get("result") or self._empty(checked)
                    if previous.get("installed") == __version__:
                        return {
                            **previous,
                            "cached": True,
                            "deferred": previous.get("available") == data.get("deferredVersion")
                            and now < data.get("deferredUntil", 0),
                        }
                    return {**result, "checkedAt": checked, "cached": True}
                data.update(checkedAt=now, result=result)
                atomic_write_json(self.path, data)
            rows = self.fetcher()
            if not isinstance(rows, list) or len(rows) > 500:
                raise ValueError("catálogo de versiones no válido")
            candidates = []
            for release in rows:
                if (
                    not isinstance(release, dict)
                    or release.get("draft") is not False
                    or release.get("prerelease") is not False
                    or not release.get("published_at")
                ):
                    continue
                try:
                    key = version_key(release.get("tag_name"))
                except ValueError:
                    continue
                if key > version_key(__version__):
                    candidates.append((key, release))
            result["status"] = "current"
            if candidates:
                release = max(candidates, key=lambda pair: pair[0])[1]
                tag = release["tag_name"]
                result.update(
                    status="available",
                    available=tag.removeprefix("v"),
                    url=get_official_links()["github"] + "/releases/tag/" + quote(tag, safe=""),
                    notes=str(release.get("body") or "")[:8000],
                )
            with locked_file(self.path):
                latest = self._read()
                result["deferred"] = result["available"] == latest.get(
                    "deferredVersion"
                ) and now < latest.get("deferredUntil", 0)
                # A newer manual request owns the cache; never replace it with an older result.
                if latest.get("checkedAt") == now:
                    latest["result"] = result
                    atomic_write_json(self.path, latest)
        except (OSError, ValueError, TypeError) as exc:
            from lanctl.core.errors import errors

            errors.from_exception(
                exc,
                origin="LANCTL.Core.Updates.Check",
                code="UPDATES.CHECK.UNAVAILABLE",
                level=24,
                print_output=False,
            )
            result = self._empty(now)
        return result

    def remind_later(self, version: str) -> None:
        version_key(version)
        with locked_file(self.path):
            data = self._read()
            data.update(deferredVersion=version.removeprefix("v"), deferredUntil=self.clock() + DAY)
            atomic_write_json(self.path, data)
