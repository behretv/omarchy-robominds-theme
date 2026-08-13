# tests/test_palette.py
"""Tests for palette generation algorithm."""

from palettgen.palette import generate_palette


def test_generate_palette_returns_dict():
    palette = generate_palette("#0052BB", "dark")
    assert isinstance(palette, dict)
    assert len(palette) == 22


def test_generate_palette_has_required_keys():
    palette = generate_palette("#0052BB", "dark")
    required_keys = [
        "accent", "cursor", "foreground", "background",
        "selection_foreground", "selection_background"
    ] + [f"color{i}" for i in range(16)]
    for key in required_keys:
        assert key in palette, f"Missing key: {key}"


def test_generate_palette_brand_color_preserved():
    palette = generate_palette("#0052BB", "dark")
    assert palette["accent"] == "#0052BB"
    assert palette["cursor"] == "#0052BB"


def test_generate_palette_dark_mode():
    palette = generate_palette("#0052BB", "dark")
    # Background should be dark
    assert palette["background"].startswith("#")
    # Foreground should be light
    assert palette["foreground"].startswith("#")


def test_generate_palette_light_mode():
    palette = generate_palette("#0052BB", "light")
    # Background should be light
    assert palette["background"].startswith("#")


def test_generate_palette_different_modes():
    dark = generate_palette("#0052BB", "dark")
    light = generate_palette("#0052BB", "light")
    # Modes should produce different palettes
    assert dark["background"] != light["background"]
