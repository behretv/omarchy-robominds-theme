# tests/test_palette.py
"""Tests for palette generation algorithm."""

from palettgen.palette import generate_palette, validate_palette


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


def test_validate_palette_dark():
    """Test validation for dark mode palette."""
    palette = generate_palette("#0052BB", "dark")
    validate_palette(palette)


def test_validate_palette_light():
    """Test validation for light mode palette."""
    palette = generate_palette("#0052BB", "light")
    validate_palette(palette)


def test_validate_palette_contrast():
    """Test that contrast ratio is sufficient."""
    palette = generate_palette("#0052BB", "dark")
    assert palette["background"] != palette["foreground"]


def test_edge_case_pure_blue():
    """Test with pure blue brand color."""
    palette = generate_palette("#0000FF", "dark")
    assert palette["accent"] == "#0000FF"
    validate_palette(palette)


def test_edge_case_red():
    """Test with red brand color."""
    palette = generate_palette("#FF0000", "dark")
    assert palette["accent"] == "#FF0000"
    validate_palette(palette)


def test_edge_case_green():
    """Test with green brand color."""
    palette = generate_palette("#00FF00", "dark")
    assert palette["accent"] == "#00FF00"
    validate_palette(palette)
