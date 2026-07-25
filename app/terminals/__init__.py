"""Adaptadores de terminal interactiva registrados por protocolo."""

from app.terminals.registry import available_terminals, open_terminal

__all__ = ["available_terminals", "open_terminal"]
