# omarchy-robominds-theme

Omarchy theme for robominds, using the official robominds brand colors extracted from the [living style guide](https://brand.robominds.de).

The color scheme is extracted directly from the style guide's `tokens.css` (the Single Source of Truth for all robominds design tokens). When the style guide is updated, re-running the update script pulls the latest colors.

## Update the theme

```bash
# Prerequisites: Python 3.11+

# Generate all theme files from a local style guide
python scripts/update_theme.py --tokens tmp/robominds-styleguide/css/tokens.css

# Generate everything AND install to VS Code in one command
python scripts/update_theme.py --tokens tmp/robominds-styleguide/css/tokens.css --install-vscode

# Shorthand: -a does the same as --install-vscode
python scripts/update_theme.py --tokens tmp/robominds-styleguide/css/tokens.css -a

# From the live style guide URL
python scripts/update_theme.py --url https://brand.robominds.de -a
```

This generates:
- `colors.toml` — terminal colors (quattro format with semantic names)
- `shell.lock.toml` — shell lock screen colors
- `keyboard.rgb` — keyboard RGB accent color
- `vscode/robominds-color-theme.json` — VS Code color theme (rendered from omarchy's template with robominds colors)

With `--install-vscode` / `-a`, it also installs the theme as a local VS Code extension at `~/.vscode/extensions/local.robominds-theme/` (and equivalents for VSCodium and Cursor if installed). After installing, switching to the robominds theme in omarchy automatically activates the robominds VS Code theme.

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
| `colors.toml` | Terminal colors (quattro semantic format) |
| `shell.lock.toml` | Shell lock screen colors |
| `keyboard.rgb` | Keyboard RGB accent color |
| `vscode/robominds-color-theme.json` | VS Code color theme (generated from omarchy template) |
| `vscode.json` | VS Code extension reference (points to local.robominds-theme) |
| `vscode/package.json` | VS Code extension manifest |
| `neovim.lua` | Neovim colorscheme config |
| `icons.theme` | Icon theme name |
| `backgrounds/` | Wallpaper images |
| `unlock.png` | Lock screen image |

## License

MIT
