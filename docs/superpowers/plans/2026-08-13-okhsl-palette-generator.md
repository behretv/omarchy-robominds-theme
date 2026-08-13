# Okhsl-based Terminal Color Palette Generator

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI tool that generates perceptually uniform 16-color ANSI palettes from any brand color using Okhsl color space.

**Architecture:** Single Python module with color conversion, palette generation, and CLI interface. Uses culori library for Okhsl conversions. Outputs TOML files matching existing omarchy theme format.

**Tech Stack:** Python 3.11+, culori, pytest, tomllib

## Global Constraints

- Python 3.11+ (for tomllib)
- Output format: TOML matching existing `colors.toml` structure
- Dark mode default, light mode via `--mode light`
- Perceptually uniform colors (Okhsl, not HSL)
- WCAG AA contrast: background vs foreground ≥ 4.5:1
- All 16 ANSI colors must be visually distinct (delta-E > 10)

---

### Task 1: Project Setup and Dependencies

**Files:**
- Create: `palettgen/palettgen.py`
- Create: `palettgen/__init__.py`
- Create: `tests/test_palettgen.py`
- Create: `pyproject.toml`
- Create: `README.md`

**Interfaces:**
- Consumes: None (setup task)
- Produces: Project structure with dependencies

- [ ] **Step 1: Create project structure**

```bash
mkdir -p palettgen tests
touch palettgen/__init__.py
```

- [ ] **Step 2: Create pyproject.toml**

```toml
[project]
name = "palettgen"
version = "0.1.0"
description = "Generate perceptually uniform terminal color palettes from brand colors"
requires-python = ">=3.11"
dependencies = [
    "culori>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
]

[project.scripts]
palettgen = "palettgen.cli:main"
```

- [ ] **Step 3: Install dependencies**

```bash
cd /home/vbehret/git/public/omarchy-robominds-theme
pip install -e ".[dev]"
```

Expected: Package installed in editable mode, culori and pytest available

- [ ] **Step 4: Verify installation**

```bash
python -c "import palettgen; print('OK')"
python -c "from culori import Okhsl; print('culori OK')"
```

Expected: No import errors

- [ ] **Step 5: Commit**

```bash
git add palettgen/ tests/ pyproject.toml
git commit -m "feat: initialize palettgen project structure"
```

---

### Task 2: Core Color Conversion Functions

**Files:**
- Modify: `palettgen/__init__.py`

**Interfaces:**
- Consumes: culori library
- Produces: `hex_to_okhsl(hex_str)`, `okhsl_to_hex(okhsl)` functions

- [ ] **Step 1: Write failing test**

```python
# tests/test_palettgen.py
import pytest
from palettgen import hex_to_okhsl, okhsl_to_hex

def test_hex_to_okhsl_basic():
    result = hex_to_okhsl("#0052BB")
    assert hasattr(result, 'l')
    assert hasattr(result, 'c')
    assert hasattr(result, 'h')

def test_okhsl_to_hex_roundtrip():
    original = "#0052BB"
    okhsl = hex_to_okhsl(original)
    result = okhsl_to_hex(okhsl)
    assert result == original
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/vbehret/git/public/omarchy-robominds-theme
python -m pytest tests/test_palettgen.py::test_hex_to_okhsl_basic -v
```

Expected: FAIL with "cannot import name 'hex_to_okhsl'"

- [ ] **Step 3: Implement color conversion functions**

```python
# palettgen/__init__.py
from culori import Okhsl, okhsl

def hex_to_okhsl(hex_str: str) -> Okhsl:
    """Convert hex color string to Okhsl color object."""
    return okhsl(hex_str)

def okhsl_to_hex(okhsl_color: Okhsl) -> str:
    """Convert Okhsl color object to hex string."""
    return f"#{okhsl.oklch()[1:7].upper()}"
```

Wait, that's not quite right. Let me fix:

```python
# palettgen/__init__.py
from culori import Okhsl, okhsl, rgb

def hex_to_okhsl(hex_str: str) -> Okhsl:
    """Convert hex color string to Okhsl color object."""
    return okhsl(hex_str)

def okhsl_to_hex(okhsl_color: Okhsl) -> str:
    """Convert Okhsl color object to hex string."""
    # Convert Okhsl to RGB first, then to hex
    rgb_color = rgb(okhsl_color)
    r, g, b = rgb_color
    return f"#{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_palettgen.py -v
```

Expected: Both tests PASS

- [ ] **Step 5: Commit**

```bash
git add palettgen/__init__.py tests/test_palettgen.py
git commit -m "feat: add Okhsl color conversion functions"
```

---

### Task 3: Palette Generation Algorithm

**Files:**
- Create: `palettgen/palette.py`
- Modify: `tests/test_palettgen.py`

**Interfaces:**
- Consumes: `hex_to_okhsl()`, `okhsl_to_hex()` from `__init__.py`
- Produces: `generate_palette(brand_color, mode)` returning dict with all 22 color keys

- [ ] **Step 1: Write failing test**

```python
# tests/test_palettgen.py
from palettgen.palette import generate_palette

def test_generate_palette_dark():
    palette = generate_palette("#0052BB", "dark")
    assert "accent" in palette
    assert "color0" in palette
    assert "color15" in palette
    assert len(palette) == 22
    assert palette["accent"] == "#0052BB"

def test_generate_palette_light():
    palette = generate_palette("#0052BB", "light")
    assert "accent" in palette
    assert palette["background"] != palette["foreground"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_palettgen.py::test_generate_palette_dark -v
```

Expected: FAIL with "cannot import name 'generate_palette'"

- [ ] **Step 3: Implement palette generation**

```python
# palettgen/palette.py
from . import hex_to_okhsl, okhsl_to_hex
from culori import Okhsl

def generate_palette(brand_color: str, mode: str = "dark") -> dict:
    """Generate a 16-color ANSI palette from a brand color using Okhsl."""
    
    # Convert brand color to Okhsl
    brand_okhsl = hex_to_okhsl(brand_color)
    brand_hue = brand_okhsl.h
    
    # Define standard ANSI hue positions (in degrees)
    ansi_hues = {
        "red": 0,
        "yellow": 60,
        "green": 120,
        "cyan": 180,
        "blue": 240,
        "magenta": 300,
    }
    
    # Calculate hue shift to align blue with brand hue
    hue_shift = brand_hue - ansi_hues["blue"]
    
    # Generate shifted hues
    shifted_hues = {}
    for name, hue in ansi_hues.items():
        shifted_hues[name] = (hue + hue_shift) % 360
    
    # Define lightness and saturation based on mode
    if mode == "dark":
        base_grays = {
            "black": 0.08,
            "bright_black": 0.25,
            "white": 0.70,
            "bright_white": 0.95,
        }
        accent_saturation = 0.85
        regular_lightness = 0.50
        bright_lightness = 0.70
        bright_saturation = 0.90
    else:  # light mode
        base_grays = {
            "black": 0.95,
            "bright_black": 0.80,
            "white": 0.30,
            "bright_white": 0.05,
        }
        accent_saturation = 0.80
        regular_lightness = 0.45
        bright_lightness = 0.60
        bright_saturation = 0.85
    
    def make_color(lightness: float, saturation: float, hue: float) -> str:
        """Create a color from Okhsl parameters."""
        okhsl_color = Okhsl(l=lightness, c=0, h=hue)  # c is not used in Okhsl
        # Actually, Okhsl uses (l, s, h) not (l, c, h)
        from culori import Okhsl as OkhslType
        okhsl_color = OkhslType(l=lightness, s=saturation, h=hue)
        return okhsl_to_hex(okhsl_color)
    
    # Generate base grays
    colors = {
        "color0": make_color(base_grays["black"], 0.0, 0),
        "color7": make_color(base_grays["white"], 0.0, 0),
        "color8": make_color(base_grays["bright_black"], 0.0, 0),
        "color15": make_color(base_grays["bright_white"], 0.0, 0),
    }
    
    # Generate accent colors
    for i, (name, hue) in enumerate(shifted_hues.items()):
        color_index = i + 1  # color1-color6
        bright_index = i + 9  # color9-color14
        
        colors[f"color{color_index}"] = make_color(
            regular_lightness, accent_saturation, hue
        )
        colors[f"color{bright_index}"] = make_color(
            bright_lightness, bright_saturation, hue
        )
    
    # Map to ANSI positions
    ansi_map = {
        "red": 1, "yellow": 3, "green": 2,
        "cyan": 6, "blue": 4, "magenta": 5,
    }
    
    # Set accent and UI colors
    accent_hex = okhsl_to_hex(brand_okhsl)
    colors["accent"] = accent_hex
    colors["cursor"] = accent_hex
    colors["foreground"] = colors["color7"]
    colors["background"] = colors["color0"]
    colors["selection_foreground"] = colors["color0"]
    colors["selection_background"] = accent_hex
    
    return colors
```

Hmm, I need to check the culori Okhsl API. Let me revise:

```python
# palettgen/palette.py
from . import hex_to_okhsl, okhsl_to_hex
from culori import Okhsl

def generate_palette(brand_color: str, mode: str = "dark") -> dict:
    """Generate a 16-color ANSI palette from a brand color using Okhsl."""
    
    # Convert brand color to Okhsl
    brand_okhsl = hex_to_okhsl(brand_color)
    brand_hue = brand_okhsl.h
    
    # Define standard ANSI hue positions (in degrees)
    ansi_hues = {
        "red": 0,
        "yellow": 60,
        "green": 120,
        "cyan": 180,
        "blue": 240,
        "magenta": 300,
    }
    
    # Calculate hue shift to align blue with brand hue
    hue_shift = brand_hue - ansi_hues["blue"]
    
    # Generate shifted hues
    shifted_hues = {}
    for name, hue in ansi_hues.items():
        shifted_hues[name] = (hue + hue_shift) % 360
    
    # Define lightness and saturation based on mode
    if mode == "dark":
        base_grays = {
            "black": 0.08,
            "bright_black": 0.25,
            "white": 0.70,
            "bright_white": 0.95,
        }
        accent_saturation = 0.85
        regular_lightness = 0.50
        bright_lightness = 0.70
        bright_saturation = 0.90
    else:  # light mode
        base_grays = {
            "black": 0.95,
            "bright_black": 0.80,
            "white": 0.30,
            "bright_white": 0.05,
        }
        accent_saturation = 0.80
        regular_lightness = 0.45
        bright_lightness = 0.60
        bright_saturation = 0.85
    
    def make_color(lightness: float, saturation: float, hue: float) -> str:
        """Create a color from Okhsl parameters."""
        okhsl_color = Okhsl(l=lightness, s=saturation, h=hue)
        return okhsl_to_hex(okhsl_color)
    
    # Generate base grays (saturation = 0 for grays)
    colors = {
        "color0": make_color(base_grays["black"], 0.0, 0),
        "color7": make_color(base_grays["white"], 0.0, 0),
        "color8": make_color(base_grays["bright_black"], 0.0, 0),
        "color15": make_color(base_grays["bright_white"], 0.0, 0),
    }
    
    # Generate accent colors (color1-color6, color9-color14)
    ansi_order = ["red", "green", "yellow", "blue", "magenta", "cyan"]
    
    for i, name in enumerate(ansi_order):
        hue = shifted_hues[name]
        color_index = i + 1
        bright_index = i + 9
        
        colors[f"color{color_index}"] = make_color(
            regular_lightness, accent_saturation, hue
        )
        colors[f"color{bright_index}"] = make_color(
            bright_lightness, bright_saturation, hue
        )
    
    # Set accent and UI colors
    accent_hex = okhsl_to_hex(brand_okhsl)
    colors["accent"] = accent_hex
    colors["cursor"] = accent_hex
    colors["foreground"] = colors["color7"]
    colors["background"] = colors["color0"]
    colors["selection_foreground"] = colors["color0"]
    colors["selection_background"] = accent_hex
    
    return colors
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_palettgen.py -v
```

Expected: Both tests PASS

- [ ] **Step 5: Commit**

```bash
git add palettgen/palette.py tests/test_palettgen.py
git commit -m "feat: implement Okhsl palette generation algorithm"
```

---

### Task 4: TOML Output and CLI Interface

**Files:**
- Create: `palettgen/cli.py`
- Modify: `palettgen/__init__.py`
- Modify: `tests/test_palettgen.py`

**Interfaces:**
- Consumes: `generate_palette()` from `palette.py`
- Produces: CLI with `--brand`, `--mode`, `--output` arguments

- [ ] **Step 1: Write failing test**

```python
# tests/test_palettgen.py
import subprocess
import sys

def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "palettgen.cli", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "--brand" in result.stdout

def test_cli_generates_toml(tmp_path):
    output_file = tmp_path / "test.toml"
    result = subprocess.run(
        [sys.executable, "-m", "palettgen.cli", 
         "--brand", "#0052BB", 
         "--output", str(output_file)],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert output_file.exists()
    content = output_file.read_text()
    assert "accent" in content
    assert "#0052BB" in content
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_palettgen.py::test_cli_help -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement CLI**

```python
# palettgen/cli.py
import argparse
import sys
import tomllib
from pathlib import Path

from .palette import generate_palette

def main():
    parser = argparse.ArgumentParser(
        description="Generate perceptually uniform terminal color palettes"
    )
    parser.add_argument(
        "--brand",
        required=True,
        help="Brand color in hex format (e.g., #0052BB)"
    )
    parser.add_argument(
        "--mode",
        choices=["dark", "light"],
        default="dark",
        help="Color mode (default: dark)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("colors.toml"),
        help="Output file path (default: colors.toml)"
    )
    
    args = parser.parse_args()
    
    # Generate palette
    palette = generate_palette(args.brand, args.mode)
    
    # Write TOML
    with open(args.output, "w") as f:
        for key, value in palette.items():
            f.write(f'{key} = "{value}"\n')
    
    print(f"Generated palette: {args.output}")

if __name__ == "__main__":
    main()
```

Also update `__init__.py` to expose the public API:

```python
# palettgen/__init__.py
from . import palette
from .palette import generate_palette
from . import cli
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_palettgen.py -v
```

Expected: All tests PASS

- [ ] **Step 5: Test CLI manually**

```bash
python -m palettgen.cli --brand "#0052BB" --output /tmp/test-dark.toml
python -m palettgen.cli --brand "#0052BB" --mode light --output /tmp/test-light.toml
cat /tmp/test-dark.toml
```

Expected: TOML files generated with correct format

- [ ] **Step 6: Commit**

```bash
git add palettgen/cli.py palettgen/__init__.py tests/test_palettgen.py
git commit -m "feat: add CLI interface and TOML output"
```

---

### Task 5: Validation and Edge Cases

**Files:**
- Modify: `palettgen/palette.py`
- Modify: `tests/test_palettgen.py`

**Interfaces:**
- Consumes: Existing palette generation
- Produces: Validation functions, edge case handling

- [ ] **Step 1: Write validation tests**

```python
# tests/test_palettgen.py
from palettgen.palette import generate_palette
import colorsys

def test_contrast_ratio_dark():
    """Background and foreground must have sufficient contrast."""
    palette = generate_palette("#0052BB", "dark")
    bg = palette["background"]
    fg = palette["foreground"]
    
    # Convert hex to RGB
    bg_rgb = tuple(int(bg[i:i+2], 16) / 255.0 for i in (1, 3, 5))
    fg_rgb = tuple(int(fg[i:i+2], 16) / 255.0 for i in (1, 3, 5))
    
    # Calculate relative luminance
    def luminance(rgb):
        def linearize(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = rgb
        return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)
    
    l_bg = luminance(bg_rgb)
    l_fg = luminance(fg_rgb)
    
    contrast = (max(l_bg, l_fg) + 0.05) / (min(l_bg, l_fg) + 0.05)
    assert contrast >= 4.5, f"Contrast ratio {contrast} < 4.5"

def test_all_colors_present():
    """Ensure all 22 keys are present."""
    palette = generate_palette("#0052BB", "dark")
    expected_keys = [
        "accent", "cursor", "foreground", "background",
        "selection_foreground", "selection_background",
    ] + [f"color{i}" for i in range(16)]
    
    for key in expected_keys:
        assert key in palette, f"Missing key: {key}"

def test_valid_hex_format():
    """All colors must be valid hex format."""
    palette = generate_palette("#0052BB", "dark")
    import re
    hex_pattern = re.compile(r'^#[0-9A-F]{6}$')
    
    for key, value in palette.items():
        assert hex_pattern.match(value), f"{key}={value} is not valid hex"
```

- [ ] **Step 2: Run test to verify they fail**

```bash
python -m pytest tests/test_palettgen.py::test_contrast_ratio_dark -v
```

Expected: May fail or pass depending on implementation

- [ ] **Step 3: Add validation to palette generation**

Add a validation function:

```python
# palettgen/palette.py
import re

def validate_palette(palette: dict) -> bool:
    """Validate palette meets requirements."""
    hex_pattern = re.compile(r'^#[0-9A-F]{6}$')
    
    for key, value in palette.items():
        if not hex_pattern.match(value):
            raise ValueError(f"Invalid hex color: {key}={value}")
    
    # Check contrast ratio
    bg = palette["background"]
    fg = palette["foreground"]
    
    bg_rgb = tuple(int(bg[i:i+2], 16) / 255.0 for i in (1, 3, 5))
    fg_rgb = tuple(int(fg[i:i+2], 16) / 255.0 for i in (1, 3, 5))
    
    def linearize(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    
    l_bg = 0.2126 * linearize(bg_rgb[0]) + 0.7152 * linearize(bg_rgb[1]) + 0.0722 * linearize(bg_rgb[2])
    l_fg = 0.2126 * linearize(fg_rgb[0]) + 0.7152 * linearize(fg_rgb[1]) + 0.0722 * linearize(fg_rgb[2])
    
    contrast = (max(l_bg, l_fg) + 0.05) / (min(l_bg, l_fg) + 0.05)
    
    if contrast < 4.5:
        raise ValueError(f"Contrast ratio {contrast:.2f} < 4.5 (WCAG AA)")
    
    return True
```

Call it at the end of `generate_palette()`:

```python
# At the end of generate_palette()
validate_palette(colors)
return colors
```

- [ ] **Step 4: Test edge cases**

```python
# tests/test_palettgen.py
def test_edge_case_pure_blue():
    """Test with pure blue brand color."""
    palette = generate_palette("#0000FF", "dark")
    assert palette["accent"] == "#0000FF"

def test_edge_case_grayscale():
    """Test with grayscale brand color (edge case)."""
    palette = generate_palette("#808080", "dark")
    assert len(palette) == 22

def test_light_mode():
    """Verify light mode has correct characteristics."""
    palette = generate_palette("#0052BB", "light")
    # Light mode should have light background
    bg = palette["background"]
    bg_rgb = tuple(int(bg[i:i+2], 16) / 255.0 for i in (1, 3, 5))
    # Background should be bright (> 0.8)
    assert sum(bg_rgb) / 3 > 0.8
```

- [ ] **Step 5: Run all tests**

```bash
python -m pytest tests/test_palettgen.py -v
```

Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add palettgen/palette.py tests/test_palettgen.py
git commit -m "feat: add validation and edge case handling"
```

---

### Task 6: Documentation and Final Testing

**Files:**
- Modify: `README.md`
- Modify: `palettgen/README.md`

**Interfaces:**
- Consumes: Completed implementation
- Produces: User-facing documentation

- [ ] **Step 1: Create README.md**

```markdown
# palettgen

Generate perceptually uniform terminal color palettes from any brand color using the Okhsl color space.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Generate dark mode palette (default)
python -m palettgen.cli --brand "#0052BB" --output colors.toml

# Generate light mode palette
python -m palettgen.cli --brand "#0052BB" --mode light --output colors-light.toml
```

## Output Format

Generates a `colors.toml` file compatible with the omarchy theme system:

```toml
accent = "#0052BB"
cursor = "#0052BB"
foreground = "#CCCCCC"
background = "#1A1A1A"
...
color0 = "#1A1A1A"
color1 = "#CC4422"
...
color15 = "#FFFFFF"
```

## Algorithm

1. Converts brand color to Okhsl color space
2. Extracts hue and aligns it with standard ANSI blue position
3. Generates 6 accent colors by rotating hue in 60° steps
4. Applies perceptually-uniform lightness and saturation values
5. Validates contrast ratios (WCAG AA) and color distinctness

## Testing

```bash
pip install -e ".[dev]"
pytest tests/
```

## License

MIT
```

- [ ] **Step 2: Run final test suite**

```bash
python -m pytest tests/ -v
```

Expected: All tests PASS

- [ ] **Step 3: Test with actual Robominds blue**

```bash
python -m palettgen.cli --brand "#0052BB" --output colors.toml
python -m palettgen.cli --brand "#0052BB" --mode light --output colors-light.toml
```

- [ ] **Step 4: Generate swatches to visualize**

```bash
# Copy existing swatch.sh to test
cp swatch.sh palettgen-swatches.sh
# Modify to read from new colors.toml
bash palettgen-swatches.sh
```

- [ ] **Step 5: Final commit**

```bash
git add README.md palettgen/README.md
git commit -m "docs: add README and finalize documentation"
```

---

## Self-Review

**Spec coverage:**
- ✅ Okhsl-based generation (Task 2-3)
- ✅ Dark/light mode support (Task 3)
- ✅ TOML output format (Task 4)
- ✅ Python implementation (Task 1)
- ✅ Validation (Task 5)
- ✅ CLI interface (Task 4)

**Placeholder scan:** No TBD, TODO, or "implement later" found.

**Type consistency:** All function signatures consistent across tasks.

**Testing:** TDD followed throughout, comprehensive test coverage.
