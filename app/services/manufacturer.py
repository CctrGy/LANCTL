from __future__ import annotations

from functools import lru_cache


def _is_private_mac(mac: str) -> bool:
    try:
        first_octet = int(mac.split(":", 1)[0], 16)
    except (ValueError, IndexError):
        return False
    return bool(first_octet & 0x02)


@lru_cache(maxsize=1)
def _parser():
    try:
        from manuf import manuf
    except ImportError:
        return None
    return manuf.MacParser()


def detect_manufacturer(mac: str) -> str:
    """Obtiene el fabricante mediante plugins activos y la base local integrada."""
    normalized = mac.strip().replace("-", ":").upper()
    if not normalized or normalized == "FF:FF:FF:FF:FF:FF":
        return ""
    from app.plugins.device_adapters import resolve_manufacturer_extensions
    provided = resolve_manufacturer_extensions(normalized)
    if provided:
        return provided
    if _is_private_mac(normalized):
        return "MAC privada/aleatoria"
    parser = _parser()
    if parser is None:
        return ""
    return parser.get_manuf_long(normalized) or parser.get_manuf(normalized) or ""
