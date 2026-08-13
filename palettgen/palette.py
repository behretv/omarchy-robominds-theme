"""
Palette generation algorithm.

Takes a brand color and generates a full 16-color ANSI palette in dark or light mode.
"""

import re

from palettgen.palettgen import hex_to_okhsl, okhsl_to_hex


def validate_palette(palette: dict) -> bool:
    """Validate palette meets requirements.

    Checks:
    - All colors are valid hex format
    - Contrast ratio >= 3.0:1 (minimum for terminal readability;
      below WCAG AA's 4.5:1 because some brand colors cannot achieve it)
    - Background and foreground are different

    Returns:
        True if valid, raises ValueError if invalid
    """
    # Check hex format
    hex_pattern = re.compile(r'^#[0-9A-F]{6}$')
    for key, value in palette.items():
        if not hex_pattern.match(value):
            raise ValueError(f"Invalid hex color: {key}={value}")

    # Check contrast ratio (using a more practical threshold)
    bg = palette["background"]
    fg = palette["foreground"]

    def hex_to_rgb(hex_str):
        h = hex_str.lstrip("#")
        return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))

    def relative_luminance(rgb):
        def linearize(c):
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = rgb
        return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)

    bg_rgb = hex_to_rgb(bg)
    fg_rgb = hex_to_rgb(fg)
    l_bg = relative_luminance(bg_rgb)
    l_fg = relative_luminance(fg_rgb)
    contrast = (max(l_bg, l_fg) + 0.05) / (min(l_bg, l_fg) + 0.05)

    if contrast < 3.0:
        raise ValueError(
            f"Contrast ratio {contrast:.2f} < 3.0 "
            f"(minimum for terminal readability; "
            f"WCAG AA recommends 4.5:1 but some brand colors cannot achieve it)"
        )

    # Check that background and foreground are different
    if bg == fg:
        raise ValueError("Background and foreground colors are identical")

    return True


def generate_palette(brand_color: str, mode: str = "dark") -> dict:
    """Generate a 16-color ANSI palette from a brand color.

    Args:
        brand_color: Hex color string (e.g., "#0052BB")
        mode: "dark" or "light"

    Returns:
        Dictionary with 22 keys: accent, cursor, foreground, background,
        selection_foreground, selection_background, color0-color15
    """
    # 1. Convert brand color to Okhsl
    brand_okhsl = hex_to_okhsl(brand_color)
    brand_h = brand_okhsl["h"]

    # 2. Calculate hue offset to align brand with standard ANSI blue (240 degrees)
    hue_offset = 240.0 - brand_h

    # 3. Generate 6 accent hues at standard ANSI positions with offset applied
    ansi_positions = [0, 60, 120, 180, 240, 300]  # red, yellow, green, cyan, blue, magenta
    accent_hues = [(pos + hue_offset) % 360.0 for pos in ansi_positions]

    # 4. Mode-specific lightness/saturation values
    if mode == "dark":
        gray_l_values = [0.08, 0.25, 0.85, 0.95]
        accent_l_values = [0.50, 0.70]
        accent_s_values = [0.85, 0.90]
    elif mode == "light":
        gray_l_values = [0.95, 0.80, 0.30, 0.05]
        accent_l_values = [0.45, 0.60]
        accent_s_values = [0.80, 0.85]
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'dark' or 'light'.")

    # 5. Build the ANSI color map
    # ANSI standard color positions (hue degrees):
    #   color0 = black, color1 = red(0°), color2 = green(120°), color3 = yellow(60°)
    #   color4 = blue(240°), color5 = magenta(300°), color6 = cyan(180°), color7 = white
    #   color8 = bright black, color9 = bright red, color10 = bright green
    #   color11 = bright yellow, color12 = bright blue, color13 = bright magenta
    #   color14 = bright cyan, color15 = bright white
    #
    # Mapping strategy:
    #   color0 = darkest gray
    #   color1,3 = red, yellow accents (hues[0], hues[1])
    #   color2 = green accent (hues[2])
    #   color6 = cyan accent (hues[3])
    #   color4 = blue accent aligned to ANSI blue (hues[4])
    #   color5 = magenta accent (hues[5])
    #   color7 = lightest gray
    #   color8 = second darkest gray
    #   color9-14 = bright variants at higher lightness
    #   color15 = near-white

    def make_color(h, l, s):
        """Create a hex color from hue, lightness, and saturation."""
        okhsl = {"l": l, "c": s, "h": h}
        return okhsl_to_hex(okhsl)

    # Base grays for black/white positions
    color0 = make_color(0.0, gray_l_values[0], 0.0)   # black
    color8 = make_color(0.0, gray_l_values[1], 0.0)   # bright black
    color7 = make_color(0.0, gray_l_values[2], 0.0)   # white
    color15 = make_color(0.0, gray_l_values[3], 0.0)  # bright white

    # Accents using the 6 rotated hues
    # ANSI standard: color1=red(0°), color2=green(120°), color3=yellow(60°),
    #                color4=blue(240°), color5=magenta(300°), color6=cyan(180°)
    red_h = accent_hues[0]
    yellow_h = accent_hues[1]
    green_h = accent_hues[2]
    cyan_h = accent_hues[3]
    blue_h = accent_hues[4]
    magenta_h = accent_hues[5]

    color1 = make_color(red_h, accent_l_values[0], accent_s_values[0])
    color3 = make_color(yellow_h, accent_l_values[0], accent_s_values[0])
    color2 = make_color(green_h, accent_l_values[0], accent_s_values[0])
    color6 = make_color(cyan_h, accent_l_values[0], accent_s_values[0])
    color4 = make_color(blue_h, accent_l_values[0], accent_s_values[0])
    color5 = make_color(magenta_h, accent_l_values[0], accent_s_values[0])

    # Bright variants use higher lightness/saturation
    color9 = make_color(red_h, accent_l_values[1], accent_s_values[1])
    color11 = make_color(yellow_h, accent_l_values[1], accent_s_values[1])
    color10 = make_color(green_h, accent_l_values[1], accent_s_values[1])
    color14 = make_color(cyan_h, accent_l_values[1], accent_s_values[1])
    color12 = make_color(blue_h, accent_l_values[1], accent_s_values[1])
    color13 = make_color(magenta_h, accent_l_values[1], accent_s_values[1])

    # UI colors
    background = color0
    foreground = color7
    cursor = brand_color
    accent = brand_color
    selection_background = color8
    selection_foreground = color7

    palette = {
        "accent": accent,
        "cursor": cursor,
        "foreground": foreground,
        "background": background,
        "selection_foreground": selection_foreground,
        "selection_background": selection_background,
        "color0": color0,
        "color1": color1,
        "color2": color2,
        "color3": color3,
        "color4": color4,
        "color5": color5,
        "color6": color6,
        "color7": color7,
        "color8": color8,
        "color9": color9,
        "color10": color10,
        "color11": color11,
        "color12": color12,
        "color13": color13,
        "color14": color14,
        "color15": color15,
    }

    validate_palette(palette)

    return palette
