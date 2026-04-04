"""Hand-crafted pixel art character templates.

Each template is a 2D grid of color slot IDs. At render time, slots are mapped
to actual colors based on user input (skin, hair, armor, etc.) with automatic
shade ramps. This is how professional pixel art games handle recoloring.

Slot legend:
    0 = transparent
    1 = outline (auto-derived from nearest slot color)
    S0-S4 = skin shades (deep shadow → bright highlight)
    H0-H4 = hair shades
    A0-A4 = armor/body shades
    P0-P4 = pants/secondary shades
    E0-E2 = eye colors
    B0-B2 = boot colors
    X0-X2 = accent colors (belt, trim, cape)
    W  = white highlight
"""

from __future__ import annotations
from typing import Dict, Tuple, List, Optional
from gclub_pixel.canvas import PixelCanvas
from gclub_pixel.palette import Color, color_ramp, shade, colored_outline as derive_outline

# Color slot constants
_ = 0    # transparent
O = 1    # outline (auto)
W = 99   # white highlight

# Skin shades
S0, S1, S2, S3, S4 = 10, 11, 12, 13, 14

# Hair shades
H0, H1, H2, H3, H4 = 20, 21, 22, 23, 24

# Armor shades
A0, A1, A2, A3, A4 = 30, 31, 32, 33, 34

# Pants shades
P0, P1, P2, P3, P4 = 40, 41, 42, 43, 44

# Eye
E0, E1, E2 = 50, 51, 52

# Boot
B0, B1, B2 = 60, 61, 62

# Accent
X0, X1, X2 = 70, 71, 72


# ================================================================
# 32x32 Character Template - Chibi Warrior (hand-crafted)
# ================================================================
# Every single pixel is intentionally placed for maximum readability
# and aesthetic quality at 32x32.

CHIBI_32 = [
    #0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],  # 0
    [_,_,_,_,_,_,_,_,_,_,_,_,H1,H2,H2,H3,H3,H2,H2,H1,_,_,_,_,_,_,_,_,_,_,_,_],  # 1
    [_,_,_,_,_,_,_,_,_,_,H0,H1,H2,H3,H3,H4,H4,H3,H3,H2,H1,H0,_,_,_,_,_,_,_,_,_,_],  # 2
    [_,_,_,_,_,_,_,_,_,H0,H1,H2,H3,H3,H4,H4,H4,H4,H3,H3,H2,H1,H0,_,_,_,_,_,_,_,_,_],  # 3
    [_,_,_,_,_,_,_,_,_,H0,H1,H2,H2,H3,H3,H4,H4,H3,H3,H2,H2,H1,H0,_,_,_,_,_,_,_,_,_],  # 4
    [_,_,_,_,_,_,_,_,_,H0,H1,S3,S4,S3,S3,S3,S3,S3,S3,S4,S3,H1,H0,_,_,_,_,_,_,_,_,_],  # 5
    [_,_,_,_,_,_,_,_,_,H0,S2,S3,S4,S3,S3,S3,S3,S3,S3,S4,S3,S2,H0,_,_,_,_,_,_,_,_,_],  # 6
    [_,_,_,_,_,_,_,_,_,_,S1,S2,S3,W,E1,E0,S2,S2,E0,E1,W,S3,S2,S1,_,_,_,_,_,_,_,_],  # 7  eyes
    [_,_,_,_,_,_,_,_,_,_,S1,S2,S3,S3,E2,E0,S2,S2,E0,E2,S3,S3,S2,S1,_,_,_,_,_,_,_,_],  # 8
    [_,_,_,_,_,_,_,_,_,_,S0,S1,S2,S2,S3,S2,S1,S1,S2,S3,S2,S2,S1,S0,_,_,_,_,_,_,_,_],  # 9  nose
    [_,_,_,_,_,_,_,_,_,_,_,S0,S1,S2,S1,S0,S0,S0,S0,S1,S2,S1,S0,_,_,_,_,_,_,_,_,_],  # 10 mouth
    [_,_,_,_,_,_,_,_,_,_,_,_,S0,S1,S1,S1,S0,S1,S1,S1,S0,_,_,_,_,_,_,_,_,_,_,_],  # 11 chin
    [_,_,_,_,_,_,_,_,_,_,_,_,_,S0,S1,S1,S1,S1,S0,_,_,_,_,_,_,_,_,_,_,_,_,_],  # 12 neck
    [_,_,_,_,_,_,_,_,_,_,A2,A3,A3,A4,A3,A3,A3,A3,A4,A3,A3,A2,_,_,_,_,_,_,_,_,_,_],  # 13 collar
    [_,_,_,_,_,_,_,_,S2,S3,A1,A2,A3,A3,A4,A3,A3,A4,A3,A3,A2,A1,S3,S2,_,_,_,_,_,_,_,_],  # 14 shoulders+arms
    [_,_,_,_,_,_,_,_,S1,S2,A1,A2,A2,A3,A3,A3,A3,A3,A3,A2,A2,A1,S2,S1,_,_,_,_,_,_,_,_],  # 15
    [_,_,_,_,_,_,_,_,S1,S2,A0,A1,A2,A2,A3,A2,A2,A3,A2,A2,A1,A0,S2,S1,_,_,_,_,_,_,_,_],  # 16
    [_,_,_,_,_,_,_,_,S0,S1,A0,A1,A1,A2,A2,A2,A2,A2,A2,A1,A1,A0,S1,S0,_,_,_,_,_,_,_,_],  # 17
    [_,_,_,_,_,_,_,_,_,S0,A0,A1,A1,X1,X2,X1,X1,X2,X1,A1,A1,A0,S0,_,_,_,_,_,_,_,_,_],  # 18 belt
    [_,_,_,_,_,_,_,_,_,_,A0,A1,A1,X0,X1,X2,X2,X1,X0,A1,A1,A0,_,_,_,_,_,_,_,_,_,_],  # 19
    [_,_,_,_,_,_,_,_,_,_,_,P2,P3,P3,P2,P1,P1,P2,P3,P3,P2,_,_,_,_,_,_,_,_,_,_,_],  # 20 pants top
    [_,_,_,_,_,_,_,_,_,_,_,P1,P2,P3,P2,_,_,P2,P3,P2,P1,_,_,_,_,_,_,_,_,_,_,_],  # 21
    [_,_,_,_,_,_,_,_,_,_,_,P1,P2,P2,P1,_,_,P1,P2,P2,P1,_,_,_,_,_,_,_,_,_,_,_],  # 22
    [_,_,_,_,_,_,_,_,_,_,_,P0,P1,P2,P1,_,_,P1,P2,P1,P0,_,_,_,_,_,_,_,_,_,_,_],  # 23
    [_,_,_,_,_,_,_,_,_,_,_,P0,P1,P1,P0,_,_,P0,P1,P1,P0,_,_,_,_,_,_,_,_,_,_,_],  # 24
    [_,_,_,_,_,_,_,_,_,_,B1,B2,B2,B2,B1,_,_,B1,B2,B2,B2,B1,_,_,_,_,_,_,_,_,_,_],  # 25 boots
    [_,_,_,_,_,_,_,_,_,_,B0,B1,B2,B1,B0,_,_,B0,B1,B2,B1,B0,_,_,_,_,_,_,_,_,_,_],  # 26
    [_,_,_,_,_,_,_,_,_,B0,B0,B1,B1,B1,B0,_,_,B0,B1,B1,B1,B0,B0,_,_,_,_,_,_,_,_,_],  # 27
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],  # 28-31 empty
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
]


def _build_slot_map(
    skin: Color, hair: Color, armor: Color, pants: Color,
    eye: Color, boot: Color, accent: Color,
) -> Dict[int, Tuple[int, int, int, int]]:
    """Build color slot → RGBA mapping."""
    sr = color_ramp(skin, 5)
    hr = color_ramp(hair, 5)
    ar = color_ramp(armor, 5)
    pr = color_ramp(pants, 5)
    er = color_ramp(eye, 3)
    br = color_ramp(boot, 3)
    xr = color_ramp(accent, 3)

    m: Dict[int, Tuple[int, int, int, int]] = {0: (0, 0, 0, 0)}

    for i, c in enumerate(sr): m[S0 + i] = (*c, 255)
    for i, c in enumerate(hr): m[H0 + i] = (*c, 255)
    for i, c in enumerate(ar): m[A0 + i] = (*c, 255)
    for i, c in enumerate(pr): m[P0 + i] = (*c, 255)
    for i, c in enumerate(er): m[E0 + i] = (*c, 255)
    for i, c in enumerate(br): m[B0 + i] = (*c, 255)
    for i, c in enumerate(xr): m[X0 + i] = (*c, 255)
    m[W] = (255, 255, 255, 255)
    m[O] = (0, 0, 0, 255)  # will be overridden by colored_outline

    return m


def render_template(
    template: List[List[int]],
    skin: Color = (220, 180, 140),
    hair: Color = (120, 75, 35),
    armor: Color = (100, 110, 150),
    pants: Color = (70, 65, 80),
    eye: Color = (45, 60, 110),
    boot: Color = (65, 50, 35),
    accent: Color = (170, 140, 50),
    use_colored_outline: bool = True,
) -> PixelCanvas:
    """Render a pixel template with custom colors.

    This is the core rendering function. Templates define the shape and
    shading structure, you provide the colors.

    Args:
        template: 2D list of color slot IDs.
        skin: Skin midtone RGB.
        hair: Hair midtone RGB.
        armor: Armor/body midtone RGB.
        pants: Pants midtone RGB.
        eye: Eye midtone RGB.
        boot: Boot midtone RGB.
        accent: Accent (belt/trim) midtone RGB.
        use_colored_outline: Use colored outline instead of black.

    Returns:
        PixelCanvas with rendered character.

    Example:
        >>> from gclub_pixel.templates import CHIBI_32, render_template
        >>> knight = render_template(CHIBI_32, armor=(170, 175, 190), accent=(180, 50, 50))
        >>> knight.save("knight.png", scale=8)
    """
    h = len(template)
    w = len(template[0]) if h > 0 else 0
    c = PixelCanvas(w, h)

    slot_map = _build_slot_map(skin, hair, armor, pants, eye, boot, accent)

    for y in range(h):
        for x in range(w):
            slot = template[y][x] if x < len(template[y]) else 0
            if slot in slot_map:
                c._pixels[y][x] = slot_map[slot]

    if use_colored_outline:
        c.colored_outline()
    return c
