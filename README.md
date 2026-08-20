# omarchy-robominds-theme

Omarchy theme for robominds, using the official robominds brand colors extracted from the [living style guide](https://brand.robominds.de).

The color scheme is extracted directly from the style guide's `tokens.css` (the Single Source of Truth for all robominds design tokens). When the style guide is updated, re-running the update script pulls the latest colors.

## Update the theme

```bash
# Prerequisites: Python 3.11+
pip install Pillow  # only needed for preview image generation

# From a local style guide (tokens.css or index.html)
python scripts/update_theme.py --tokens tmp/robominds-styleguide/css/tokens.css

# From the live style guide URL
python scripts/update_theme.py --url https://brand.robominds.de
```

This generates:
- `colors.toml` — terminal colors (quattro format with semantic names)
- `shell.lock.toml` — shell lock screen colors
- `keyboard.rgb` — keyboard RGB accent color

## Color mapping

The robominds style guide tokens map to the omarchy quattro theme as follows:

| Theme key | CSS token | Description |
|-----------|-----------|-------------|
| `accent` | `--rm-blue-700` | robominds Blue (primary) |
| `background` | `--rm-navy-grey-1` | Main background |
| `dark_background` | `--rm-navy-grey-2` | Darker background |
| `darker_background` | `--rm-ref-ral-9005` | Darkest background |
| `lighter_background` | `--rm-midnight` | Lighter background |
| `foreground` | `--rm-gray-200` | Main foreground |
| `dark_foreground` | `--rm-gray-400` | Dimmed foreground |
| `light_foreground` | `--rm-gray-100` | Brighter foreground |
| `bright_foreground` | `--rm-white` | Brightest foreground |
| `red` / `bright_red` | `--rm-red-500` / `--rm-red-300` | Red family |
| `yellow` / `bright_yellow` | `--rm-yellow-500` / `--rm-yellow-300` | Yellow family |
| `orange` | `--rm-orange-500` | Orange |
| `green` / `bright_green` | `--rm-green-500` / `--rm-green-300` | Green family |
| `cyan` / `bright_cyan` | `--rm-teal-500` / `--rm-teal-300` | Teal family |
| `blue` / `bright_blue` | `--rm-blue-700` / `--rm-blue-600` | Blue family |
| `magenta` / `bright_magenta` | `--rm-violet-500` / `--rm-violet-300` | Violet family |
| `brown` | `--rm-orange-700` | Dark orange |
| `selection` | `--rm-navy-grey-1` | Selection background |
| `muted` | `--rm-gray-800` | Muted UI elements |

## Theme files

| File | Purpose |
|------|---------|
| `colors.toml` | Terminal colors (quattro semantic format) |
| `shell.lock.toml` | Shell lock screen colors |
| `keyboard.rgb` | Keyboard RGB accent color |
| `neovim.lua` | Neovim colorscheme config |
| `vscode.json` | VS Code theme extension |
| `icons.theme` | Icon theme name |
| `backgrounds/` | Wallpaper images |
| `unlock.png` | Lock screen image |

## License

MIT
