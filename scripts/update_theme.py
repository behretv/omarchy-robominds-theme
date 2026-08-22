#!/usr/bin/env python3
"""Extract the robominds color scheme from the style guide and update the theme.

Reads CSS design tokens (the "Single Source of Truth") from either a local
``tokens.css`` file or a live style-guide URL, maps them to the omarchy
quattro theme format, and writes ``colors.toml``, ``keyboard.rgb``,
``shell.lock.toml``, and ``vscode/robominds-color-theme.json``.

With ``--install-vscode`` (or ``-a`` to do everything), also installs the
generated VS Code theme as a local extension into VS Code / VSCodium / Cursor.

Usage:
    # From a local style guide folder
    python scripts/update_theme.py --tokens tmp/robominds-styleguide/css/tokens.css

    # From the live style guide URL
    python scripts/update_theme.py --url https://brand.robominds.de

    # Generate everything and install to VS Code in one command
    python scripts/update_theme.py --tokens ... --install-vscode

    # Custom output location
    python scripts/update_theme.py --tokens ... \
        --output colors.toml
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

# ---------------------------------------------------------------------------
# Token mapping — robominds CSS tokens adapted for a dark theme.
#
# The robominds brand colors were designed for light themes. This mapping
# selects robominds shades that work well on dark backgrounds, using a
# muted, desaturated profile with the following assignments:
# - Background: dark navy (#1D2731)
# - Foreground: light gray (#DBDBDB)
# - Keywords/Storage: magenta/violet
# - Functions: blue
# - Operators: yellow
# - Properties: bright yellow
# - Types/Classes: bright cyan
# - Strings: green
# - Numbers: magenta
# - this/self: bright red
# ---------------------------------------------------------------------------
TOKEN_MAPPING: dict[str, str] = {
    "mode": "dark",
    # UI accents
    "accent": "--rm-blue-400",
    "selection": "--rm-blue-800",
    "muted": "#6B6B6B",  # mix of gray-700 and gray-400 for comment readability
    # Backgrounds — navy-grey family, progressively darker
    "background": "--rm-navy-grey-1",
    "dark_background": "--rm-navy-grey-2",
    "darker_background": "#0A0A0A",
    "lighter_background": "--rm-blue-900",
    # Foregrounds — gray family, progressively brighter
    "foreground": "--rm-gray-300",
    "dark_foreground": "--rm-gray-700",
    "light_foreground": "--rm-gray-400",
    "bright_foreground": "--rm-gray-200",
    # Terminal accent colors — 300/500
    "red": "--rm-red-300",
    "yellow": "--rm-yellow-300",
    "orange": "--rm-orange-500",
    "green": "--rm-green-300",
    "cyan": "--rm-teal-300",
    "blue": "--rm-blue-400",
    "magenta": "--rm-violet-300",
    "brown": "--rm-orange-700",
    # Bright variants — differentiated from normal
    "bright_red": "--rm-red-500",
    "bright_yellow": "--rm-yellow-500",
    "bright_green": "--rm-green-500",
    "bright_cyan": "--rm-teal-500",
    "bright_blue": "--rm-blue-500",
    "bright_magenta": "--rm-magenta-500",
}

# shell.lock.toml uses a subset of colors
SHELL_LOCK_MAPPING: dict[str, str] = {
    "text": "--rm-gray-300",
    "placeholder": "--rm-gray-700",
    "text-error": "--rm-red-500",
    "border": "--rm-gray-700",
    "border-active": "--rm-blue-400",
    "border-error": "--rm-red-500",
}

# keyboard.rgb uses the accent color (hex without #)
KEYBOARD_RGB_TOKEN = "--rm-blue-400"


# ---------------------------------------------------------------------------
# CSS token parsing
# ---------------------------------------------------------------------------
def parse_tokens_css(css_text: str) -> dict[str, str]:
    """Parse a tokens.css file and return a dict of --var-name → hex value.

    Handles ``var(--x)`` references by resolving them recursively.
    """
    raw: dict[str, str] = {}
    var_pattern = re.compile(r"(--rm-[\w-]+)\s*:\s*([^;]+);")
    for m in var_pattern.finditer(css_text):
        name = m.group(1).strip()
        value = m.group(2).strip()
        raw[name] = value

    # Resolve var() references
    resolved: dict[str, str] = {}
    for name, value in raw.items():
        resolved[name] = _resolve_var(value, raw, set())

    # Keep only hex colors
    colors: dict[str, str] = {}
    for name, value in resolved.items():
        v = value.strip()
        if v.startswith("#") and len(v) in (4, 7, 9):
            colors[name] = v.upper() if len(v) == 7 else v
    return colors


def _resolve_var(value: str, raw: dict[str, str], seen: set[str]) -> str:
    """Resolve a ``var(--x)`` reference to its underlying hex value."""
    v = value.strip()
    m = re.match(r"var\(\s*(--rm-[\w-]+)\s*\)", v)
    if m:
        ref = m.group(1)
        if ref in seen:
            return v  # circular reference, return as-is
        if ref in raw:
            return _resolve_var(raw[ref], raw, seen | {ref})
        return v
    return v


# ---------------------------------------------------------------------------
# Style guide source resolution
# ---------------------------------------------------------------------------
class _LinkParser(HTMLParser):
    """Extract <link> stylesheet hrefs from an HTML page."""

    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "link":
            d = dict(attrs)
            if d.get("rel") == "stylesheet" and "href" in d:
                self.hrefs.append(d["href"])


def fetch_tokens_css(source: str) -> str:
    """Fetch the contents of tokens.css from a URL or local path.

    ``source`` can be:
      - A direct URL to a tokens.css file
      - A URL to an HTML page that links to tokens.css
      - A local file path to tokens.css
      - A local file path to an HTML file that links to tokens.css
    """
    if source.startswith(("http://", "https://")):
        return _fetch_tokens_from_url(source)
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"Source not found: {source}")
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".css":
        return text
    if path.suffix in (".html", ".htm"):
        return _find_tokens_css_in_html(text, base_path=path.parent)
    raise ValueError(f"Unsupported file type: {path.suffix}")


def _fetch_tokens_from_url(url: str) -> str:
    """Fetch tokens.css from a URL — either directly or via an HTML page."""
    req = urllib.request.Request(url, headers={"User-Agent": "robominds-theme/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode("utf-8")
        content_type = resp.headers.get("Content-Type", "")

    if "css" in content_type or url.endswith(".css"):
        return content

    # It's an HTML page — find the tokens.css link
    if "html" in content_type or content.strip().startswith("<"):
        parser = _LinkParser()
        parser.feed(content)
        for href in parser.hrefs:
            if "tokens" in href.lower():
                if href.startswith("http"):
                    return _fetch_tokens_from_url(href)
                base = url.rsplit("/", 1)[0]
                return _fetch_tokens_from_url(f"{base}/{href}")
        raise ValueError("Could not find tokens.css link in the HTML page")
    return content


def _find_tokens_css_in_html(html_text: str, base_path: Path) -> str:
    """Find and read tokens.css from <link> tags in an HTML file."""
    parser = _LinkParser()
    parser.feed(html_text)
    for href in parser.hrefs:
        if "tokens" in href.lower():
            css_path = (base_path / href).resolve()
            if css_path.is_file():
                return css_path.read_text(encoding="utf-8")
    raise ValueError("Could not find tokens.css link in the HTML file")


# ---------------------------------------------------------------------------
# Theme file generation
# ---------------------------------------------------------------------------
def _resolve_color(token_name: str, tokens: dict[str, str]) -> str:
    """Resolve a token name to a hex color, raising on failure.

    Direct hex values (starting with ``#``) are returned as-is.
    """
    if token_name.startswith("#"):
        return token_name
    hex_val = tokens.get(token_name)
    if not hex_val:
        raise ValueError(f"Token {token_name} not found in tokens.css")
    return hex_val


def generate_colors_toml(tokens: dict[str, str]) -> str:
    """Generate the contents of colors.toml from parsed tokens.

    Output is grouped with blank line separators:
      mode | UI accents | backgrounds | foregrounds | colors | bright colors
    """
    # Group keys for readable output
    ui_keys = ("accent", "selection", "muted")
    bg_keys = (
        "background",
        "dark_background",
        "darker_background",
        "lighter_background",
    )
    fg_keys = ("foreground", "dark_foreground", "light_foreground", "bright_foreground")
    color_keys = (
        "red",
        "yellow",
        "orange",
        "green",
        "cyan",
        "blue",
        "magenta",
        "brown",
    )
    bright_keys = (
        "bright_red",
        "bright_yellow",
        "bright_green",
        "bright_cyan",
        "bright_blue",
        "bright_magenta",
    )

    lines: list[str] = []

    def emit(key: str) -> None:
        token_name = TOKEN_MAPPING[key]
        if key == "mode":
            lines.append(f'mode = "{token_name}"')
        else:
            lines.append(f'{key} = "{_resolve_color(token_name, tokens)}"')

    # mode
    emit("mode")
    lines.append("")
    # UI accents
    for k in ui_keys:
        emit(k)
    lines.append("")
    # backgrounds
    for k in bg_keys:
        emit(k)
    lines.append("")
    # foregrounds
    for k in fg_keys:
        emit(k)
    lines.append("")
    # terminal colors
    for k in color_keys:
        emit(k)
    lines.append("")
    # bright variants
    for k in bright_keys:
        emit(k)

    return "\n".join(lines) + "\n"


def generate_shell_lock_toml(tokens: dict[str, str]) -> str:
    """Generate the contents of shell.lock.toml from parsed tokens."""
    lines: list[str] = []
    for key, token_name in SHELL_LOCK_MAPPING.items():
        lines.append(f'{key:<17} = "{_resolve_color(token_name, tokens)}"')
    return "\n".join(lines) + "\n"


def generate_keyboard_rgb(tokens: dict[str, str]) -> str:
    """Generate the contents of keyboard.rgb (hex without #)."""
    hex_val = _resolve_color(KEYBOARD_RGB_TOKEN, tokens)
    return hex_val.lstrip("#") + "\n"


# ---------------------------------------------------------------------------
# VS Code theme generation (from omarchy template)
# ---------------------------------------------------------------------------
OMARCHY_TEMPLATE_PATHS = [
    Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy"))
    / "default/themed/vscode-theme.json.tpl",
    Path.home() / ".local/share/omarchy/default/themed/vscode-theme.json.tpl",
]


def _find_omarchy_template() -> Path | None:
    """Locate the omarchy VS Code theme template."""
    return next((p for p in OMARCHY_TEMPLATE_PATHS if p.is_file()), None)


def _parse_colors_toml(toml_text: str) -> dict[str, str]:
    """Parse a simple colors.toml into a key→value dict."""
    colors: dict[str, str] = {}
    for line in toml_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'(\w+)\s*=\s*"([^"]+)"', line)
        if m:
            colors[m.group(1)] = m.group(2)
    return colors


def _resolve_template_colors(colors: dict[str, str]) -> dict[str, str]:
    """Resolve derived/aliased colors that the VS Code template expects.

    Mirrors the alias resolution in omarchy-theme-color so the template gets
    every variable it references.
    """
    resolved = dict(colors)

    # theme_type ← mode
    resolved.setdefault("theme_type", resolved.get("mode", "dark"))

    # selection_background / selection_foreground
    resolved.setdefault(
        "selection_background",
        resolved.get("selection", resolved.get("background", "#000000")),
    )
    resolved.setdefault(
        "selection_foreground",
        resolved.get("bright_foreground", resolved.get("foreground", "#ffffff")),
    )

    # cursor ← bright_foreground
    resolved.setdefault(
        "cursor",
        resolved.get("bright_foreground", resolved.get("foreground", "#ffffff")),
    )

    # orange ← yellow if missing
    resolved.setdefault("orange", resolved.get("yellow", "#ffff00"))

    # brown ← mix(orange, black, 50%) if missing
    if "brown" not in resolved and "orange" in resolved:
        resolved["brown"] = _mix_color(resolved["orange"], "#000000", 0.5)

    # lighter_background / dark_foreground / light_foreground fallbacks
    resolved.setdefault("lighter_background", resolved.get("background", "#000000"))
    resolved.setdefault("dark_foreground", resolved.get("foreground", "#ffffff"))
    resolved.setdefault("light_foreground", resolved.get("foreground", "#ffffff"))

    # muted fallback
    resolved.setdefault(
        "muted", resolved.get("dark_foreground", resolved.get("foreground", "#ffffff"))
    )

    return resolved


def _mix_color(start: str, end: str, amount: float) -> str:
    """Mix two hex colors. amount=0 → start, amount=1 → end."""
    s = start.lstrip("#")
    e = end.lstrip("#")
    r = int(s[0:2], 16)
    g = int(s[2:4], 16)
    b = int(s[4:6], 16)
    er = int(e[0:2], 16)
    eg = int(e[2:4], 16)
    eb = int(e[4:6], 16)
    mr = round(r * (1 - amount) + er * amount)
    mg = round(g * (1 - amount) + eg * amount)
    mb = round(b * (1 - amount) + eb * amount)
    return f"#{mr:02x}{mg:02x}{mb:02x}"


def generate_vscode_theme(colors_toml_text: str) -> str:
    """Render the omarchy VS Code template with robominds colors.

    Reads the omarchy ``vscode-theme.json.tpl`` template, substitutes all
    ``{{ variable }}`` placeholders with values from colors.toml, and replaces
    the theme name with "robominds".
    """
    template_path = _find_omarchy_template()
    if template_path is None:
        raise FileNotFoundError(
            "Could not find omarchy VS Code template. "
            "Ensure omarchy is installed (OMARCHY_PATH or /usr/share/omarchy)."
        )

    template = template_path.read_text(encoding="utf-8")
    colors = _parse_colors_toml(colors_toml_text)
    resolved = _resolve_template_colors(colors)

    # Substitute {{ variable }} placeholders
    def replace_placeholder(m: re.Match) -> str:
        key = m.group(1).strip()
        return resolved.get(key, m.group(0))

    rendered = re.sub(r"\{\{\s*(\w+)\s*\}\}", replace_placeholder, template)

    # -----------------------------------------------------------------------
    # Token color patches
    #
    # The omarchy template assigns colors differently from the desired
    # robominds dark theme. These patches remap token colors:
    #   Keywords/Storage → magenta    Functions → blue
    #   Operators → yellow            Properties → bright_yellow
    #   Types/Classes → bright_cyan   this/self → bright_red
    #   Numbers → magenta             Booleans → orange
    #   Punctuation → blue-gray       Decorators → magenta
    #   Imports → orange              Macros → orange
    # -----------------------------------------------------------------------
    import json as _json

    data = _json.loads(rendered)
    tokens = data.get("tokenColors", [])

    # Color shortcuts from the resolved palette
    fg = resolved.get("foreground", "#DBDBDB")
    muted = resolved.get("muted", "#6B6B6B")
    orange = resolved.get("orange", "#E4761B")
    bright_red = resolved.get("bright_red", "#D32F2F")
    yellow = resolved.get("yellow", "#F4C64D")
    bright_yellow = resolved.get("bright_yellow", "#E8A100")
    green = resolved.get("green", "#6FC08D")
    bright_cyan = resolved.get("bright_cyan", "#12857F")
    blue = resolved.get("blue", "#64B7F7")
    bright_blue = resolved.get("bright_blue", "#2593F4")
    magenta = resolved.get("magenta", "#A98BE0")

    for token in tokens:
        name = token.get("name", "")

        # Punctuation → muted (blue-gray, we use muted for comments)
        if name == "Punctuation":
            token["scope"] = ["punctuation.definition.comment"]
            token["settings"]["foreground"] = muted

        # Keywords → magenta
        if name == "Keyword":
            token["settings"]["foreground"] = magenta
        if name == "Keyword Control":
            token["settings"]["foreground"] = magenta
        if name == "Keyword Import":
            token["settings"]["foreground"] = orange  # imports = orange

        # Operators → yellow
        if name == "Keyword Operator":
            token["settings"]["foreground"] = yellow
        if name == "Operator":
            token["settings"]["foreground"] = yellow

        # Functions → blue
        if name == "Function":
            token["settings"]["foreground"] = blue
        if name == "Function Method":
            token["settings"]["foreground"] = blue
        if name == "Function Builtin":
            token["settings"]["foreground"] = orange  # macros/builtins = orange

        # Function arguments → bright_yellow
        if name == "Variable Parameter":
            token["settings"]["foreground"] = bright_yellow

        # Properties → bright_yellow
        if name == "Variable Property":
            token["settings"]["foreground"] = bright_yellow

        # Numbers → magenta
        if name == "Constant Numeric":
            token["settings"]["foreground"] = magenta

        # Booleans → orange
        if name == "Constant Boolean":
            token["settings"]["foreground"] = orange

        # this/self → bright_red italic
        if name == "This/Self":
            token["settings"]["foreground"] = bright_red
            token["settings"]["fontStyle"] = "italic"

        # Types → bright_cyan
        if name == "Type":
            token["settings"]["foreground"] = bright_cyan
        if name == "Type Builtin":
            token["settings"]["foreground"] = bright_cyan
        if name == "Type Class":
            token["settings"]["foreground"] = bright_cyan
        if name == "Type Interface":
            token["settings"]["foreground"] = bright_cyan
        if name == "Type Enum":
            token["settings"]["foreground"] = bright_cyan

        # Storage modifier → magenta
        if name == "Storage Modifier":
            token["settings"]["foreground"] = magenta

        # Constant builtin (true/false/null) → bright_blue
        if name == "Constant Builtin":
            token["settings"]["foreground"] = bright_blue

        # Decorators → magenta
        if name == "Function Decorator":
            token["settings"]["foreground"] = magenta

        # Namespace → foreground
        if name == "Namespace":
            token["settings"]["foreground"] = fg

        # Tags → bright_yellow
        if name == "Tag":
            token["settings"]["foreground"] = bright_yellow

    # Patch semanticTokenColors to match
    sem = data.get("semanticTokenColors", {})
    if sem:
        sem["keyword"] = magenta
        sem["function"] = blue
        sem["function.defaultLibrary"] = orange
        sem["method"] = blue
        sem["parameter"] = bright_yellow
        sem["parameter.declaration"] = bright_yellow
        sem["property"] = bright_yellow
        sem["property.declaration"] = bright_yellow
        sem["property.readonly"] = bright_yellow
        sem["number"] = magenta
        sem["boolean"] = orange
        sem["type"] = bright_cyan
        sem["type.defaultLibrary"] = bright_cyan
        sem["class"] = bright_cyan
        sem["interface"] = bright_cyan
        sem["enum"] = bright_cyan
        sem["operator"] = yellow
        sem["macro"] = orange
        sem["namespace"] = blue
        # Module-level constants (UPPER_CASE in Python) are already handled
        # via variable.readonly → bright_yellow above.

    # Insert rules that the omarchy template lacks
    # 1. String punctuation (quotes) → green, placed first for priority
    tokens.insert(
        0,
        {
            "name": "String Punctuation",
            "scope": [
                "punctuation.definition.string",
                "punctuation.definition.string.begin",
                "punctuation.definition.string.end",
                "string.quoted punctuation.definition.string",
            ],
            "settings": {"foreground": green},
        },
    )
    # 2. Brackets/braces/parens → blue-gray
    #    Use blue with reduced opacity for the muted blue-gray look
    tokens.insert(
        1,
        {
            "name": "Brackets",
            "scope": ["punctuation.section", "meta.brace", "meta.bracket"],
            "settings": {"foreground": blue + "99"},
        },
    )
    # 3. Separators (; , :) → foreground with transparency
    tokens.insert(
        2,
        {
            "name": "Separators",
            "scope": ["punctuation.separator", "punctuation.terminator"],
            "settings": {"foreground": fg + "b3"},
        },
    )
    # 4. Accessor (.) → yellow (operators = yellow)
    tokens.insert(
        3,
        {
            "name": "Accessor",
            "scope": ["punctuation.accessor"],
            "settings": {"foreground": yellow},
        },
    )

    rendered = _json.dumps(data, indent=4)

    # Rename the theme from "Omarchy" to "robominds"
    rendered = rendered.replace('"name": "Omarchy"', '"name": "robominds"')

    return rendered


# ---------------------------------------------------------------------------
# VS Code extension installation
# ---------------------------------------------------------------------------
EXTENSION_ID = "local.robominds-theme"
EXTENSION_VERSION = "1.0.0"

VSCODE_EXTENSIONS_DIRS = [
    Path.home() / ".vscode/extensions",
    Path.home() / ".vscode-insiders/extensions",
    Path.home() / ".vscode-oss/extensions",
    Path.home() / ".cursor/extensions",
]


def install_vscode_extension(theme_dir: Path) -> None:
    """Install the robominds theme as a local VS Code extension.

    Copies ``vscode/package.json`` and ``vscode/robominds-color-theme.json``
    into each editor's extensions directory and registers the extension in
    ``extensions.json`` (no jq dependency — pure Python).
    """
    theme_json = theme_dir / "vscode" / "robominds-color-theme.json"
    package_json = theme_dir / "vscode" / "package.json"

    if not theme_json.is_file():
        print(
            "⚠ Skipping VS Code install: vscode/robominds-color-theme.json not found",
            file=sys.stderr,
        )
        return
    if not package_json.is_file():
        print(
            "⚠ Skipping VS Code install: vscode/package.json not found", file=sys.stderr
        )
        return

    installed_any = False
    for ext_base in VSCODE_EXTENSIONS_DIRS:
        if not ext_base.is_dir():
            continue
        ext_dir = ext_base / EXTENSION_ID
        _install_into_editor(ext_base, ext_dir, theme_json, package_json)
        print(f"✓ Installed for {ext_dir}")
        installed_any = True

    if not installed_any:
        print("No VS Code / VSCodium / Cursor installation found.", file=sys.stderr)
        return

    print("\nDone! The 'robominds' theme is now available in VS Code.")


def _install_into_editor(
    ext_base: Path,
    ext_dir: Path,
    theme_json: Path,
    package_json: Path,
) -> None:
    """Copy theme files into an editor's extension dir and register it."""
    themes_dir = ext_dir / "themes"
    themes_dir.mkdir(parents=True, exist_ok=True)

    # Copy package.json and theme JSON
    (ext_dir / "package.json").write_text(
        package_json.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (themes_dir / "robominds-color-theme.json").write_text(
        theme_json.read_text(encoding="utf-8"), encoding="utf-8"
    )

    # Register in extensions.json
    extensions_file = ext_base / "extensions.json"
    existing: list[dict] = []
    if extensions_file.is_file():
        try:
            existing = json.loads(extensions_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            existing = []

    # Remove any previous entry for this extension ID
    existing = [
        e for e in existing if e.get("identifier", {}).get("id") != EXTENSION_ID
    ]

    existing.append(
        {
            "identifier": {"id": EXTENSION_ID},
            "version": EXTENSION_VERSION,
            "location": {
                "$mid": 1,
                "fsPath": str(ext_dir),
                "external": f"file://{ext_dir}",
                "path": str(ext_dir),
                "scheme": "file",
            },
            "relativeLocation": ext_dir.name,
        }
    )

    extensions_file.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")

    # Remove from .obsolete if present
    obsolete_file = ext_base / ".obsolete"
    if obsolete_file.is_file():
        try:
            obsolete = json.loads(obsolete_file.read_text(encoding="utf-8"))
            key = f"{EXTENSION_ID}-{EXTENSION_VERSION}"
            obsolete.pop(key, None)
            if obsolete:
                obsolete_file.write_text(
                    json.dumps(obsolete, indent=2) + "\n", encoding="utf-8"
                )
            else:
                obsolete_file.unlink()
        except (json.JSONDecodeError, ValueError):
            pass


def write_file(content: str, output: Path, label: str) -> None:
    """Write content to a file and print a confirmation."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")
    print(f"✓ Generated {output} ({label})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    """CLI entry point: parse args, extract tokens, generate theme files."""
    parser = argparse.ArgumentParser(
        description=(
            "Extract the robominds color scheme from the style guide and "
            "update the omarchy quattro theme files."
        )
    )
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument(
        "--tokens",
        type=Path,
        help="Path to tokens.css (or index.html that links to it)",
    )
    src.add_argument(
        "--url",
        type=str,
        help="URL to the style guide (tokens.css or HTML page)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("colors.toml"),
        help="Output path for colors.toml (default: colors.toml)",
    )
    parser.add_argument(
        "--install-vscode",
        action="store_true",
        help="Install the generated theme as a local VS Code extension",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Generate all theme files and install to VS Code (shorthand for --install-vscode)",
    )

    args = parser.parse_args()

    # 1. Fetch tokens.css
    if args.url:
        print(f"Fetching tokens from {args.url} ...")
        css_text = fetch_tokens_css(args.url)
    else:
        print(f"Reading tokens from {args.tokens} ...")
        css_text = fetch_tokens_css(str(args.tokens))

    # 2. Parse tokens
    tokens = parse_tokens_css(css_text)
    if not tokens:
        print("ERROR: No color tokens found in the source", file=sys.stderr)
        return 1
    print(f"✓ Parsed {len(tokens)} color tokens")

    # 3. Generate theme files
    base_dir = args.output.parent

    colors_toml_content = generate_colors_toml(tokens)

    write_file(
        colors_toml_content,
        args.output,
        "colors",
    )
    write_file(
        generate_shell_lock_toml(tokens),
        base_dir / "shell.lock.toml",
        "shell lock",
    )
    write_file(
        generate_keyboard_rgb(tokens),
        base_dir / "keyboard.rgb",
        "keyboard RGB",
    )

    # 4. Generate VS Code theme from omarchy template
    vscode_generated = False
    try:
        vscode_theme = generate_vscode_theme(colors_toml_content)
        write_file(
            vscode_theme,
            base_dir / "vscode" / "robominds-color-theme.json",
            "VS Code theme",
        )
        vscode_generated = True
    except FileNotFoundError as e:
        print(f"⚠ Skipping VS Code theme: {e}", file=sys.stderr)

    # 5. Install VS Code extension if requested
    if args.install_vscode or args.all:
        if vscode_generated:
            print()
            install_vscode_extension(base_dir)
        else:
            print(
                "⚠ Skipping VS Code install: no vscode/robominds-color-theme.json generated",
                file=sys.stderr,
            )

    print("\nDone! Theme updated from style guide.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
