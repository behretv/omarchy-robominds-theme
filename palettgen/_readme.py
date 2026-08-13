"""README swatch-table updater — imported by the CLI after palette generation."""

from __future__ import annotations

import re
import urllib.parse
from pathlib import Path

# ANSI color role labels — kept in sync with the order in palette.py
_ANSI_ROLES = [
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

_README_PATTERN = re.compile(
    r"(## Output Format\n.*?)(?=\n## )",
    re.DOTALL,
)


def _parse_toml(path: Path) -> dict[str, str]:
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


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_ansi_fg(r: int, g: int, b: int) -> str:
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#000000" if luminance > 128 else "#FFFFFF"


def _build_swatch_table(palette: dict[str, str]) -> str:
    lines: list[str] = []
    lines.append("| Name | Hex | Swatch | Conventional Role |")
    lines.append("|------|-----|--------|-------------------|")

    for key, label in _ANSI_ROLES:
        if key not in palette:
            continue
        hex_val = palette[key]
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12">'
            f'<rect width="12" height="12" fill="{hex_val}"/></svg>'
        )
        encoded = urllib.parse.quote(svg)
        img_url = f"data:image/svg+xml,{encoded}"
        lines.append(
            f"| `{key}` | `{hex_val}` "
            f'| ![{hex_val}]({img_url}) '
            f"| {label} |"
        )

    return "\n".join(lines)


def update_readme(readme_path: Path, toml_path: Path) -> None:
    """Replace the TOML code block in README.md with a swatch table."""
    readme_text = readme_path.read_text()
    palette = _parse_toml(toml_path)

    if not palette:
        raise ValueError(f"Could not parse {toml_path}")

    table = _build_swatch_table(palette)

    HEADER = "## Output Format\n\nGenerates a `colors.toml` file with 22 color keys:\n\nGenerated palette swatches (auto-generated — do not edit by hand):\n\n"

    def _replacer(m: re.Match) -> str:
        return HEADER + table + "\n"

    new_text, count = _README_PATTERN.subn(_replacer, readme_text, count=1)

    if count == 0:
        raise ValueError(
            f"Could not find '## Output Format' section in {readme_path}"
        )

    readme_path.write_text(new_text)
