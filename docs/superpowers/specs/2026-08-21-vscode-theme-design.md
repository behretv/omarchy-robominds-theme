# Robominds VS Code Color Theme — Design

Date: 2026-08-21
Status: approved for planning

## Goal

When a user of this omarchy theme switches to it (`omarchy theme set robominds`),
VS Code should automatically switch to a robominds-branded VS Code color theme.
Scope: **VS Code Marketplace only** for now; Open VSX (VSCodium/Cursor) is a
follow-up.

## Background / confirmed mechanics

- The repo is installed via `omarchy-theme-install <git-url>`, which clones it to
  `~/.config/omarchy/themes/robominds`. All theme files live at the repo root.
- `omarchy-theme-set-vscode` reads the theme's `vscode.json`
  (`{"name": ..., "extension": "<publisher>.<id>"}`). If the referenced VS Code
  extension is not installed it runs `code --install-extension <id>`, then writes
  `"workbench.colorTheme": "<name>"` into `settings.json` of VS Code, VSCodium,
  and Cursor (each gated by a skip-toggle).
- The single source of truth for colors is the robominds style guide
  `tokens.css`; `scripts/update_theme.py` already parses it and generates
  `colors.toml`, `shell.lock.toml`, `keyboard.rgb`.
- The color keys in `colors.toml` cover all 19 color variables used by
  omarchy's built-in `vscode-theme.json.tpl` (plus derived
  `selection_background`/`selection_foreground` and `theme_type` — 22
  variables in total, all satisfiable from `colors.toml`), so a theme generated
  from the same tokens is validated by omarchy's own rendering path.
- Node/npm are available locally (`@vscode/vsce` via `npx`) for packaging.
- Marketplace publisher: `robominds`. Extension id: `robominds.robominds`.
  Theme label: `robominds`.

## Decisions

- Keep the VS Code extension source **in this repo** (a `vscode/` subdirectory),
  not a separate repository. One source of truth, one update run.
- **Approach B** for generation: extend `scripts/update_theme.py` to also
  generate the VS Code theme JSON from the same `tokens.css` parse. Publishing
  is a manual `vsce publish` (via Makefile) for now; GitHub Actions publish
  (and Open VSX) is deferred.

## Design

### 1. Repo layout

```
vscode/
├── package.json                     # static: name "robominds", publisher
│                                    #   "robominds", version,
│                                    #   contributes.themes -> label "robominds",
│                                    #   uiTheme "vs-dark",
│                                    #   path ./themes/robominds-color-theme.json
├── LICENSE                          # MIT (required by vsce; ext-level copy)
├── README.md                        # short, used as the marketplace listing
└── themes/
    └── robominds-color-theme.json   # GENERATED — checked in, packed by vsce
Makefile
vscode.json                          # -> {"name": "robominds",
                                     #     "extension": "robominds.robominds"}
```

### 2. Theme JSON generation

- Add a committed template `vscode/themes/robominds-color-theme.json.tpl`,
  copied verbatim from omarchy's built-in
  `/usr/share/omarchy/default/themed/vscode-theme.json.tpl`. It is complete
  (UI `colors`, `tokenColors`, `semanticTokenColors`) and uses only these
  variables:
  `accent, background, blue, bright_blue, bright_cyan, bright_foreground,
  bright_green, bright_magenta, bright_red, bright_yellow, cyan,
  dark_foreground, foreground, green, magenta, muted, orange, red, yellow,
  selection_background, selection_foreground, theme_type`.
- `update_theme.py` gains `generate_vscode_theme(tokens) -> str`:
  - plain `{{ key }}` substitution for all resolved token colors,
  - `theme_type` from `mode` (`dark`/`light`),
  - derived values matching omarchy: `selection_background = selection`,
    `selection_foreground = bright_foreground`,
  - fails (non-zero exit) if any `{{ }}` placeholder survives or a required
    key is missing.
- Output written to `vscode/themes/robominds-color-theme.json`, next to the
  existing generated files. No new CLI flags: `--tokens`/`--url` unchanged.
- The `.tpl` file is excluded from the packed `.vsix` (vsce `files` field in
  `package.json`; only the generated JSON ships).

### 3. `vscode.json` (omarchy descriptor)

Replaces the current Kanagawa reference:

```json
{
  "name": "robominds",
  "extension": "robominds.robominds"
}
```

### 4. Makefile (repo root)

```makefile
STYLEGUIDE_URL ?= https://brand.robominds.de
TOKENS       ?=
PUBLISHER    ?= robominds
VSCODE_SETTINGS ?= $(HOME)/.config/Code/User/settings.json

.PHONY: update vscode-login test-vscode apply-vscode-theme untest-vscode publish-vscode

update:
ifeq ($(TOKENS),)
	python3 scripts/update_theme.py --url $(STYLEGUIDE_URL)
else
	python3 scripts/update_theme.py --tokens $(TOKENS)
endif

vscode-login:
	cd vscode && npx -y @vscode/vsce login $(PUBLISHER)

test-vscode:
	code --install-extension --force vscode
	$(MAKE) -s apply-vscode-theme

apply-vscode-theme:
	# insert/replace "workbench.colorTheme": "robominds" in $(VSCODE_SETTINGS)
	# (sed, following the omarchy-theme-set-vscode approach)

untest-vscode:
	# remove the "workbench.colorTheme" line from $(VSCODE_SETTINGS)

publish-vscode:
	cd vscode && npx -y @vscode/vsce publish
```

- `update` — regenerate all theme files from the style guide (URL or local
  `TOKENS` path).
- `vscode-login` — one-time `vsce login robominds` (Prompts for the PAT).
- `test-vscode` — install the local extension (`--force`) and apply "robominds"
  to the local VS Code; no marketplace involved; no restart needed. Delegates
  the settings.json edit to `apply-vscode-theme` (the sed insert/replace step),
  which is also what `untest-vscode`'s cleanup mirrors.
- `untest-vscode` — remove the `workbench.colorTheme` override so omarchy's
  own theming (or the user's previous choice) applies again.
- `publish-vscode` — publish to the VS Code Marketplace. Version bump in
  `vscode/package.json` remains manual and intentional (vsce refuses to
  publish an existing version).

### 5. Publish workflow (manual, for now)

1. `make update`
2. Review the generated diff (including `vscode/themes/robominds-color-theme.json`).
3. `make test-vscode` — verify in a real VS Code.
4. Bump `version` in `vscode/package.json` if colors/content shipped.
5. `make vscode-login` (first time only).
6. `make publish-vscode`.
7. `omarchy theme set robominds` — installs the published extension (if not
   already present) and switches the workbench theme to "robominds".
8. `make untest-vscode` (optional cleanup of the local test override).

## Verification

- Generation correctness: script exits non-zero on leftover `{{ }}` or missing
  keys; `python3 -m json.tool` on the generated JSON.
- Local: `make test-vscode` and visually inspect colors in VS Code
  (editor, UI chrome, at least Python and Markdown syntax).
- After first publish: `omarchy theme set robominds` on a machine without the
  extension installed — it must install `robominds.robominds` and set
  `"workbench.colorTheme": "robominds"` in `~/.config/Code/User/settings.json`.

## Out of scope (deferred follow-ups)

- GitHub Actions publish workflow (tag-triggered, PAT as repo secret) — the
  "C" step.
- Open VSX publication (VSCodium/Cursor auto-switching); same `.vsix`, one
  additional `openvsx publish` command once CI exists.
- Light mode variant (robominds tokens are dark-first; `theme_type` handling
  already supports a future light theme).
