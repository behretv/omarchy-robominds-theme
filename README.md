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

Generated palette swatches (auto-generated — do not edit by hand):

| Name | Hex | Swatch | Conventional Role |
|------|-----|--------|-------------------|
| `color0` | `#000000` | ![#000000](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%23000000%22/%3E%3C/svg%3E) | black |
| `color1` | `#FF0010` | ![#FF0010](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%23FF0010%22/%3E%3C/svg%3E) | red |
| `color2` | `#083400` | ![#083400](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%23083400%22/%3E%3C/svg%3E) | green |
| `color3` | `#FF0000` | ![#FF0000](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%23FF0000%22/%3E%3C/svg%3E) | yellow |
| `color4` | `#1E00FF` | ![#1E00FF](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%231E00FF%22/%3E%3C/svg%3E) | blue |
| `color5` | `#C800FF` | ![#C800FF](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%23C800FF%22/%3E%3C/svg%3E) | magenta |
| `color6` | `#007538` | ![#007538](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%23007538%22/%3E%3C/svg%3E) | cyan |
| `color7` | `#9D9D9D` | ![#9D9D9D](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%239D9D9D%22/%3E%3C/svg%3E) | white |
| `color8` | `#040404` | ![#040404](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%23040404%22/%3E%3C/svg%3E) | bright black |
| `color9` | `#FF0034` | ![#FF0034](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%23FF0034%22/%3E%3C/svg%3E) | bright red |
| `color10` | `#287F00` | ![#287F00](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%23287F00%22/%3E%3C/svg%3E) | bright green |
| `color11` | `#FF0000` | ![#FF0000](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%23FF0000%22/%3E%3C/svg%3E) | bright yellow |
| `color12` | `#0000FF` | ![#0000FF](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%230000FF%22/%3E%3C/svg%3E) | bright blue |
| `color13` | `#FF00FF` | ![#FF00FF](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%23FF00FF%22/%3E%3C/svg%3E) | bright magenta |
| `color14` | `#00FF87` | ![#00FF87](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%2300FF87%22/%3E%3C/svg%3E) | bright cyan |
| `color15` | `#DBDBDB` | ![#DBDBDB](data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%20width%3D%2212%22%20height%3D%2212%22%3E%3Crect%20width%3D%2212%22%20height%3D%2212%22%20fill%3D%22%23DBDBDB%22/%3E%3C/svg%3E) | bright white |

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
