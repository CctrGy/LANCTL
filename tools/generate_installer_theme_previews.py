"""Render the real suite UI with Core palettes and synthetic, non-user data.

Run explicitly with the GUI development dependencies and Edge installed.
Committed BMPs allow Inno builds without a browser dependency.
"""

import base64
import struct
from pathlib import Path
from unittest.mock import patch

from playwright.sync_api import sync_playwright

from lanctl import __version__
from lanctl.core.gui_preferences import _payload

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "packaging/inno/theme-previews"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with patch("lanctl.core.gui_preferences.active_theme_extensions", return_value=[]):
        themes = _payload(
            {"theme": "graphite", "density": "comfortable", "fontScale": 1, "reducedMotion": True}
        )["themes"]
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            for theme in themes:
                payload = _payload(
                    {
                        "theme": theme["id"],
                        "density": "comfortable",
                        "fontScale": 1,
                        "reducedMotion": True,
                    }
                )
                page = browser.new_page(viewport={"width": 1040, "height": 650})
                page.goto((ROOT / "gui/suite.html").as_uri())
                page.evaluate(
                    """({palette, version}) => {
                      window.pywebview = {api: {
                        bootstrap: async () => ({ok:true, version, projects:[], plugins:[],
                          activeProject:'', sessions:[], system:'Windows', architecture:'x64'}),
                        gui_preferences: async () => ({ok:true, ...palette}),
                        runtime_status: async () => ({ok:true, sessions:[], plugins:[]}),
                        check_updates: async () => ({ok:true, status:'idle'}),
                        update_status: async () => ({ok:true, status:'idle'}),
                        record_activity: async () => ({ok:true})
                      }};
                      window.dispatchEvent(new Event('pywebviewready'));
                    }""",
                    {"palette": payload, "version": __version__},
                )
                page.wait_for_function("document.querySelectorAll('.launch-card').length === 5")
                page.wait_for_function(
                    "accent => document.documentElement.style.getPropertyValue('--lime') === accent",
                    arg=theme["tokens"]["--color-accent"],
                )
                page.evaluate("document.fonts.ready")
                pixels = page.evaluate(
                    """async encoded => {
                      const image = new Image();
                      image.src = 'data:image/png;base64,' + encoded;
                      await image.decode();
                      const canvas = document.createElement('canvas');
                      canvas.width = 832; canvas.height = 520;
                      const ctx = canvas.getContext('2d');
                      ctx.drawImage(image, 0, 0, 832, 520);
                      const rgba = ctx.getImageData(0, 0, 832, 520).data;
                      const bytes = new Uint8Array(832 * 520 * 3);
                      let offset = 0;
                      for (let y = 519; y >= 0; y--) for (let x = 0; x < 832; x++) {
                        const i = (y * 832 + x) * 4;
                        bytes[offset++] = rgba[i+2];
                        bytes[offset++] = rgba[i+1];
                        bytes[offset++] = rgba[i];
                      }
                      let text = '';
                      for (let i = 0; i < bytes.length; i += 8192)
                        text += String.fromCharCode(...bytes.subarray(i, i + 8192));
                      return btoa(text);
                    }""",
                    base64.b64encode(page.screenshot()).decode("ascii"),
                )
                data = base64.b64decode(pixels)
                header = struct.pack("<2sIHHI", b"BM", 54 + len(data), 0, 0, 54)
                header += struct.pack("<IiiHHIIiiII", 40, 832, 520, 1, 24, 0, len(data), 0, 0, 0, 0)
                (OUTPUT / (theme["id"] + ".bmp")).write_bytes(header + data)
                print(f"Rendered {theme['id']}: {theme['name']}")
                page.close()
            browser.close()


if __name__ == "__main__":
    main()
