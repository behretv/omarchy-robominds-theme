# Robominds VS Code Color Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `scripts/update_theme.py` to also generate a VS Code color theme extension (`robominds.robominds`) from the same robominds style-guide tokens, so `omarchy theme set robominds` switches VS Code to a robominds-branded theme.

**Architecture:** A committed template (`vscode/themes/robominds-color-theme.json.tpl`, copied from omarchy's built-in template with the name changed) is rendered by a new `generate_vscode_theme(tokens)` function that substitutes `{{ key }}` placeholders from the parsed `tokens.css` tokens. The rendered JSON is checked in and packed by `vsce` into a `vscode/` extension subdirectory. A root `Makefile` wraps update/test/publish; `vscode.json` points omarchy at the published extension.

**Tech Stack:** Python 3.11+ (stdlib only), Make, `@vscode/vsce` via `npx` (Node 25 available), `code` CLI.

## Global Constraints

- Python is **stdlib only** — no new Python dependencies, no pytest (tests use `unittest`, run with `python3 -m unittest discover -s tests -v`).
- Extension publisher is `robominds`, extension id `robominds.robominds`, theme label `robominds`.
- The template uses exactly these 22 variables: `accent, background, blue, bright_blue, bright_cyan, bright_foreground, bright_green, bright_magenta, bright_red, bright_yellow, cyan, dark_foreground, foreground, green, magenta, muted, orange, red, selection_background, selection_foreground, theme_type, yellow`.
- Derived values must match omarchy: `selection_background` = the `selection` color, `selection_foreground` = `bright_foreground`, `theme_type` = `mode`.
- Generation must **fail (ValueError → non-zero exit)** if any `{{ }}` placeholder survives or a required token is missing.
- The `.tpl` file must NOT be shipped inside the packed `.vsix` (controlled by the `files` field in `vscode/package.json`).
- The live style guide URL `https://brand.robominds.de` may be unreachable from the dev machine; the committed fixture `tests/fixtures/tokens.css` is the offline source of truth for all regeneration and test steps.
- `code --install-extension <path> --force` — in this CLI version `--force` must come **after** the path (before it, the path is consumed as the `--force` value and install fails).
- `code --install-extension` accepts a `.vsix` file or a marketplace id, **not** a source folder — local testing must package first.

---

### Task 1: VS Code extension scaffolding

**Files:**
- Create: `vscode/themes/robominds-color-theme.json.tpl` (template, generated from omarchy's built-in)
- Create: `vscode/package.json`
- Create: `vscode/LICENSE` (copy of the repo-root `LICENSE`)
- Create: `vscode/README.md`
- Modify: `.gitignore` (append `vscode/*.vsix`)

**Interfaces:**
- Consumes: omarchy's built-in template at `/usr/share/omarchy/default/themed/vscode-theme.json.tpl` (must exist on the dev machine; it is part of the omarchy system install).
- Produces: a template file whose only `{{ }}` placeholders are the 22 variables listed in Global Constraints, and a valid `vscode/package.json` that `vsce` can package.

- [ ] **Step 1: Create the template directory and template file**

Run:

```bash
mkdir -p vscode/themes
sed 's/"name": "Omarchy"/"name": "robominds"/' \
  /usr/share/omarchy/default/themed/vscode-theme.json.tpl \
  > vscode/themes/robominds-color-theme.json.tpl
```

Expected: `vscode/themes/robominds-color-theme.json.tpl` exists (~60 KB). If `/usr/share/omarchy/default/themed/vscode-theme.json.tpl` does not exist on the machine, stop and report — the plan depends on it.

- [ ] **Step 2: Create `vscode/package.json`**

Write `vscode/package.json`:

```json
{
    "name": "robominds",
    "displayName": "Robominds",
    "description": "Robominds color theme for VS Code, generated from the robominds brand style guide tokens.",
    "version": "0.1.0",
    "publisher": "robominds",
    "license": "MIT",
    "engines": { "vscode": "^1.70.0" },
    "categories": ["Themes"],
    "repository": {
        "type": "git",
        "url": "https://github.com/behretv/omarchy-robominds-theme.git"
    },
    "contributes": {
        "themes": [
            {
                "label": "robominds",
                "uiTheme": "vs-dark",
                "path": "./themes/robominds-color-theme.json"
            }
        ]
    },
    "files": [
        "themes/robominds-color-theme.json",
        "LICENSE",
        "README.md",
        "package.json"
    ]
}
```

- [ ] **Step 3: Create `vscode/LICENSE` and `vscode/README.md`**

Run:

```bash
cp LICENSE vscode/LICENSE
```

Write `vscode/README.md`:

```markdown
# Robominds

Robominds color theme for VS Code.

Generated from the robominds brand style guide tokens
(`<https://brand.robominds.de>` — `tokens.css`) by
`scripts/update_theme.py` in the
[omarchy-robominds-theme](https://github.com/behretv/omarchy-robominds-theme)
repository.

## Install

    code --install-extension robominds.robominds

or simply switch the omarchy theme to robominds:

    omarchy theme set robominds

## License

MIT
```

- [ ] **Step 4: Exclude `.vsix` from git**

Append this line to `.gitignore` (which currently contains `__pycache__/`, `*.pyc`, `.venv/`, `.superpowers/`, `*egg-info/`, `.ruff_cache/`, `tmp/`):

```
vscode/*.vsix
```

- [ ] **Step 5: Verify the template**

Run:

```bash
python3 -m json.tool vscode/package.json > /dev/null && echo "package.json OK"
python3 - <<'EOF'
import json, re
from pathlib import Path
tpl = Path("vscode/themes/robominds-color-theme.json.tpl").read_text()
placeholders = sorted(set(re.findall(r"\{\{\s*(\w+)\s*\}\}", tpl)))
expected = sorted([
    "accent", "background", "blue", "bright_blue", "bright_cyan",
    "bright_foreground", "bright_green", "bright_magenta", "bright_red",
    "bright_yellow", "cyan", "dark_foreground", "foreground", "green",
    "magenta", "muted", "orange", "red", "selection_background",
    "selection_foreground", "theme_type", "yellow",
])
assert placeholders == expected, f"placeholder mismatch: {placeholders}"
dummy = {k: "#FF0000" for k in expected}
rendered = re.sub(r"\{\{\s*(\w+)\s*\}\}", lambda m: dummy[m.group(1)], tpl)
parsed = json.loads(rendered)
assert parsed["name"] == "robominds"
assert parsed["type"] == "#FF0000"  # theme_type placeholder, sanity only
print(f"template OK: {len(placeholders)} placeholders, {len(parsed['colors'])} colors")
EOF
```

Expected: `package.json OK` and `template OK: 22 placeholders, 664 colors`.

- [ ] **Step 6: Commit**

```bash
git add vscode/ .gitignore
git commit -m "Add VS Code extension scaffolding with theme template"
```

---

### Task 2: `generate_vscode_theme` in `update_theme.py`

**Files:**
- Create: `tests/fixtures/tokens.css` (offline token fixture — exact values from the committed `colors.toml`)
- Create: `tests/test_update_theme.py`
- Modify: `scripts/update_theme.py` (add `VSCODE_TEMPLATE`, `_vscode_value_for`, `generate_vscode_theme` after the `generate_keyboard_rgb` function at line ~235; wire into `main()` after the `keyboard.rgb` write at line ~308; update module docstring line 5-7)
- Create (generated, checked in): `vscode/themes/robominds-color-theme.json`

**Interfaces:**
- Consumes: `parse_tokens_css` (line 86), `_resolve_color` (line 204), `TOKEN_MAPPING` (line 34), `write_file` (line 238) from `scripts/update_theme.py`; the template from Task 1.
- Produces: `generate_vscode_theme(tokens: dict[str, str], template_path: Path | None = None) -> str` — renders the committed template (default) or an explicit template path, raises `ValueError` on missing tokens or leftover placeholders. Later tasks call it via `make update`.

- [ ] **Step 1: Create the token fixture**

Run: `mkdir -p tests/fixtures`

Write `tests/fixtures/tokens.css` (these 19 values are the exact inverse of `TOKEN_MAPPING` applied to the committed `colors.toml`; regenerating from them reproduces every committed theme file byte-for-byte):

```css
:root {
  --rm-blue-400: #64B7F7;
  --rm-blue-500: #2593F4;
  --rm-blue-700: #0052BB;
  --rm-gray-100: #F2F2F2;
  --rm-gray-200: #E6E6E6;
  --rm-gray-400: #BBBBBB;
  --rm-gray-800: #3C3C3C;
  --rm-green-300: #6FC08D;
  --rm-midnight: #262626;
  --rm-navy-grey-1: #1D2731;
  --rm-navy-grey-2: #0E0E13;
  --rm-orange-300: #F0A96A;
  --rm-orange-500: #E4761B;
  --rm-red-300: #E88585;
  --rm-ref-ral-9005: #0A0A0A;
  --rm-teal-300: #66BDB6;
  --rm-violet-300: #A98BE0;
  --rm-white: #FFFFFF;
  --rm-yellow-300: #F4C64D;
}
```

- [ ] **Step 2: Write the failing tests**

Write `tests/test_update_theme.py`:

```python
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import update_theme as ut

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "tokens.css"
TEMPLATE = REPO_ROOT / "vscode" / "themes" / "robominds-color-theme.json.tpl"


def load_fixture_tokens():
    return ut.parse_tokens_css(FIXTURE.read_text(encoding="utf-8"))


class GenerateVscodeThemeTests(unittest.TestCase):
    def setUp(self):
        self.tokens = load_fixture_tokens()

    def test_generates_valid_json(self):
        result = ut.generate_vscode_theme(self.tokens, TEMPLATE)
        parsed = json.loads(result)
        self.assertEqual(parsed["name"], "robominds")
        self.assertEqual(parsed["type"], "dark")

    def test_no_placeholders_remain(self):
        result = ut.generate_vscode_theme(self.tokens, TEMPLATE)
        self.assertIsNone(re.search(r"\{\{.*?\}\}", result))

    def test_color_values_match_omarchy_derivation(self):
        parsed = json.loads(ut.generate_vscode_theme(self.tokens, TEMPLATE))
        colors = parsed["colors"]
        self.assertEqual(colors["editor.background"], "#1D2731")
        self.assertEqual(colors["terminal.background"], "#1D2731")
        self.assertEqual(colors["selection.background"], "#1D273180")
        self.assertEqual(colors["editor.selectionBackground"], "#1D273160")
        self.assertEqual(colors["editor.selectionForeground"], "#FFFFFF")

    def test_missing_token_raises(self):
        tokens = {k: v for k, v in self.tokens.items() if k != "--rm-white"}
        with self.assertRaises(ValueError):
            ut.generate_vscode_theme(tokens, TEMPLATE)

    def test_unsubstituted_placeholder_raises(self):
        with tempfile.NamedTemporaryFile("w", suffix=".tpl", delete=False) as f:
            f.write('{"accent": "{{ accent }}", "x": "{{ not_a_real_key }}"}')
            path = Path(f.name)
        try:
            with self.assertRaises(ValueError):
                ut.generate_vscode_theme(self.tokens, path)
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `python3 -m unittest discover -s tests -v`

Expected: 5 failures, each with `AttributeError: module 'update_theme' has no attribute 'generate_vscode_theme'`.

- [ ] **Step 4: Implement `generate_vscode_theme`**

In `scripts/update_theme.py`, add these lines after the `generate_keyboard_rgb` function (which ends at line 235, before the `write_file` function):

```python
# ---------------------------------------------------------------------------
# VS Code theme generation
# ---------------------------------------------------------------------------
VSCODE_TEMPLATE = (
    Path(__file__).resolve().parent.parent
    / "vscode"
    / "themes"
    / "robominds-color-theme.json.tpl"
)


def _vscode_value_for(key: str, tokens: dict[str, str]) -> str | None:
    """Resolve one template variable to a color value, or None if unknown."""
    if key == "theme_type":
        return TOKEN_MAPPING["mode"]
    if key == "selection_background":
        return _resolve_color(TOKEN_MAPPING["selection"], tokens)
    if key == "selection_foreground":
        return _resolve_color(TOKEN_MAPPING["bright_foreground"], tokens)
    if key in TOKEN_MAPPING:
        return _resolve_color(TOKEN_MAPPING[key], tokens)
    return None


def generate_vscode_theme(
    tokens: dict[str, str], template_path: Path | None = None
) -> str:
    """Render the VS Code color theme JSON from parsed tokens.

    Substitutes ``{{ key }}`` placeholders in the committed template.
    Raises ValueError if a required token is missing or a placeholder
    is left unsubstituted.
    """
    template = (template_path or VSCODE_TEMPLATE).read_text(encoding="utf-8")

    def repl(m: re.Match[str]) -> str:
        value = _vscode_value_for(m.group(1).strip(), tokens)
        return m.group(0) if value is None else value

    result = re.sub(r"\{\{\s*(\w+)\s*\}\}", repl, template)
    if re.search(r"\{\{.*?\}\}", result):
        raise ValueError(
            "Unsubstituted placeholders remain in the VS Code theme "
            f"(template: {template_path or VSCODE_TEMPLATE})"
        )
    return result
```

Also update the module docstring: change the line

```
 quattro theme format, and writes ``colors.toml``, ``keyboard.rgb``, and
 ``shell.lock.toml``.
```

to

```
 quarto theme format, and writes ``colors.toml``, ``keyboard.rgb``,
 ``shell.lock.toml``, and the VS Code color theme
 (``vscode/themes/robominds-color-theme.json``).
```

- [ ] **Step 5: Wire generation into `main()`**

In `scripts/update_theme.py` `main()`, after the `write_file(generate_keyboard_rgb(...), ...)` block (ending line 308) and before `print("\nDone! ...")`, add:

```python
    write_file(
        generate_vscode_theme(tokens),
        base_dir / "vscode" / "themes" / "robominds-color-theme.json",
        "vscode theme",
    )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -v`

Expected: `Ran 5 tests ... OK`.

- [ ] **Step 7: Run the full generator offline and verify output**

Run (from repo root):

```bash
python3 scripts/update_theme.py --tokens tests/fixtures/tokens.css
```

Expected: four `✓ Generated` lines (colors, shell lock, keyboard RGB, vscode theme). Then verify:

```bash
git status --short
git diff --stat
python3 -m json.tool vscode/themes/robominds-color-theme.json > /dev/null && echo "JSON OK"
grep -c '{{' vscode/themes/robominds-color-theme.json || echo "no placeholders"
```

Expected: `git status` shows only the new untracked file `vscode/themes/robominds-color-theme.json` (the fixture + tests are also new); `git diff` is empty (the regenerated `colors.toml`, `shell.lock.toml`, `keyboard.rgb` are byte-identical to the committed ones); `JSON OK`; `no placeholders`.

- [ ] **Step 8: Verify vsce packaging and template exclusion**

Run:

```bash
cd vscode && npx -y @vscode/vsce package --no-dependencies
unzip -l robominds-0.1.0.vsix | grep -E 'extension/'
rm robominds-0.1.0.vsix
```

Expected: `DONE  Packaged: .../robominds-0.1.0.vsix`; the `extension/` listing contains `package.json`, `readme.md`, `LICENSE.txt`, and `themes/robominds-color-theme.json` — and does NOT contain `robominds-color-theme.json.tpl`.

- [ ] **Step 9: Commit**

```bash
git add tests/ scripts/update_theme.py vscode/themes/robominds-color-theme.json
git commit -m "Generate VS Code color theme from style guide tokens"
```

---

### Task 3: `vscode.json`, Makefile, README

**Files:**
- Modify: `vscode.json` (replace the Kanagawa placeholder)
- Create: `Makefile` (repo root)
- Modify: `README.md` (add VS Code section)

**Interfaces:**
- Consumes: `scripts/update_theme.py` CLI (`--tokens`/`--url`, unchanged), `vscode/package.json` version, `code` CLI, `npx @vscode/vsce`.
- Produces: `make update`, `make package-vscode`, `make test-vscode`, `make apply-vscode-theme`, `make untest-vscode`, `make vscode-login`, `make publish-vscode`; omarchy descriptor `vscode.json` = `{"name": "robominds", "extension": "robominds.robominds"}`.

- [ ] **Step 1: Update `vscode.json`**

Replace the entire content of `vscode.json` (currently `{"name": "Kanagawa", "extension": "qufiwefefwoyn.kanagawa"}`) with:

```json
{
  "name": "robominds",
  "extension": "robominds.robominds"
}
```

- [ ] **Step 2: Create the Makefile**

Write `Makefile`:

```makefile
STYLEGUIDE_URL  ?= https://brand.robominds.de
TOKENS          ?=
PUBLISHER       ?= robominds
VSCODE_SETTINGS ?= $(HOME)/.config/Code/User/settings.json

.PHONY: update package-vscode vscode-login test-vscode apply-vscode-theme untest-vscode publish-vscode

update:
ifeq ($(TOKENS),)
	python3 scripts/update_theme.py --url $(STYLEGUIDE_URL)
else
	python3 scripts/update_theme.py --tokens $(TOKENS)
endif

package-vscode:
	cd vscode && npx -y @vscode/vsce package --no-dependencies

vscode-login:
	cd vscode && npx -y @vscode/vsce login $(PUBLISHER)

test-vscode: package-vscode
	code --install-extension $(shell find vscode -maxdepth 1 -name '*.vsix' | head -n1) --force
	$(MAKE) -s apply-vscode-theme

apply-vscode-theme:
	mkdir -p $(dir $(VSCODE_SETTINGS))
	@test -f $(VSCODE_SETTINGS) || printf '{\n}\n' > $(VSCODE_SETTINGS)
	@! grep -q '"workbench.colorTheme"' $(VSCODE_SETTINGS) || \
		sed -i --follow-symlinks -E '0,/\{/{s/\{/{\ "workbench.colorTheme": "",/}' $(VSCODE_SETTINGS)
	sed -i --follow-symlinks -E 's|("workbench.colorTheme"[[:space:]]*:[[:space:]]*")[^"]*(")|\1robominds\2|' $(VSCODE_SETTINGS)
	@echo "VS Code theme set to robominds in $(VSCODE_SETTINGS)"

untest-vscode:
	sed -i --follow-symlinks -E 's/"workbench\.colorTheme"[[:space:]]*:[^,}]*,?//' $(VSCODE_SETTINGS)
	@echo "Removed workbench.colorTheme from $(VSCODE_SETTINGS)"

publish-vscode:
	cd vscode && npx -y @vscode/vsce publish
```

Notes on two deliberate deviations from the design spec, both verified against this machine's tooling:
- `test-vscode` packages a `.vsix` first, because `code --install-extension` rejects source-folder paths.
- `--force` comes after the `.vsix` path; in this VS Code CLI version placing it before the path makes the CLI consume it as the `--install-extension` argument and the install silently fails.

- [ ] **Step 3: Document the workflow in `README.md`**

The current `README.md` has sections: `# omarchy-robominds-theme`, `## Update the theme`, `## Color mapping`, `## Theme files`, `## License`.

In `## Update the theme`, after the existing `python scripts/update_theme.py --url https://brand.robominds.de` example block, add:

```markdown
Or, from the repository root:

    make update                          # fetches from the live style guide
    make update TOKENS=path/to/tokens.css  # or from a local tokens.css
```

Insert a new `## VS Code theme` section between `## Update the theme` and `## Color mapping`:

```markdown
## VS Code theme

The same tokens generate a VS Code color theme extension
(`robominds.robominds`). The rendered theme is checked in at
`vscode/themes/robominds-color-theme.json`; the template
(`.tpl`), `package.json`, `LICENSE`, and `README.md` under `vscode/`
are static and packed by `vsce` (the `.tpl` is excluded from the
`.vsix`).

    make test-vscode      # package + install locally, apply to your VS Code
    make untest-vscode    # remove the local workbench.colorTheme override
    make vscode-login     # one-time vsce login (marketplace PAT)
    make publish-vscode   # publish to the VS Code Marketplace

Publish workflow: `make update` → review the diff → `make test-vscode`
→ bump `version` in `vscode/package.json` → `make vscode-login`
(first time only) → `make publish-vscode` → `omarchy theme set robominds`.
```

In `## Theme files`, add one line to the file table (if it is a table) or as a bullet: `vscode/` — VS Code theme extension (generated theme + static packaging files).

- [ ] **Step 4: Verify regeneration is a no-op and the Makefile works offline**

Run:

```bash
make update TOKENS=tests/fixtures/tokens.css
git status --short
```

Expected: four `✓ Generated` lines; `git status --short` shows nothing new or modified (all regenerated files are byte-identical).

- [ ] **Step 5: Verify `make test-vscode` end-to-end**

Run:

```bash
make test-vscode
code --list-extensions | grep robominds
grep workbench.colorTheme "$HOME/.config/Code/User/settings.json"
```

Expected: vsce `DONE  Packaged: .../robominds-0.1.0.vsix`; `Extension 'robominds.robominds' was successfully installed` (or "updated"); `code --list-extensions` lists `robominds.robominds`; `settings.json` contains `"workbench.colorTheme": "robominds"`. Open VS Code and visually confirm: editor + UI chrome use the robominds palette, and Python + Markdown files get syntax colors. (If the user's `settings.json` did not exist before, it is created with the theme entry.)

- [ ] **Step 6: Verify `make untest-vscode`**

Run:

```bash
make untest-vscode
grep workbench.colorTheme "$HOME/.config/Code/User/settings.json" || echo "removed"
```

Expected: `removed` (the line is gone; a stray trailing comma may remain, which is valid JSONC and matches omarchy's own sed behavior).

- [ ] **Step 7: Clean up the local `.vsix`**

Run:

```bash
rm -f vscode/*.vsix
git status --short
```

Expected: clean tree (the `.vsix` is gitignored anyway; removal keeps the working tree tidy).

- [ ] **Step 8: Commit**

```bash
git add vscode.json Makefile README.md
git commit -m "Add vscode.json descriptor, Makefile, and VS Code workflow docs"
```

---

## Final verification (after all tasks)

Run the full check suite; all must pass:

```bash
python3 -m unittest discover -s tests -v          # 5 tests OK
python3 scripts/update_theme.py --tokens tests/fixtures/tokens.css && git diff --exit-code   # regeneration is a no-op
python3 -m json.tool vscode/themes/robominds-color-theme.json > /dev/null && echo JSON_OK
grep -c '{{' vscode/themes/robominds-color-theme.json || echo NO_PLACEHOLDERS
```

Marketplace publish itself (`make vscode-login`, `make publish-vscode`) requires a real `robominds` publisher account and PAT — it is intentionally manual per the spec and is NOT executed by this plan. After a future publish, verify on a machine without the extension: `omarchy theme set robominds` must install `robominds.robominds` and write `"workbench.colorTheme": "robominds"` to `~/.config/Code/User/settings.json`.
