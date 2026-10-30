"""Open a standalone GUI design sample; no LANCTL settings or data are loaded."""

from pathlib import Path

import webview


class PreviewApi:
    def __init__(self):
        self._window = None

    def close_preview(self):
        if self._window is not None:
            self._window.destroy()


def main():
    api = PreviewApi()
    page = Path(__file__).resolve().parents[1] / "gui/prototypes/settings-preview.html"
    api._window = webview.create_window(
        "LANCTL · SETTINGS · Ejemplo de diseño",
        page.as_uri(),
        js_api=api,
        width=1000,
        height=800,
        min_size=(560, 500),
        text_select=True,
    )
    webview.start(gui="qt")


if __name__ == "__main__":
    main()
