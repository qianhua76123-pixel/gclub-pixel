"""Professional character generator with hand-tuned pixel-perfect templates.

This module uses carefully designed pixel-by-pixel templates where every
single pixel has been placed to create natural-looking characters with
proper proportions, shading, and detail.

Key design principles (learned from Stardew Valley, Celeste, etc.):
- Head is ~35% of height for chibi, ~25% for normal proportions
- Body width is ~50-60% of total width
- Eyes at 40% of head height from top
- Hair must have highlight strands for volume
- Armor needs at least 3 tone levels + detail pixels
- Legs must taper at knees and ankles
- Feet point slightly outward for stability
- Every edge needs intentional pixel placement for clean silhouette

Example:
    >>> from gclub_pixel.chargen import generate
    >>> knight = generate(body_color=(160,165,180), hair_color=(130,90,40))
    >>> knight.save("knight.png", scale=8)
"""

from __future__ import annotations
from gclub_pixel.canvas import PixelCanvas
from gclub_pixel.palette import Color, color_ramp, shade

# Shorthand for readability
def _s(base: Color, factor: float) -> Color:
    return shade(*base, factor)


def generate(
    skin_color: Color = (225, 190, 150),
    hair_color: Color = (110, 70, 35),
    body_color: Color = (100, 115, 165),
    pants_color: Color = (65, 60, 75),
    boot_color: Color = (70, 55, 35),
    eye_color: Color = (55, 75, 130),
    accent_color: Color = (175, 55, 55),
    size: int = 32,
) -> PixelCanvas:
    """Generate a high-quality character sprite.

    Every pixel is intentionally placed for clean silhouettes and
    natural proportions. Uses 5-shade color ramps with top-left lighting.

    Args:
        skin_color: Skin midtone (will auto-generate 5 shades).
        hair_color: Hair midtone.
        body_color: Armor/shirt midtone.
        pants_color: Pants midtone.
        boot_color: Boot midtone.
        eye_color: Eye iris color.
        accent_color: Belt/trim color.
        size: Output size (32 recommended).

    Returns:
        PixelCanvas with finished character.

    Example:
        >>> knight = generate(body_color=(160, 165, 180))
        >>> knight.save("knight.png", scale=8)
    """
    c = PixelCanvas(size, size)

    # Build 5-shade ramps for every color
    sk = color_ramp(skin_color, 5)   # sk[0]=deep shadow ... sk[4]=highlight
    hr = color_ramp(hair_color, 5)
    bd = color_ramp(body_color, 5)
    pt = color_ramp(pants_color, 5)
    bt = color_ramp(boot_color, 5)
    ac = color_ramp(accent_color, 5)
    ey = color_ramp(eye_color, 3)

    wh = (255, 255, 255)  # pure white for eye highlights

    def p(x, y, color):
        """Set pixel (bounds-checked)."""
        if 0 <= x < size and 0 <= y < size:
            c._pixels[y][x] = (*color, 255)

    # ============================================================
    # HAIR - Row 1-5 (back layer, round top, asymmetric for interest)
    # ============================================================
    #                          row 1: crown tuft
    p(14,1,hr[3]); p(15,1,hr[4]); p(16,1,hr[3]); p(17,1,hr[2])
    #                          row 2: wider
    for x in range(12,20):
        t = abs(x - 15.5) / 4
        p(x, 2, hr[4] if t < 0.3 else hr[3] if t < 0.6 else hr[2])
    #                          row 3: full width + highlight strand
    for x in range(11,21):
        t = abs(x - 15.5) / 5
        p(x, 3, hr[3] if t < 0.4 else hr[2] if t < 0.7 else hr[1])
    p(13, 3, hr[4])  # highlight strand
    #                          row 4: sides frame face
    for x in range(10,22):
        t = abs(x - 15.5) / 6
        p(x, 4, hr[2] if t < 0.5 else hr[1] if t < 0.8 else hr[0])
    p(14, 4, hr[4])  # another highlight
    #                          row 5: hair ends
    p(10,5,hr[1]); p(11,5,hr[1]); p(20,5,hr[0]); p(21,5,hr[0])

    # ============================================================
    # HEAD / FACE - Row 4-11 (oval, not rectangle!)
    # Proportions: 12px wide, 8px tall, centered at x=16
    # ============================================================
    # Row 4-5: forehead (narrower, covered by hair above)

    # Row 5: forehead visible under hair
    for x in range(12, 20):
        t = abs(x - 15.5) / 4
        p(x, 5, sk[4] if t < 0.3 else sk[3])

    # Row 6: upper face (widest part)
    for x in range(11, 21):
        t = abs(x - 15.5) / 5
        p(x, 6, sk[4] if t < 0.2 else sk[3] if t < 0.5 else sk[2] if t < 0.8 else sk[1])

    # Row 7: eye row
    p(11,7,sk[1]); p(12,7,sk[2])
    # Left eye: sclera + iris + pupil + highlight
    p(13,7,wh); p(14,7,ey[1]); p(15,7,ey[0])
    p(16,7,sk[3])  # nose bridge
    # Right eye
    p(17,7,ey[0]); p(18,7,ey[1]); p(19,7,wh)
    p(20,7,sk[2]); p(21,7,sk[1])
    # Eye highlights (critical for life!)
    p(13,6,wh)  # top-left highlight left eye
    p(19,6,wh)  # top-left highlight right eye

    # Row 8: below eyes / nose area
    for x in range(11, 21):
        t = abs(x - 15.5) / 5
        p(x, 8, sk[3] if t < 0.3 else sk[2] if t < 0.6 else sk[1])
    p(16, 8, sk[1])  # subtle nose shadow
    p(15, 8, sk[2])

    # Row 9: mouth area
    for x in range(12, 20):
        t = abs(x - 15.5) / 4
        p(x, 9, sk[2] if t < 0.5 else sk[1])
    p(15, 9, _s(skin_color, 0.55))  # mouth line
    p(16, 9, _s(skin_color, 0.55))
    p(15, 10, _s(skin_color, 0.72))  # lower lip highlight
    p(16, 10, _s(skin_color, 0.72))

    # Row 10: chin (narrow)
    for x in range(12, 20):
        t = abs(x - 15.5) / 4
        if t < 0.8:
            p(x, 10, sk[1] if t < 0.5 else sk[0])

    # Row 11: jaw / chin tip
    for x in range(13, 19):
        p(x, 11, sk[0])

    # ============================================================
    # NECK - Row 12
    # ============================================================
    p(14,12,sk[1]); p(15,12,sk[2]); p(16,12,sk[1]); p(17,12,sk[0])

    # ============================================================
    # BODY / ARMOR - Row 13-20
    # Wider at shoulders, tapers at waist. Cylindrical shading.
    # ============================================================
    # Row 13: collar / neckline (bright highlight)
    for x in range(12, 20):
        p(x, 13, bd[4] if abs(x-15.5) < 2 else bd[3])

    # Row 14: shoulders (widest)
    for x in range(9, 23):
        t = abs(x - 15.5) / 7
        if t < 0.2: col = bd[4]
        elif t < 0.4: col = bd[3]
        elif t < 0.6: col = bd[2]
        elif t < 0.8: col = bd[1]
        else: col = bd[0]
        p(x, 14, col)

    # Row 15-16: upper torso
    for row in (15, 16):
        for x in range(10, 22):
            t = abs(x - 15.5) / 6
            vert = (row - 14) / 6
            if t < 0.15 and vert < 0.3: col = bd[4]
            elif t < 0.3: col = bd[3]
            elif t < 0.55: col = bd[2]
            elif t < 0.8: col = bd[1]
            else: col = bd[0]
            p(x, row, col)

    # Row 17: mid torso with center detail line
    for x in range(10, 22):
        t = abs(x - 15.5) / 6
        col = bd[2] if t < 0.5 else bd[1] if t < 0.8 else bd[0]
        p(x, 17, col)
    p(15, 17, bd[0]); p(16, 17, bd[0])  # center seam

    # Row 18: lower torso
    for x in range(10, 22):
        t = abs(x - 15.5) / 6
        col = bd[2] if t < 0.4 else bd[1] if t < 0.7 else bd[0]
        p(x, 18, col)

    # Row 19: belt
    for x in range(10, 22):
        p(x, 19, ac[1] if abs(x - 15.5) > 3 else ac[2])
    p(15, 19, ac[4])  # buckle bright
    p(16, 19, ac[3])  # buckle

    # Row 20: below belt
    for x in range(11, 21):
        t = abs(x - 15.5) / 5
        col = bd[1] if t < 0.5 else bd[0]
        p(x, 20, col)

    # ============================================================
    # ARMS - Row 14-20 (outside body columns)
    # Left arm = lit, Right arm = shadow
    # ============================================================
    for row in range(14, 20):
        vert = (row - 14) / 6
        # Left arm (lit side)
        if row < 17:  # upper arm = armor
            p(8, row, bd[3]); p(9, row, bd[2])
        else:  # forearm = skin
            p(8, row, sk[3]); p(9, row, sk[2])
        # Right arm (shadow side)
        if row < 17:
            p(22, row, bd[1]); p(23, row, bd[0])
        else:
            p(22, row, sk[1]); p(23, row, sk[0])

    # Hands
    p(8,20,sk[3]); p(9,20,sk[2])   # left hand
    p(22,20,sk[1]); p(23,20,sk[0]) # right hand

    # ============================================================
    # LEGS - Row 21-26 (two separate legs with gap, tapered)
    # ============================================================
    # Row 21: hip (wider)
    for x in range(11, 15):
        p(x, 21, pt[3] if x < 13 else pt[2])
    for x in range(17, 21):
        p(x, 21, pt[2] if x < 19 else pt[1])

    # Row 22-23: thighs
    for row in (22, 23):
        for x in range(11, 15):
            t = abs(x - 12.5) / 2
            p(x, row, pt[3] if t < 0.3 else pt[2] if t < 0.7 else pt[1])
        for x in range(17, 21):
            t = abs(x - 18.5) / 2
            p(x, row, pt[2] if t < 0.3 else pt[1] if t < 0.7 else pt[0])

    # Row 24: knees (slightly narrower)
    for x in range(11, 15):
        p(x, 24, pt[1])
    for x in range(17, 21):
        p(x, 24, pt[0])

    # Row 25: shins
    for x in range(12, 15):
        p(x, 25, pt[2] if x == 12 else pt[1])
    for x in range(17, 20):
        p(x, 25, pt[1] if x == 17 else pt[0])

    # ============================================================
    # BOOTS - Row 26-28
    # ============================================================
    # Row 26: boot top (with highlight line)
    for x in range(11, 16):
        p(x, 26, bt[3] if x < 13 else bt[2])
    for x in range(16, 21):
        p(x, 26, bt[2] if x < 18 else bt[1])

    # Row 27: boot body
    for x in range(11, 16):
        p(x, 27, bt[2] if x < 14 else bt[1])
    for x in range(16, 21):
        p(x, 27, bt[1] if x < 19 else bt[0])

    # Row 28: boot sole (wider, grounded)
    for x in range(10, 16):
        p(x, 28, bt[1] if x < 13 else bt[0])
    for x in range(16, 22):
        p(x, 28, bt[0])

    # ============================================================
    # FINAL: colored outline
    # ============================================================
    c.colored_outline()

    return c
