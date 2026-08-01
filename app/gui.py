from __future__ import annotations

from app import __version__
from app.core.resources import bundled_path
from app.gui_theme import resolve_theme
from app.plugins.manager import get_plugin_manager


class GuiApi:
    def bootstrap(self) -> dict:
        manager = get_plugin_manager()
        return {"version": __version__, "theme": resolve_theme(manager.extensions.list("theme"))}


def run_gui() -> int:
    try:
        import webview
    except ImportError as error:
        raise RuntimeError("La GUI requiere pywebview. Instala las dependencias del proyecto.") from error
    index = bundled_path("GUI/index.html")
    if not index.is_file():
        raise RuntimeError(f"No se encontraron los recursos de la GUI: {index}")
    webview.create_window("LANCTL", index.as_uri(), js_api=GuiApi(), width=1480, height=900,
                          min_size=(1100, 700), background_color="#071522")
    webview.start(debug=False)
    return 0
