# palettgen

Generate perceptually uniform terminal color palettes from any brand color using the Okhsl color space.

## Features

- **Perceptually uniform**: Uses Okhsl color space for consistent visual appearance
- **Brand-aware**: Aligns palette hues to your brand color
- **Dark/Light mode**: Generate palettes for both modes
- **TOML output**: Compatible with omarchy theme system
- **Validated**: Checks contrast ratios and color distinctness

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
# Generate dark mode palette (default)
python -m palettgen.cli --brand "#0052BB" --output colors.toml

# Generate light mode palette
python -m palettgen.cli --brand "#0052BB" --mode light --output colors-light.toml

# Show help
python -m palettgen.cli --help
```

## Arguments

- `--brand` (required): Brand color in hex format (e.g., #0052BB)
- `--mode`: Color mode - "dark" or "light" (default: dark)
- `--output`: Output file path (default: colors.toml)

## Output Format

Generates a `colors.toml` file with 22 color keys:

```toml
accent = "#0052BB"
cursor = "#0052BB"
foreground = "#E6E6E6"
background = "#1D2730"
selection_foreground = "#1D2730"
selection_background = "#364450"

color0 = "#1D2730"
color1 = "#E86850"
color2 = "#00C090"
color3 = "#FFC000"
color4 = "#00B8D0"
color5 = "#D058A0"
color6 = "#00E0EA"
color7 = "#E6E6E6"
color8 = "#364450"
color9 = "#FF9E50"
color10 = "#00E0CA"
color11 = "#FFD040"
color12 = "#33E6F0"
color13 = "#E070B0"
color14 = "#00E0EA"
color15 = "#FFFFFF"
```

## Algorithm

1. Converts brand color to Okhsl color space
2. Extracts hue and aligns it with standard ANSI blue position (240°)
3. Generates 6 accent colors by rotating hue in 60° steps
4. Applies perceptually-uniform lightness and saturation values
5. Validates contrast ratios and color distinctness

## Testing

```bash
pytest tests/ -v
```

## Examples

```bash
# Robominds blue (dark mode)
python -m palettgen.cli --brand "#0052BB" --output robominds-dark.toml

# Robominds blue (light mode)
python -m palettgen.cli --brand "#0052BB" --mode light --output robominds-light.toml

# GitHub purple
python -m palettgen.cli --brand "#6F42C1" --output github.toml

# VS Code blue
python -m palettgen.cli --brand "#007ACC" --output vscode.toml
```

## Limitations

- Validation threshold: Contrast ratio checked at 3.0:1 (practical minimum) rather than WCAG AA 4.5:1 due to Okhsl color space constraints
- Edge cases: Very dark or very light brand colors may produce limited palette variation

## License

MIT

## References

- [Oklab color space](https://bottosson.github.io/posts/oklab/)
- [Okhsl color model](https://bottosson.github.io/posts/colorpicker/)
- [Ham Vocke's terminal color scheme article](https://hamvocke.com/blog/lets-create-a-terminal-color-scheme/)
