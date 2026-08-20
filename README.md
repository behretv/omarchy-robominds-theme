# omarchy-robominds-theme

Omarchy theme for robominds, using the official robominds brand colors extracted from the [living style guide](https://brand.robominds.de).

The color scheme is **not calculated** — it is extracted directly from the style guide's `tokens.css` (the Single Source of Truth for all robominds design tokens). When the style guide is updated, re-running the update script pulls the latest colors.

## Update the theme

```bash
# Prerequisites: Python 3.11+ with Pillow
pip install Pillow

# From a local style guide (tokens.css or index.html)
python scripts/update_theme.py --tokens tmp/robominds-styleguide/css/tokens.css

# From the live style guide URL
python scripts/update_theme.py --url https://brand.robominds.de
```

This single command:
1. Parses `tokens.css` for all `--rm-*` color tokens
2. Maps them to the 16-color ANSI palette + UI colors (dark and light modes)
3. Writes `colors.toml` and `colors-light.toml`
4. Generates `images/palette-dark.png` and `images/palette-light.png`
5. Updates this README with the palette images

## Color mapping

The 16 ANSI colors map to the robominds brand families:

| Row | Slot | Token | Description |
|-----|------|-------|-------------|
| **Dark** | `color0` (bg) | `--rm-navy-grey-2` | Darkest background |
| | `color1` (red) | `--rm-red-700` | Dark red |
| | `color2` (green) | `--rm-green-700` | Dark green |
| | `color3` (yellow) | `--rm-yellow-700` | Dark yellow |
| | `color4` (blue) | `--rm-blue-700` | robominds Blue (primary) |
| | `color5` (purple) | `--rm-violet-700` | Dark violet |
| | `color6` (aqua) | `--rm-teal-700` | Dark teal |
| | `color7` (gray) | `--rm-gray-400` | Mid gray |
| **Bright** | `color8` (gray) | `--rm-navy-grey-1` | Bright background |
| | `color9` (red) | `--rm-red-500` | Red |
| | `color10` (green) | `--rm-green-500` | Green |
| | `color11` (yellow) | `--rm-yellow-500` | Yellow |
| | `color12` (blue) | `--rm-blue-600` | Blue light |
| | `color13` (purple) | `--rm-violet-500` | Violet |
| | `color14` (aqua) | `--rm-teal-500` | Teal |
| | `color15` (fg) | `--rm-gray-200` | Foreground (dark) / `--rm-midnight` (light) |

UI colors: `accent` and `cursor` use `--rm-blue-700`, `background`/`foreground` use the appropriate bg/fg slots, `selection_*` use `--rm-navy-grey-1`/`--rm-gray-100`.

## Output format

`colors.toml` and `colors-light.toml` each contain 22 keys: `accent`, `cursor`, `foreground`, `background`, `selection_foreground`, `selection_background`, and `color0`–`color15`.

## Palette

### Dark mode

![Palette Dark](images/palette-dark.png)

### Light mode

![Palette Light](images/palette-light.png)


## Omarchy theme files

| File | Purpose |
|------|---------|
| `colors.toml` | Dark mode terminal colors |
| `colors-light.toml` | Light mode terminal colors |
| `btop.theme` | btop system monitor theme |
| `hyprland.lua` | Hyprland window manager colors |
| `neovim.lua` | Neovim colorscheme config |
| `vscode.json` | VS Code theme extension |
| `icons.theme` | Icon theme name |
| `backgrounds/` | Wallpaper images |
| `unlock.png` | Lock screen image |

## License

MIT
