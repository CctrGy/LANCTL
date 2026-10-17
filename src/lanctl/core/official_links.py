"""Canonical public destinations shared by application interfaces."""

from __future__ import annotations

import webbrowser

_LINKS = {
    "web": "https://cctrgy.github.io/lanctl/",
    "github": "https://github.com/CctrGy/LANCTL",
    "reference": "https://cctrgy.github.io/lanctl/reference/",
}


def get_official_links() -> dict[str, str]:
    return dict(_LINKS)


def open_official_link(key: str) -> dict:
    if not isinstance(key, str) or key not in _LINKS:
        raise ValueError("enlace oficial desconocido")
    url = _LINKS[key]
    return {"key": key, "url": url, "opened": bool(webbrowser.open(url, new=2))}
