# omarchy-robominds-dark

Omarchy theme for robominds, using the official robominds brand colors extracted from the [living style guide](https://brand.robominds.de).

The color scheme is extracted directly from the style guide's `tokens.css` (the Single Source of Truth for all robominds design tokens). When the style guide is updated, re-running the update script pulls the latest colors.

## Install

```bash
omarchy theme install https://github.com/<org>/omarchy-robominds-dark.git
```

Or via the Makefile:

```bash
make install    # clone + apply
make update     # pull latest + re-apply
make apply TOKENS=/path/to/tokens.css   # regenerate from style guide + re-apply
make apply URL=https://brand.robominds.de
```

## Update the theme

```bash
# Prerequisites: Python 3.11+

# Generate theme files from a local style guide
python scripts/update_theme.py --tokens tmp/robominds-styleguide/css/tokens.css

# From the live style guide URL
python scripts/update_theme.py --url https://brand.robominds.de
```

This generates:
- `colors.toml` — terminal colors (quattro format with semantic names)
- `shell.lock.toml` — shell lock screen colors
- `keyboard.rgb` — keyboard RGB accent color

`colors.toml` is the only file the installed theme needs: omarchy generates every per-app config (VS Code, Neovim, terminals, ...) from it via templates on `omarchy theme set`.

## Color mapping

The robominds style guide tokens map to the omarchy quattro theme as follows:

| Theme key | CSS token | Description |
|-----------|-----------|-------------|
| `accent` | `--rm-blue-400` | robominds Blue (primary) |
| `selection` | `--rm-navy-grey-1` | Selection background |
| `muted` | `#6B6B6B` | Muted UI elements / comments |
| `background` | `--rm-navy-grey-1` | Main background |
| `dark_background` | `--rm-navy-grey-2` | Darker background |
| `darker_background` | `#0A0A0A` | Darkest background |
| `lighter_background` | `--rm-blue-900` | Lighter background |
| `foreground` | `--rm-gray-300` | Main foreground |
| `dark_foreground` | `--rm-gray-700` | Dimmed foreground |
| `light_foreground` | `--rm-gray-400` | Brighter foreground |
| `bright_foreground` | `--rm-gray-200` | Brightest foreground |
| `red` / `bright_red` | `--rm-red-300` / `--rm-red-500` | Red family |
| `yellow` / `bright_yellow` | `--rm-yellow-300` / `--rm-yellow-500` | Yellow family |
| `orange` | `--rm-orange-500` | Orange |
| `green` / `bright_green` | `--rm-green-300` / `--rm-green-500` | Green family |
| `cyan` / `bright_cyan` | `--rm-teal-300` / `--rm-teal-500` | Teal family |
| `blue` / `bright_blue` | `--rm-blue-400` / `--rm-blue-500` | Blue family |
| `magenta` / `bright_magenta` | `--rm-violet-300` | Violet family |
| `brown` | `--rm-orange-700` | Dark orange |

## Theme files

| File | Purpose |
|------|---------|
| `colors.toml` | Terminal colors (quattro semantic format) — the only file omarchy needs; it generates per-app configs from it |
| `shell.lock.toml` | Shell lock screen colors |
| `keyboard.rgb` | Keyboard RGB accent color |
| `icons.theme` | Icon theme name |
| `backgrounds/` | Wallpaper images |
| `unlock.png` | Lock screen image |

## License

MIT
