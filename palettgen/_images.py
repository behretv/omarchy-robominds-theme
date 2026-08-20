"""Palette strip image generation — imported by the CLI and the standalone script."""

from __future__ import annotations

import re
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]
    ImageFont = None  # type: ignore[assignment]

# ANSI color role labels — two rows: dark (color0-7) and bright (color8-15)
ANSI_ROLES = [
    ("color0", "bg"),      # dark row
    ("color1", "red"),
    ("color2", "green"),
    ("color3", "yellow"),
    ("color4", "blue"),
    ("color5", "purple"),
    ("color6", "aqua"),
    ("color7", "gray"),
    ("color8", "gray"),    # bright row
    ("color9", "red"),
    ("color10", "green"),
    ("color11", "yellow"),
    ("color12", "blue"),
    ("color13", "purple"),
    ("color14", "aqua"),
    ("color15", "fg"),
]


def _require_pillow() -> None:
    if Image is None:
        raise ImportError(
            "Pillow is required for image generation. Install with: pip install Pillow"
        )


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


def generate_palette_strip(
    palette: dict[str, str], output_path: Path, mode: str
) -> None:
    """Generate a palette strip image.

    Creates an image with the 16 ANSI colors arranged in two rows:
    the first row holds the dark/normal colors (color0-color7) and the
    second row holds the light/bright colors (color8-color15). Each
    square is labeled with the color name and hex value.
    """
    _require_pillow()

    # Image dimensions
    square_size = 80
    padding = 10
    label_height = 40
    per_row = len(ANSI_ROLES) // 2  # 8 colors per row
    rows = 2
    total_width = per_row * square_size + (per_row + 1) * padding
    total_height = rows * (square_size + label_height) + (rows + 1) * padding

    # Create image with mode-appropriate background
    if mode == "dark":
        bg_color = (30, 30, 30)  # Dark gray background
        text_color = (255, 255, 255)  # White text
    else:
        bg_color = (245, 245, 245)  # Light gray background
        text_color = (0, 0, 0)  # Black text

    img = Image.new("RGB", (total_width, total_height), bg_color)
    draw = ImageDraw.Draw(img)

    # Try to use a monospace font for better readability
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14
        )
        small_font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11
        )
    except (IOError, OSError):
        font = ImageFont.load_default()
        small_font = font

    for i, (key, label) in enumerate(ANSI_ROLES):
        if key not in palette:
            continue

        hex_val = palette[key]
        r, g, b = hex_to_rgb(hex_val)
        color = (r, g, b)

        row = i // per_row
        col = i % per_row
        x_offset = padding + col * (square_size + padding)
        y_offset = padding + row * (square_size + label_height + padding)

        # Draw color square
        x1 = x_offset
        y1 = y_offset
        x2 = x_offset + square_size
        y2 = y_offset + square_size
        draw.rectangle([x1, y1, x2, y2], fill=color, outline=(128, 128, 128), width=2)

        # Draw label below
        label_text = f"{key}\n{hex_val}"
        # Center the text
        bbox = draw.textbbox((0, 0), label_text, font=small_font)
        text_width = bbox[2] - bbox[0]
        text_x = x_offset + (square_size - text_width) // 2
        text_y = y2 + 5

        draw.text((text_x, text_y), label_text, fill=text_color, font=small_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)
    print(f"Generated {output_path} ({total_width}x{total_height}px, {mode} mode)")


def update_readme_with_images(
    readme_path: Path, dark_image_path: Path, light_image_path: Path
) -> None:
    """Update README.md to include palette strip images."""

    readme_text = readme_path.read_text()

    # Check if images section already exists
    if "## Palette" in readme_text:
        # Replace existing palette section
        pattern = re.compile(r"(## Palette.*?)(?=\n## )", re.DOTALL)

        def replacer(m):
            return (
                "## Palette\n\n"
                "### Dark mode\n\n"
                f"![Palette Dark]({dark_image_path.as_posix()})\n\n"
                "### Light mode\n\n"
                f"![Palette Light]({light_image_path.as_posix()})\n\n"
            )

        new_text, count = pattern.subn(replacer, readme_text, count=1)

        if count == 0:
            print(
                "WARNING: Could not find existing ## Palette section",
                file=__import__("sys").stderr,
            )
            # Append palette section at the end
            new_text = (
                readme_text.rstrip()
                + "\n\n## Palette\n\n### Dark mode\n\n![Palette Dark]("
                + dark_image_path.as_posix()
                + ")\n\n### Light mode\n\n![Palette Light]("
                + light_image_path.as_posix()
                + ")\n"
            )
    else:
        # Insert palette section before Algorithm section
        pattern = re.compile(r"(## Algorithm)", re.MULTILINE)

        def replacer(m):
            return (
                "## Palette\n\n"
                "### Dark mode\n\n"
                f"![Palette Dark]({dark_image_path.as_posix()})\n\n"
                "### Light mode\n\n"
                f"![Palette Light]({light_image_path.as_posix()})\n\n"
                r"\1"
            )

        new_text, count = pattern.subn(replacer, readme_text, count=1)

        if count == 0:
            raise RuntimeError(
                "Could not find ## Algorithm section to insert palette before"
            )

    readme_path.write_text(new_text)
    print(f"Updated {readme_path} with palette images")


def generate_images(
    dark_toml: Path,
    light_toml: Path,
    images_dir: Path,
    readme_path: Path,
) -> None:
    """Generate dark + light palette images and update the README.

    Args:
        dark_toml: Path to the dark mode colors.toml.
        light_toml: Path to the light mode colors.toml.
        images_dir: Directory where palette PNGs are saved.
        readme_path: Path to README.md to update with image references.
    """
    _require_pillow()

    images_dir.mkdir(parents=True, exist_ok=True)

    dark_palette = parse_toml_simple(dark_toml)
    if not dark_palette:
        raise ValueError(f"Could not parse {dark_toml}")

    light_palette = parse_toml_simple(light_toml)
    if not light_palette:
        raise ValueError(f"Could not parse {light_toml}")

    dark_image_path = images_dir / "palette-dark.png"
    light_image_path = images_dir / "palette-light.png"

    generate_palette_strip(dark_palette, dark_image_path, "dark")
    generate_palette_strip(light_palette, light_image_path, "light")
    update_readme_with_images(readme_path, dark_image_path, light_image_path)
