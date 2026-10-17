"""Committed Setup previews must be real, distinct images available to Inno."""

import hashlib
import struct
from pathlib import Path


def test_all_five_setup_previews_are_complete_distinct_interface_images():
    root = Path(__file__).resolve().parents[1]
    setup = (root / "packaging/inno/LANCTL.iss").read_text(encoding="utf-8")
    assert 'Source: "theme-previews\\*.bmp"; Flags: dontcopy' in setup
    assert "ThemePreview: TBitmapImage" in setup
    assert "ThemePreview.Bitmap.LoadFromFile" in setup
    assert "GetInitialTheme('') + '.bmp'" in setup
    hashes = set()
    for theme in ("graphite", "midnight", "forest", "violet", "light"):
        assert f"ExtractTemporaryFile('{theme}.bmp')" in setup
        data = (root / f"packaging/inno/theme-previews/{theme}.bmp").read_bytes()
        magic, size, _, _, offset = struct.unpack("<2sIHHI", data[:14])
        _, width, height, planes, bits, compression = struct.unpack("<IiiHHI", data[14:34])
        assert magic == b"BM" and size == len(data)
        assert (width, height, planes, bits, compression) == (832, 520, 1, 24, 0)
        assert len(data) - offset == width * height * 3
        colors = {data[i : i + 3] for i in range(offset, len(data), 3)}
        # Text, icons and cards must be present, rather than a flat color panel.
        assert len(colors) > 1000
        assert any(min(pixel) > 180 for pixel in colors)
        assert any(max(pixel) < 70 for pixel in colors)
        hashes.add(hashlib.sha256(data).hexdigest())
    assert len(hashes) == 5
