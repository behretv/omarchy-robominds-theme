#!/usr/bin/env python3
"""Regenerate the palette swatch table in README.md from a colors.toml file.

Usage:
    python scripts/update_readme.py [--toml PATH] [--readme PATH]

Defaults:
    --toml   colors.toml          (relative to project root)
    --readme README.md            (relative to project root)

The script locates the TOML example block in the README (between
"```toml" and "```") and replaces it with a markdown table of colored
swatches. Everything else in the README is left untouched.
"""

import argparse
import re
import sys
from pathlib import Path

# ANSI color role labels — kept in sync with the order in palette.py
ANSI_ROLES = [
    ("color0",  "black"),
    ("color1",  "red"),
    ("color2",  "green"),
    ("color3",  "yellow"),
    ("color4",  "blue"),
    ("color5",  "magenta"),
    ("color6",  "cyan"),
    ("color7",  "white"),
    ("color8",  "bright black"),
    ("color9",  "bright red"),
    ("color10", "bright green"),
    ("color11", "bright yellow"),
    ("color12", "bright blue"),
    ("color13", "bright magenta"),
    ("color14", "bright cyan"),
    ("color15", "bright white"),
]


def parse_toml_simple(path: Path) -> dict[str, str]:
    """Minimal TOML parser — handles ``key = "value"`` lines only."""
    data: dict[str, str] = {}
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"')
        if val:
            data[key] = val
    return data


def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_to_ansi_fg(r: int, g: int, b: int) -> str:
    """Choose black or white for text on top of (r,g,b) background."""
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#000000" if luminance > 128 else "#FFFFFF"


def build_swatch_table(palette: dict[str, str]) -> str:
    """Build the markdown table from a parsed palette dict."""
    lines: list[str] = []
    lines.append("| Name | Hex | Swatch | Conventional Role |")
    lines.append("|------|-----|--------|-------------------|")

    for key, label in ANSI_ROLES:
        if key not in palette:
            continue
        hex_val = palette[key]
        r, g, b = hex_to_rgb(hex_val)
        fg = rgb_to_ansi_fg(r, g, b)
        # Inline image using a data URI so no external assets are needed.
        # 1x1 pixel SVG encoded as data:image/svg+xml.
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12">'
            f'<rect width="12" height="12" fill="{hex_val}"/></svg>'
        )
        import urllib.parse
        encoded = urllib.parse.quote(svg)
        img_url = f"data:image/svg+xml,{encoded}"
        lines.append(
            f"| `{key}` | `{hex_val}` "
            f'| ![{hex_val}]({img_url}) '
            f"| {label} |"
        )

    return "\n".join(lines)


README_PATTERN = re.compile(
    r"(## Output Format\n.*?)(?=\n## )",
    re.DOTALL,
)

_HEADER = (
    "## Output Format\n\n"
    "Generates a `colors.toml` file with 22 color keys:\n\n"
    "Generated palette swatches (auto-generated — do not edit by hand):\n\n"
)


def update_readme(readme_path: Path, toml_path: Path) -> None:
    readme_text = readme_path.read_text()

    palette = parse_toml_simple(toml_path)
    if not palette:
        print(f"ERROR: Could not parse {toml_path}", file=sys.stderr)
        sys.exit(1)

    table = build_swatch_table(palette)

    def replacer(m: re.Match) -> str:
        return _HEADER + table + "\n"

    new_text, count = README_PATTERN.subn(replacer, readme_text, count=1)

    if count == 0:
        print(
            f"ERROR: Could not find '## Output Format' section in {readme_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    readme_path.write_text(new_text)
    print(f"Updated {readme_path} with {len(palette)} palette entries from {toml_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate the palette swatch table in README.md"
    )
    parser.add_argument(
        "--toml",
        type=Path,
        default=Path("colors.toml"),
        help="Path to colors.toml (default: colors.toml)",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=Path("README.md"),
        help="Path to README.md (default: README.md)",
    )
    args = parser.parse_args()

    if not args.toml.is_file():
        print(f"ERROR: {args.toml} not found", file=sys.stderr)
        sys.exit(1)

    update_readme(args.readme, args.toml)


if __name__ == "__main__":
    main()
