"""
palettgen - Okhsl-based Terminal Color Palette Generator

Core color conversion functions between hex strings and Okhsl color space.
Conversion chain: hex <-> RGB <-> XYZ <-> Lab <-> OKLab <-> OKLCh <-> Okhsl
"""

import math

# --- hex <-> RGB ---

def hex_to_rgb(hex_str: str) -> tuple[float, float, float]:
    """Convert hex string '#RRGGBB' to (R, G, B) tuple with values 0-255."""
    h = hex_str.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert (R, G, B) integers 0-255 to uppercase hex string '#RRGGBB'."""
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


# --- RGB <-> XYZ (sRGB -> D65) ---

def rgb_to_xyz(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Convert sRGB (0-255) to CIE XYZ (D65 illuminant)."""
    # Linearise sRGB
    def linearise(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    rl, gl, bl = linearise(r), linearise(g), linearise(b)

    # sRGB -> XYZ matrix (D65)
    x = 0.4124564 * rl + 0.3575761 * gl + 0.1804375 * bl
    y = 0.2126729 * rl + 0.7151522 * gl + 0.0721750 * bl
    z = 0.0193339 * rl + 0.1191920 * gl + 0.9503041 * bl
    return (x, y, z)


def xyz_to_rgb(x: float, y: float, z: float) -> tuple[int, int, int]:
    """Convert CIE XYZ to sRGB (0-255) integers."""
    # XYZ -> sRGB matrix
    r =  3.2404542 * x - 1.5371385 * y - 0.4985314 * z
    g = -0.9692660 * x + 1.8760108 * y + 0.0415560 * z
    b =  0.0556434 * x - 0.2040259 * y + 1.0572252 * z

    def gamma(c):
        c = max(0.0, min(1.0, c))
        return round(255.0 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1.0 / 2.4) - 0.055))

    return (gamma(r), gamma(g), gamma(b))


# --- XYZ <-> Lab (D65) ---

# D65 reference white
_XN = 0.95047
_YN = 1.00000
_ZN = 1.08883


def _f(t: float) -> float:
    epsilon = 0.008856
    kappa = 903.3
    return t ** (1.0 / 3.0) if t > epsilon else (kappa * t + 16.0) / 116.0


def _f_inv(ft: float) -> float:
    epsilon = 0.008856
    kappa = 903.3
    return (ft ** 3) if ft ** 3 > epsilon else (116.0 * ft - 16.0) / kappa


def xyz_to_lab(x: float, y: float, z: float) -> tuple[float, float, float]:
    """Convert CIE XYZ to CIE Lab (D65)."""
    fx = _f(x / _XN)
    fy = _f(y / _YN)
    fz = _f(z / _ZN)
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return (L, a, b)


def lab_to_xyz(L: float, a: float, b: float) -> tuple[float, float, float]:
    """Convert CIE Lab (D65) to CIE XYZ."""
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0
    x = _XN * _f_inv(fx)
    y = _YN * _f_inv(fy)
    z = _ZN * _f_inv(fz)
    return (x, y, z)


# --- Lab <-> OKLab ---

def lab_to_oklab(L: float, a: float, b: float) -> tuple[float, float, float]:
    """Convert CIE Lab to OKLab using Björn Ottosson's formulas."""
    # Lab -> linear sRGB (via XYZ -> linear sRGB)
    x, y, z = lab_to_xyz(L, a, b)
    rl, gl, bl = xyz_to_rgb(x, y, z)
    rl = rl / 255.0
    gl = gl / 255.0
    bl = bl / 255.0

    # linear sRGB -> LMS
    l =  0.4122214708 * rl + 0.5363325398 * gl + 0.0514459895 * bl
    m =  0.2119034983 * rl + 0.6806995451 * gl + 0.1073969566 * bl
    s =  0.0883024619 * rl + 0.2817188376 * gl + 0.6299787005 * bl

    # cube root
    l_ = l ** (1.0 / 3.0)
    m_ = m ** (1.0 / 3.0)
    s_ = s ** (1.0 / 3.0)

    # LMS -> OKLab matrix
    L_ok =  0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a_ok =  1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b_ok =  0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_

    return (L_ok, a_ok, b_ok)


def oklab_to_lab(L_ok: float, a_ok: float, b_ok: float) -> tuple[float, float, float]:
    """Convert OKLab to CIE Lab (D65) using Björn Ottosson's formulas."""
    # OKLab -> LMS
    l_ =  L_ok + 0.3963377774 * a_ok + 0.2158037573 * b_ok
    m_ =  L_ok - 0.1055613458 * a_ok - 0.0638541728 * b_ok
    s_ =  L_ok - 0.0894841775 * a_ok - 1.2914855480 * b_ok

    # inverse cube root
    l = l_ ** 3
    m = m_ ** 3
    s = s_ ** 3

    # LMS -> linear sRGB
    rl =  4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    gl = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bl = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

    # linear sRGB -> 8-bit RGB
    def clamp(v):
        return max(0, min(255, round(255.0 * max(0.0, min(1.0, v)))))

    r, g, b = clamp(rl), clamp(gl), clamp(bl)

    # RGB -> XYZ -> Lab
    x, y, z = rgb_to_xyz(r, g, b)
    return xyz_to_lab(x, y, z)


# --- OKLab polar (OKLCh) <-> Okhsl ---

def oklab_to_okhsl(L_ok: float, a_ok: float, b_ok: float) -> dict:
    """Convert OKLab to Okhsl-like polar coordinates."""
    C = math.sqrt(a_ok * a_ok + b_ok * b_ok)
    h = math.degrees(math.atan2(b_ok, a_ok))
    if h < 0:
        h += 360.0
    return {"l": L_ok, "c": C, "h": h}


def okhsl_to_oklab(hsl: dict) -> tuple[float, float, float]:
    """Convert Okhsl-like polar coordinates back to OKLab."""
    h_rad = hsl["h"] * math.pi / 180.0
    L = hsl["l"]
    C = hsl["c"]
    a = C * math.cos(h_rad)
    b = C * math.sin(h_rad)
    return (L, a, b)


# --- Public API ---

def hex_to_okhsl(hex_str: str) -> dict:
    """Convert hex color string to Okhsl dict {l, c, h}.

    Chain: hex -> RGB -> XYZ -> Lab -> OKLab -> Okhsl
    """
    r, g, b = hex_to_rgb(hex_str)
    x, y, z = rgb_to_xyz(r, g, b)
    L, a, b_val = xyz_to_lab(x, y, z)
    L_ok, a_ok, b_ok = lab_to_oklab(L, a, b_val)
    return oklab_to_okhsl(L_ok, a_ok, b_ok)


def okhsl_to_hex(okhsl: dict) -> str:
    """Convert Okhsl dict back to uppercase hex string.

    Chain: Okhsl -> OKLab -> Lab -> XYZ -> RGB -> hex
    """
    L_ok, a_ok, b_ok = okhsl_to_oklab(okhsl)
    L, a, b_val = oklab_to_lab(L_ok, a_ok, b_ok)
    x, y, z = lab_to_xyz(L, a, b_val)
    r, g, b = xyz_to_rgb(x, y, z)
    return rgb_to_hex(r, g, b)
