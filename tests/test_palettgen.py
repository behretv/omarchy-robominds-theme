# tests/test_palettgen.py
"""Tests for palettgen package."""

from palettgen.palettgen import hex_to_okhsl, okhsl_to_hex


def test_hex_to_okhsl_basic():
    """Test basic conversion returns valid Okhsl values."""
    result = hex_to_okhsl("#0052BB")
    assert isinstance(result, dict)
    assert "l" in result
    assert "c" in result
    assert "h" in result
    assert 0.0 <= result["l"] <= 1.0
    assert result["c"] >= 0.0
    assert 0.0 <= result["h"] < 360.0


def test_okhsl_to_hex_roundtrip():
    """Test that converting to Okhsl and back gives the same hex."""
    original = "#0052BB"
    okhsl = hex_to_okhsl(original)
    result = okhsl_to_hex(okhsl)
    assert result.upper() == original.upper()


def test_multiple_colors_roundtrip():
    """Test roundtrip for several colors."""
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFFFF", "#000000"]
    for color in colors:
        okhsl = hex_to_okhsl(color)
        result = okhsl_to_hex(okhsl)
        assert result.upper() == color.upper(), f"Failed for {color}"
