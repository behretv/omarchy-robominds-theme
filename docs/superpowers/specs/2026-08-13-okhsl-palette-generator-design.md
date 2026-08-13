# Okhsl-based Terminal Color Palette Generator

**Date:** 2026-08-13  
**Status:** Approved  

## Overview

Generate a perceptually uniform 16-color ANSI palette from any single brand color, with dark/light mode support. Outputs a `colors.toml` matching the existing omarchy theme format.

## Problem

Creating terminal color schemes by hand is difficult. HSL-based generation produces perceptually uneven results (blues look darker than yellows at the same lightness). We need a scientific method that:

1. Works from a single brand color (e.g., Robominds blue `#0052BB`)
2. Produces perceptually uniform colors
3. Supports both dark and light modes
4. Outputs the existing `colors.toml` format
5. Is maintainable and extensible

## Solution: Okhsl-based Generation

### Why Okhsl?

- Perceptually uniform (addresses HSL's shortcomings)
- Mathematical simplicity (predictable parameter ranges)
- Combines benefits of HSL and Oklab

### Algorithm

**Input:**
- Brand color (hex, e.g., `#0052BB`)
- Mode: `dark` (default) or `light`

**Step 1: Convert to Okhsl**
```
Brand color → Okhsl(L, S, H)
Extract hue (H) as the anchor
```

**Step 2: Generate 6 ANSI accent hues**
- Standard positions: 0° (red), 60° (yellow), 120° (green), 180° (cyan), 240° (blue), 300° (magenta)
- Shift all hues so one aligns with the brand hue
- Example: brand hue 207° → shift = 207° - 240° = -33°
- Result: red=327°, yellow=27°, green=87°, cyan=147°, blue=207°, magenta=267°

**Step 3: Assign lightness and saturation per mode**

*Dark mode:*
- Base grays: black L=8%, bright black L=25%, white L=70%, bright white L=95%
- Regular accents: L=50%, S=85%
- Bright accents: L=70%, S=90%

*Light mode:*
- Base grays: black L=95%, bright black L=80%, white L=30%, bright white L=5%
- Regular accents: L=45%, S=80%
- Bright accents: L=60%, S=85%

**Step 4: Convert back to hex**
```
Okhsl(L, S, H) → RGB → #RRGGBB
```

**Step 5: Map to ANSI positions**
- color0 = black
- color1 = red
- color2 = green
- color3 = yellow
- color4 = blue (aligns with brand hue)
- color5 = magenta
- color6 = cyan
- color7 = white
- color8 = bright black
- color9 = bright red
- color10 = bright green
- color11 = bright yellow
- color12 = bright blue (brand color)
- color13 = bright magenta
- color14 = bright cyan
- color15 = bright white

**Additional keys:**
- `accent` = color12 (bright blue, the brand color)
- `cursor` = color12
- `foreground` = white (color7)
- `background` = black (color0)
- `selection_foreground` = background
- `selection_background` = accent

### Output Format

```toml
accent = "#0052BB"
cursor = "#0052BB"
foreground = "#CCCCCC"
background = "#1A1A1A"
selection_foreground = "#1A1A1A"
selection_background = "#0052BB"

color0 = "#1A1A1A"
color1 = "#CC4422"
color2 = "#44AA66"
color3 = "#CCAA22"
color4 = "#0052BB"
color5 = "#AA44CC"
color6 = "#2288AA"
color7 = "#CCCCCC"
color8 = "#444444"
color9 = "#FF6644"
color10 = "#66CC88"
color11 = "#FFCC44"
color12 = "#0052BB"
color13 = "#CC66EE"
color14 = "#44AACC"
color15 = "#FFFFFF"
```

## File Structure

```
palettgen/
├── palettgen.py          # Main generator script
├── README.md             # Usage instructions
└── tests/
    └── test_palettgen.py # Unit tests
```

## CLI Interface

```bash
# Generate dark mode palette (default)
python palettgen.py --brand #0052BB --output colors.toml

# Generate light mode palette
python palettgen.py --brand #0052BB --mode light --output colors-light.toml

# Show help
python palettgen.py --help
```

## Dependencies

- `culori` (Python) — for Okhsl color space conversion
- Standard library:
  - `tomllib` (Python 3.11+) or `tomli` for older versions
  - `argparse`
  - `colorsys` (fallback if needed)

## Validation

1. **Valid hex:** All output colors must be valid `#RRGGBB` format
2. **Contrast ratio:** Background vs foreground ≥ 4.5:1 (WCAG AA)
3. **Distinctness:** All 16 ANSI colors must be visually distinct (CIE76 delta-E > 10)

## Testing

- Unit tests for Okhsl conversion
- Round-trip tests (hex → Okhsl → hex)
- Contrast ratio validation
- Delta-E distinctness checks
- Edge cases: pure black, pure white, grayscale brand colors

## Future Extensions

- Support for 256-color palettes
- Custom hue offsets (e.g., brand doesn't align with standard blue)
- Export to other formats (Alacritty, Kitty, VS Code, etc.)
- Integration with existing `swatch.sh` for visualization

## References

- [Oklab color space](https://bottosson.github.io/posts/oklab/)
- [Okhsl color model](https://bottosson.github.io/posts/colorpicker/)
- [culori.js](https://culorijs.org/)
- [Ham Vocke's article on terminal color schemes](https://hamvocke.com/blog/lets-create-a-terminal-color-scheme/)
