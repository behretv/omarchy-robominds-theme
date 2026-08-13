import subprocess
import sys
from pathlib import Path
import tempfile


def test_cli_help():
    """Test that --help works."""
    result = subprocess.run(
        [sys.executable, "-m", "palettgen.cli", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "--brand" in result.stdout
    assert "--mode" in result.stdout
    assert "--output" in result.stdout


def test_cli_generates_dark_mode(tmp_path):
    """Test generating dark mode palette."""
    output = tmp_path / "test-dark.toml"
    result = subprocess.run(
        [sys.executable, "-m", "palettgen.cli",
         "--brand", "#0052BB",
         "--output", str(output)],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert output.exists()
    content = output.read_text()
    assert 'accent = "#0052BB"' in content
    assert "color0" in content
    assert "color15" in content


def test_cli_generates_light_mode(tmp_path):
    """Test generating light mode palette."""
    output = tmp_path / "test-light.toml"
    result = subprocess.run(
        [sys.executable, "-m", "palettgen.cli",
         "--brand", "#0052BB",
         "--mode", "light",
         "--output", str(output)],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert output.exists()
    content = output.read_text()
    assert "Mode: light" in content


def test_cli_invalid_brand():
    """Test that invalid brand color is handled."""
    result = subprocess.run(
        [sys.executable, "-m", "palettgen.cli",
         "--brand", "not-a-color",
         "--output", "/tmp/test-invalid.toml"],
        capture_output=True,
        text=True
    )
    # Should fail with ValueError or similar
    assert result.returncode != 0


def test_cli_default_output():
    """Test default output file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        import os
        os.chdir(tmpdir)
        result = subprocess.run(
            [sys.executable, "-m", "palettgen.cli",
             "--brand", "#0052BB"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert Path("colors.toml").exists()
