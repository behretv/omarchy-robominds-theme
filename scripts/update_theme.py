#!/usr/bin/env python3
"""Extract the robominds color scheme from the style guide and update the theme.

Reads CSS design tokens (the "Single Source of Truth") from either a local
``tokens.css`` file or a live style-guide URL, maps them to the omarchy
quattro theme format, and writes ``colors.toml``, ``keyboard.rgb``, and
``shell.lock.toml``.

``colors.toml`` is the only file the installed theme needs: omarchy generates
every per-app config (VS Code, Neovim, terminals, ...) from it via templates on
``omarchy theme set``.

Usage:
    # From a local style guide folder
    python scripts/update_theme.py --tokens tmp/robominds-styleguide/css/tokens.css

    # From the live style guide URL
    python scripts/update_theme.py --url https://brand.robominds.de

    # Custom output location
    python scripts/update_theme.py --tokens ... --output colors.toml
"""

from __future__ import annotations

import argparse
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

    print("\nDone! Theme updated from style guide.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
