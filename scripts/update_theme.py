#!/usr/bin/env python3
"""Extract the robominds color scheme from the style guide and update the theme.

Reads CSS design tokens (the "Single Source of Truth") from either a local
``tokens.css`` file or a live style-guide URL, maps them to the 16-color ANSI
palette + UI colors, writes ``colors.toml`` / ``colors-light.toml``, generates
palette PNG images, and updates ``README.md``.

Usage:
    # From a local style guide folder
    python scripts/update_theme.py --tokens tmp/robominds-styleguide/css/tokens.css

    # From a live style guide URL (fetches tokens.css)
    python scripts/update_theme.py --url https://brand.robominds.de

    # Custom output locations
    python scripts/update_theme.py --tokens ... \
        --output colors.toml --readme README.md --images-dir images
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print(
        "ERROR: Pillow is required. Install with: pip install Pillow",
        file=sys.stderr,
    )
    sys.exit(1)


# ---------------------------------------------------------------------------
# ANSI color role labels — two rows: dark (color0-7) and bright (color8-15)
# ---------------------------------------------------------------------------
ANSI_ROLES = [
    ("color0", "bg"),  # dark row
    ("color1", "red"),
    ("color2", "green"),
    ("color3", "yellow"),
    ("color4", "blue"),
    ("color5", "purple"),
    ("color6", "aqua"),
    ("color7", "gray"),
    ("color8", "gray"),  # bright row
    ("color9", "red"),
    ("color10", "green"),
    ("color11", "yellow"),
    ("color12", "blue"),
    ("color13", "purple"),
    ("color14", "aqua"),
    ("color15", "fg"),
]

# ---------------------------------------------------------------------------
# Mapping from ANSI slots to CSS custom-property names in tokens.css.
# Dark row uses the 700 (dark) variants; bright row uses the 500 (base) variants.
# ---------------------------------------------------------------------------
TOKEN_MAPPING = {
    # UI colors
    "accent": "--rm-blue-700",
    "cursor": "--rm-blue-700",
    # Dark mode
    "dark": {
        "background": "--rm-navy-grey-2",
        "foreground": "--rm-gray-200",
        "selection_background": "--rm-navy-grey-1",
        "selection_foreground": "--rm-gray-200",
        "color0": "--rm-navy-grey-2",  # bg
        "color1": "--rm-red-700",  # red
        "color2": "--rm-green-700",  # green
        "color3": "--rm-yellow-700",  # yellow
        "color4": "--rm-blue-700",  # blue
        "color5": "--rm-violet-700",  # purple
        "color6": "--rm-teal-700",  # aqua
        "color7": "--rm-gray-400",  # gray
        "color8": "--rm-navy-grey-1",  # gray (bright bg)
        "color9": "--rm-red-500",  # red
        "color10": "--rm-green-500",  # green
        "color11": "--rm-yellow-500",  # yellow
        "color12": "--rm-blue-600",  # blue
        "color13": "--rm-violet-500",  # purple
        "color14": "--rm-teal-500",  # aqua
        "color15": "--rm-gray-200",  # fg
    },
    # Light mode
    "light": {
        "background": "--rm-gray-50",
        "foreground": "--rm-midnight",
        "selection_background": "--rm-gray-100",
        "selection_foreground": "--rm-midnight",
        "color0": "--rm-gray-50",  # bg
        "color1": "--rm-red-700",  # red
        "color2": "--rm-green-700",  # green
        "color3": "--rm-yellow-700",  # yellow
        "color4": "--rm-blue-700",  # blue
        "color5": "--rm-violet-700",  # purple
        "color6": "--rm-teal-700",  # aqua
        "color7": "--rm-gray-700",  # gray
        "color8": "--rm-gray-100",  # gray (bright bg)
        "color9": "--rm-red-500",  # red
        "color10": "--rm-green-500",  # green
        "color11": "--rm-yellow-500",  # yellow
        "color12": "--rm-blue-600",  # blue
        "color13": "--rm-violet-500",  # purple
        "color14": "--rm-teal-500",  # aqua
        "color15": "--rm-midnight",  # fg
    },
}


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
                # Resolve relative URL
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
                return css_path.read_text()
    raise ValueError("Could not find tokens.css link in the HTML file")


# ---------------------------------------------------------------------------
# Color scheme generation
# ---------------------------------------------------------------------------
def generate_scheme(tokens: dict[str, str]) -> dict[str, dict[str, str]]:
    """Generate dark and light color schemes from parsed tokens.

    Returns ``{"dark": {...}, "light": {...}}`` where each dict has the
    22 keys: accent, cursor, foreground, background, selection_*,
    color0-color15.
    """
    schemes: dict[str, dict[str, str]] = {}

    for mode in ("dark", "light"):
        mapping = TOKEN_MAPPING[mode]
        scheme: dict[str, str] = {}

        # UI colors
        scheme["accent"] = tokens.get(TOKEN_MAPPING["accent"], "#0052BB")
        scheme["cursor"] = tokens.get(TOKEN_MAPPING["cursor"], "#0052BB")

        for key, token_name in mapping.items():
            if key not in scheme:
                hex_val = tokens.get(token_name)
                if not hex_val:
                    raise ValueError(
                        f"Token {token_name} not found in tokens.css "
                        f"(needed for {mode}.{key})"
                    )
                scheme[key] = hex_val

        schemes[mode] = scheme

    return schemes


def write_toml(scheme: dict[str, str], output: Path, mode: str) -> None:
    """Write a color scheme to a TOML file."""
    with open(output, "w", encoding="utf-8") as f:
        f.write(f"# robominds {mode} theme — extracted from style guide tokens.css\n")
        f.write(f"# Mode: {mode}\n\n")
        f.writelines(f'{key} = "{value}"\n' for key, value in scheme.items())
    print(f"✓ Generated {output} ({mode} mode, {len(scheme)} colors)")


# ---------------------------------------------------------------------------
# Palette image generation
# ---------------------------------------------------------------------------
def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = hex_str.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def generate_palette_image(
    palette: dict[str, str], output_path: Path, mode: str
) -> None:
    """Generate a palette strip image with 16 ANSI colors in two rows."""
    # pylint: disable=too-many-locals
    sq = 80  # square_size
    pad = 10  # padding
    lh = 40  # label_height
    per_row = len(ANSI_ROLES) // 2
    rows = 2
    total_width = per_row * sq + (per_row + 1) * pad
    total_height = rows * (sq + lh) + (rows + 1) * pad

    if mode == "dark":
        bg_color = (30, 30, 30)
        text_color = (255, 255, 255)
    else:
        bg_color = (245, 245, 245)
        text_color = (0, 0, 0)

    img = Image.new("RGB", (total_width, total_height), bg_color)
    draw = ImageDraw.Draw(img)

    try:
        small_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11
        )
    except OSError:
        small_font = ImageFont.load_default()

    for i, (key, _label) in enumerate(ANSI_ROLES):
        if key not in palette:
            continue

        hex_val = palette[key]
        color = _hex_to_rgb(hex_val)
        row = i // per_row
        col = i % per_row
        x = pad + col * (sq + pad)
        y = pad + row * (sq + lh + pad)

        draw.rectangle(
            [x, y, x + sq, y + sq],
            fill=color,
            outline=(128, 128, 128),
            width=2,
        )

        label_text = f"{key}\n{hex_val}"
        bbox = draw.textbbox((0, 0), label_text, font=small_font)
        text_x = x + (sq - (bbox[2] - bbox[0])) // 2
        draw.text((text_x, y + sq + 5), label_text, fill=text_color, font=small_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"Generated {output_path} ({total_width}x{total_height}px, {mode} mode)")


# ---------------------------------------------------------------------------
# README update
# ---------------------------------------------------------------------------
def update_readme(readme_path: Path, dark_image: Path, light_image: Path) -> None:
    """Update README.md to include palette strip images."""
    readme_text = readme_path.read_text()

    palette_section = (
        "## Palette\n\n"
        "### Dark mode\n\n"
        f"![Palette Dark]({dark_image.as_posix()})\n\n"
        "### Light mode\n\n"
        f"![Palette Light]({light_image.as_posix()})\n\n"
    )

    if "## Palette" in readme_text:
        pattern = re.compile(r"(## Palette.*?)(?=\n## )", re.DOTALL)
        new_text, count = pattern.subn(lambda m: palette_section, readme_text, count=1)
        if count == 0:
            new_text = readme_text.rstrip() + "\n\n" + palette_section
    else:
        pattern = re.compile(r"(## Algorithm|## Testing|## Limitations)", re.MULTILINE)
        new_text, count = pattern.subn(
            lambda m: palette_section + r"\1", readme_text, count=1
        )
        if count == 0:
            new_text = readme_text.rstrip() + "\n\n" + palette_section

    readme_path.write_text(new_text)
    print(f"✓ Updated {readme_path} with palette images")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    """CLI entry point: parse args, extract tokens, generate theme files."""
    parser = argparse.ArgumentParser(
        description=(
            "Extract the robominds color scheme from the style guide and "
            "update the omarchy theme (TOMLs, palette images, README)."
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
        help="Output path for dark mode TOML (default: colors.toml)",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=Path("README.md"),
        help="Path to README.md (default: README.md)",
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=Path("images"),
        help="Directory for palette PNG images (default: images)",
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

    # 3. Generate color schemes
    schemes = generate_scheme(tokens)

    # 4. Write TOML files
    dark_output = args.output
    light_output = dark_output.with_name(
        dark_output.stem + "-light" + dark_output.suffix
    )
    write_toml(schemes["dark"], dark_output, "dark")
    write_toml(schemes["light"], light_output, "light")

    # 5. Generate palette images
    images_dir = args.images_dir
    images_dir.mkdir(parents=True, exist_ok=True)
    dark_image = images_dir / "palette-dark.png"
    light_image = images_dir / "palette-light.png"
    generate_palette_image(schemes["dark"], dark_image, "dark")
    generate_palette_image(schemes["light"], light_image, "light")

    # 6. Update README
    if args.readme.is_file():
        update_readme(args.readme, dark_image, light_image)
    else:
        print(f"Warning: {args.readme} not found, skipping README update")

    print("\nDone! Theme updated from style guide.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
