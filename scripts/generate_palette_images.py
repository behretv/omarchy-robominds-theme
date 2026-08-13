#!/usr/bin/env python3
"""Generate palette strip images and update README.md.

Creates horizontal color strip images for dark and light modes,
similar to Gruvbox's palette display. Saves them as PNG files
and updates the README with embedded images.

Usage:
    python scripts/generate_palette_images.py [--brand COLOR] [--mode MODE]
"""

import argparse
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)

# ANSI color role labels
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


def generate_palette_strip(palette: dict[str, str], output_path: Path, mode: str) -> None:
    """Generate a horizontal palette strip image.
    
    Creates a wide image with 16 colored squares, each labeled with
    the color name and hex value.
    """
    # Image dimensions
    square_size = 80
    padding = 10
    label_height = 40
    total_width = len(ANSI_ROLES) * square_size + (len(ANSI_ROLES) + 1) * padding
    total_height = square_size + label_height + padding * 2
    
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
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 11)
    except (IOError, OSError):
        font = ImageFont.load_default()
        small_font = font
    
    x_offset = padding
    
    for i, (key, label) in enumerate(ANSI_ROLES):
        if key not in palette:
            continue
            
        hex_val = palette[key]
        r, g, b = hex_to_rgb(hex_val)
        color = (r, g, b)
        
        # Draw color square
        x1 = x_offset
        y1 = padding
        x2 = x_offset + square_size
        y2 = padding + square_size
        draw.rectangle([x1, y1, x2, y2], fill=color, outline=(128, 128, 128), width=2)
        
        # Draw label below
        label_text = f"{key}\n{hex_val}"
        # Center the text
        bbox = draw.textbbox((0, 0), label_text, font=small_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = x_offset + (square_size - text_width) // 2
        text_y = y2 + 5
        
        draw.text((text_x, text_y), label_text, fill=text_color, font=small_font)
        
        x_offset += square_size + padding
    
    img.save(output_path)
    print(f"Generated {output_path} ({total_width}x{total_height}px, {mode} mode)")


def update_readme_with_images(readme_path: Path, dark_image_path: Path, light_image_path: Path) -> None:
    """Update README.md to include palette strip images."""
    
    readme_text = readme_path.read_text()
    
    # Check if images section already exists
    if "## Palette" in readme_text:
        # Replace existing palette section
        pattern = re.compile(
            r"(## Palette.*?)(?=\n## )",
            re.DOTALL
        )
        
        def replacer(m):
            return (
                "## Palette\n\n"
                "### Dark mode\n\n"
                f"![Palette Dark]({dark_image_path.name})\n\n"
                "### Light mode\n\n"
                f"![Palette Light]({light_image_path.name})\n\n"
            )
        
        new_text, count = pattern.subn(replacer, readme_text, count=1)
        
        if count == 0:
            print("WARNING: Could not find existing ## Palette section", file=sys.stderr)
            # Append palette section at the end
            new_text = readme_text.rstrip() + "\n\n## Palette\n\n### Dark mode\n\n![Palette Dark](" + dark_image_path.name + ")\n\n### Light mode\n\n![Palette Light](" + light_image_path.name + ")\n"
    else:
        # Insert palette section before Algorithm section
        pattern = re.compile(
            r"(## Algorithm)",
            re.MULTILINE
        )
        
        def replacer(m):
            return (
                "## Palette\n\n"
                "### Dark mode\n\n"
                f"![Palette Dark]({dark_image_path.name})\n\n"
                "### Light mode\n\n"
                f"![Palette Light]({light_image_path.name})\n\n"
                r"\1"
            )
        
        new_text, count = pattern.subn(replacer, readme_text, count=1)
        
        if count == 0:
            print("ERROR: Could not find ## Algorithm section to insert palette before", file=sys.stderr)
            sys.exit(1)
    
    readme_path.write_text(new_text)
    print(f"Updated {readme_path} with palette images")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate palette strip images and update README"
    )
    parser.add_argument(
        "--brand",
        type=str,
        default="#0052BB",
        help="Brand color in hex format (default: #0052BB)"
    )
    parser.add_argument(
        "--mode",
        choices=["dark", "light"],
        default="dark",
        help="Color mode (default: dark)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("colors.toml"),
        help="Path to colors.toml (default: colors.toml)"
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=Path("README.md"),
        help="Path to README.md (default: README.md)"
    )
    parser.add_argument(
        "--images-dir",
        type=Path,
        default=Path("images"),
        help="Directory to save images (default: images)"
    )
    
    args = parser.parse_args()
    
    # Parse palette
    if not args.output.is_file():
        print(f"ERROR: {args.output} not found", file=sys.stderr)
        sys.exit(1)
    
    palette = parse_toml_simple(args.output)
    if not palette:
        print(f"ERROR: Could not parse {args.output}", file=sys.stderr)
        sys.exit(1)
    
    # Create images directory
    args.images_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate dark mode palette (always)
    dark_image_path = args.images_dir / "palette-dark.png"
    generate_palette_strip(palette, dark_image_path, "dark")
    
    # Generate light mode palette if different from dark
    if args.mode == "light":
        # Load light mode palette
        light_toml = args.output.with_name(args.output.stem + "-light" + args.output.suffix)
        if light_toml.is_file():
            light_palette = parse_toml_simple(light_toml)
            if light_palette:
                light_image_path = args.images_dir / "palette-light.png"
                generate_palette_strip(light_palette, light_image_path, "light")
                update_readme_with_images(args.readme, dark_image_path, light_image_path)
            else:
                print(f"WARNING: Could not parse {light_toml}", file=sys.stderr)
        else:
            print(f"WARNING: {light_toml} not found, only generating dark mode image", file=sys.stderr)
            # Just update with dark mode image
            readme_text = args.readme.read_text()
            if "## Palette" not in readme_text:
                pattern = re.compile(r"(## Algorithm)", re.MULTILINE)
                def replacer(m):
                    return (
                        "## Palette\n\n"
                        "### Dark mode\n\n"
                        f"![Palette Dark]({dark_image_path.name})\n\n"
                        r"\1"
                    )
                new_text, count = pattern.subn(replacer, readme_text, count=1)
                if count > 0:
                    args.readme.write_text(new_text)
                    print(f"Updated {args.readme} with dark mode palette image")
    else:
        # Just generate dark mode and update README
        readme_text = args.readme.read_text()
        if "## Palette" not in readme_text:
            pattern = re.compile(r"(## Algorithm)", re.MULTILINE)
            def replacer(m):
                return (
                    "## Palette\n\n"
                    "### Dark mode\n\n"
                    f"![Palette Dark]({dark_image_path.name})\n\n"
                    r"\1"
                )
            new_text, count = pattern.subn(replacer, readme_text, count=1)
            if count > 0:
                args.readme.write_text(new_text)
                print(f"Updated {args.readme} with dark mode palette image")
            else:
                print("ERROR: Could not update README", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"README already has Palette section, run with --mode light to add light mode image")


if __name__ == "__main__":
    main()
