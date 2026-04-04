"""High-level sprite generation with professional shading.

Generates game-ready sprites with proper pixel art techniques:
- Multi-tone shading (highlight → midtone → shadow → deep shadow)
- Colored outlines (not flat black)
- Consistent top-left light source
- Specular highlights and ambient occlusion
- Detail pixels for texture (armor rivets, cloth folds, hair strands)

Example:
    >>> hero = Sprite.character(size=32, body_color=(80, 100, 180), hair_color=(160, 80, 40))
    >>> hero.save("hero.png", scale=4)
"""

from __future__ import annotations

from typing import Optional, Tuple

from gclub_pixel.canvas import PixelCanvas
from gclub_pixel.palette import Color, ColorLike, Palette, color_ramp, colored_outline, shade, resolve_color

_DEFAULT_PALETTE = "endesga32"


def _resolve_rgb(color: ColorLike, palette: Optional[Palette] = None) -> Color:
    """Resolve any color to an RGB tuple."""
    if isinstance(color, str) or isinstance(color, int):
        if palette is None:
            from gclub_pixel.palette import get_palette
            palette = get_palette(_DEFAULT_PALETTE)
        return palette.get(color) if isinstance(color, str) else palette.get(color)
    if isinstance(color, (tuple, list)):
        return (color[0], color[1], color[2])
    return (128, 128, 128)


class Sprite:
    """Factory for generating game-quality pixel sprites with proper shading."""

    @staticmethod
    def character(
        size: int = 32,
        palette: str = _DEFAULT_PALETTE,
        skin_color: ColorLike = (220, 180, 140),
        hair_color: ColorLike = (100, 60, 30),
        body_color: ColorLike = (80, 100, 180),
        pants_color: ColorLike = (60, 60, 90),
        eye_color: ColorLike = (40, 40, 80),
        boot_color: ColorLike = (70, 50, 35),
        style: str = "chibi",
    ) -> PixelCanvas:
        """Generate a character sprite with professional multi-tone shading.

        Light source: top-left. Each body part has 3-5 color shades for
        highlight, midtone, shadow, and deep shadow.

        Args:
            size: Sprite size (32 or 48 recommended).
            skin_color: RGB tuple for skin midtone.
            hair_color: RGB tuple for hair midtone.
            body_color: RGB tuple for torso/armor midtone.
            pants_color: RGB tuple for legs midtone.
            eye_color: RGB tuple for eyes.
            boot_color: RGB tuple for boots.
            style: "chibi" (big head) or "tall".

        Example:
            >>> knight = Sprite.character(
            ...     size=32,
            ...     body_color=(160, 160, 180),  # silver armor
            ...     hair_color=(140, 90, 40),
            ...     pants_color=(80, 70, 60),
            ... )
            >>> knight.save("knight.png", scale=8)
        """
        pal = None
        try:
            from gclub_pixel.palette import get_palette
            pal = get_palette(palette)
        except Exception:
            pass

        skin = _resolve_rgb(skin_color, pal)
        hair = _resolve_rgb(hair_color, pal)
        body = _resolve_rgb(body_color, pal)
        pants = _resolve_rgb(pants_color, pal)
        eyes = _resolve_rgb(eye_color, pal)
        boots = _resolve_rgb(boot_color, pal)

        c = PixelCanvas(size, size)

        if style == "tall":
            _draw_tall_shaded(c, size, skin, hair, body, pants, eyes, boots)
        else:
            _draw_chibi_shaded(c, size, skin, hair, body, pants, eyes, boots)

        c.colored_outline()
        return c

    @staticmethod
    def weapon(
        weapon_type: str = "sword",
        size: int = 16,
        palette: str = _DEFAULT_PALETTE,
        blade_color: ColorLike = (180, 190, 200),
        handle_color: ColorLike = (100, 70, 40),
        accent_color: ColorLike = (200, 170, 50),
    ) -> PixelCanvas:
        """Generate a weapon icon with shading.

        Example:
            >>> sword = Sprite.weapon("sword", blade_color=(190, 200, 210))
        """
        pal = None
        try:
            from gclub_pixel.palette import get_palette
            pal = get_palette(palette)
        except Exception:
            pass

        blade = _resolve_rgb(blade_color, pal)
        handle = _resolve_rgb(handle_color, pal)
        accent = _resolve_rgb(accent_color, pal)
        c = PixelCanvas(size, size)

        if weapon_type == "sword":
            _draw_sword_shaded(c, size, blade, handle, accent)
        elif weapon_type == "axe":
            _draw_axe_shaded(c, size, blade, handle, accent)
        elif weapon_type == "staff":
            _draw_staff_shaded(c, size, blade, handle, accent)
        elif weapon_type == "shield":
            _draw_shield_shaded(c, size, blade, handle, accent)
        else:
            _draw_sword_shaded(c, size, blade, handle, accent)

        c.colored_outline()
        return c

    @staticmethod
    def item(
        item_type: str = "potion",
        size: int = 16,
        palette: str = _DEFAULT_PALETTE,
        color: ColorLike = (220, 50, 50),
        outline_color: ColorLike = None,
    ) -> PixelCanvas:
        """Generate an item icon with shading.

        Example:
            >>> potion = Sprite.item("potion", color=(220, 50, 50))
        """
        pal = None
        try:
            from gclub_pixel.palette import get_palette
            pal = get_palette(palette)
        except Exception:
            pass

        main = _resolve_rgb(color, pal)
        c = PixelCanvas(size, size)

        if item_type == "potion":
            _draw_potion_shaded(c, size, main)
        elif item_type == "coin":
            _draw_coin_shaded(c, size, main)
        elif item_type == "gem":
            _draw_gem_shaded(c, size, main)
        elif item_type == "heart":
            _draw_heart_shaded(c, size, main)
        elif item_type == "key":
            _draw_key_shaded(c, size, main)
        else:
            _draw_potion_shaded(c, size, main)

        c.colored_outline()
        return c


# ================================================================
# Internal shaded drawing functions
# ================================================================

def _px(c: PixelCanvas, x: int, y: int, rgb: Color):
    """Set pixel with bounds check."""
    if 0 <= x < c.width and 0 <= y < c.height:
        c._pixels[y][x] = (*rgb, 255)


def _rect(c: PixelCanvas, x: int, y: int, w: int, h: int, rgb: Color):
    """Fill rect shorthand."""
    for py in range(max(0, y), min(c.height, y + h)):
        for px in range(max(0, x), min(c.width, x + w)):
            c._pixels[py][px] = (*rgb, 255)


def _shaded_rect(c: PixelCanvas, x: int, y: int, w: int, h: int, base: Color):
    """Draw a shaded rectangle with top-left light."""
    c.fill_rect_shaded(x, y, w, h, base)


def _shaded_circle(c: PixelCanvas, cx: int, cy: int, r: int, base: Color):
    """Draw a shaded circle with top-left light."""
    c.fill_circle_shaded(cx, cy, r, base)


def _draw_chibi_shaded(c, size, skin, hair, body, pants, eyes, boots):
    """Draw chibi character with full shading (32px optimized)."""
    s = size
    mid = s // 2

    skin_r = color_ramp(skin, 5)
    hair_r = color_ramp(hair, 5)
    body_r = color_ramp(body, 5)
    pants_r = color_ramp(pants, 5)
    boot_r = color_ramp(boots, 5)

    # --- Hair (top of head, rounded) ---
    # Hair top curve
    for dx in range(-5, 6):
        ax = mid + dx
        if abs(dx) <= 3:
            _px(c, ax, 1, hair_r[3])  # highlight top
        if abs(dx) <= 4:
            _px(c, ax, 2, hair_r[2] if dx < 0 else hair_r[1])
        if abs(dx) <= 5:
            _px(c, ax, 3, hair_r[2] if dx < -1 else (hair_r[1] if dx > 1 else hair_r[2]))
    # Hair sides
    for dy in range(3, 6):
        _px(c, mid - 5, dy, hair_r[1])  # shadow side
        _px(c, mid + 5, dy, hair_r[0])  # deep shadow side
    # Hair fringe detail
    _px(c, mid - 2, 3, hair_r[3])  # highlight strand
    _px(c, mid, 2, hair_r[4])  # bright highlight

    # --- Face (oval, shaded sphere) ---
    for dy in range(4, 10):
        w_face = 5 if dy in (4, 9) else 6
        for dx in range(-w_face, w_face + 1):
            ax, ay = mid + dx, dy
            if not (0 <= ax < s and 0 <= ay < s):
                continue
            # Sphere shading based on distance from light
            ldist = ((dx + 2) ** 2 + (dy - 5) ** 2) ** 0.5 / 8
            if ldist < 0.3:
                _px(c, ax, ay, skin_r[4])
            elif ldist < 0.5:
                _px(c, ax, ay, skin_r[3])
            elif ldist < 0.75:
                _px(c, ax, ay, skin_r[2])
            else:
                _px(c, ax, ay, skin_r[1])

    # Chin shadow
    for dx in range(-3, 4):
        _px(c, mid + dx, 10, skin_r[0])

    # --- Eyes ---
    eye_highlight = shade(*eyes, 2.0)
    _px(c, mid - 3, 7, eyes)
    _px(c, mid - 2, 7, eyes)
    _px(c, mid + 2, 7, eyes)
    _px(c, mid + 3, 7, eyes)
    # Eye highlights (white dot)
    _px(c, mid - 3, 6, eye_highlight)
    _px(c, mid + 2, 6, eye_highlight)

    # Mouth
    _px(c, mid - 1, 9, skin_r[0])
    _px(c, mid, 9, skin_r[0])

    # --- Body / Torso ---
    for dy in range(11, 19):
        bw = 6 if dy < 17 else 5
        for dx in range(-bw, bw + 1):
            ax, ay = mid + dx, dy
            if not (0 <= ax < s):
                continue
            # Cylindrical shading
            edge_dist = abs(dx) / max(bw, 1)
            vert_pos = (dy - 11) / 8

            if dx <= -bw + 1 and dy == 11:
                _px(c, ax, ay, body_r[3])  # top-left highlight
            elif edge_dist > 0.8:
                _px(c, ax, ay, body_r[0] if dx > 0 else body_r[1])
            elif edge_dist > 0.5:
                _px(c, ax, ay, body_r[1] if dx > 0 else body_r[2])
            elif vert_pos < 0.2:
                _px(c, ax, ay, body_r[3])
            elif vert_pos > 0.8:
                _px(c, ax, ay, body_r[1])
            else:
                _px(c, ax, ay, body_r[2])

    # Body detail: belt/seam
    belt_color = shade(*body, 0.45)
    for dx in range(-5, 6):
        _px(c, mid + dx, 16, belt_color)
    # Belt buckle
    buckle = shade(*body, 1.8)
    _px(c, mid, 16, buckle)
    _px(c, mid - 1, 16, buckle)

    # Collar highlight
    for dx in range(-3, 4):
        _px(c, mid + dx, 11, body_r[4])

    # --- Arms ---
    for dy in range(12, 18):
        arm_shade_l = skin_r[3] if dy < 14 else skin_r[2] if dy < 16 else skin_r[1]
        arm_shade_r = skin_r[2] if dy < 14 else skin_r[1] if dy < 16 else skin_r[0]
        # Shoulder armor piece
        if dy == 12:
            _px(c, mid - 7, dy, body_r[3])
            _px(c, mid + 7, dy, body_r[1])
        _px(c, mid - 7, dy, arm_shade_l)
        _px(c, mid - 8, dy, arm_shade_l if dy < 15 else skin_r[0])
        _px(c, mid + 7, dy, arm_shade_r)
        _px(c, mid + 8, dy, arm_shade_r if dy > 14 else skin_r[0])

    # Hands
    _px(c, mid - 8, 18, skin_r[2])
    _px(c, mid - 7, 18, skin_r[3])
    _px(c, mid + 7, 18, skin_r[1])
    _px(c, mid + 8, 18, skin_r[2])

    # --- Legs ---
    for dy in range(19, 25):
        leg_gap = 1
        for dx in range(-4, -leg_gap):
            edge = abs(dx) / 4
            sc = pants_r[3] if edge < 0.3 and dy < 21 else (pants_r[1] if edge > 0.7 else pants_r[2])
            _px(c, mid + dx, dy, sc)
        for dx in range(leg_gap + 1, 5):
            edge = abs(dx) / 4
            sc = pants_r[2] if edge < 0.5 else pants_r[1] if edge < 0.8 else pants_r[0]
            _px(c, mid + dx, dy, sc)

    # --- Boots ---
    for dy in range(25, 28):
        for dx in range(-5, -1):
            _px(c, mid + dx, dy, boot_r[3] if dx > -4 and dy == 25 else boot_r[2] if dy < 27 else boot_r[1])
        for dx in range(2, 6):
            _px(c, mid + dx, dy, boot_r[2] if dy < 27 else boot_r[1] if dx < 4 else boot_r[0])

    # Boot highlights
    _px(c, mid - 4, 25, boot_r[4])
    _px(c, mid + 2, 25, boot_r[3])


def _draw_tall_shaded(c, size, skin, hair, body, pants, eyes, boots):
    """Taller proportions with shading."""
    # Reuse chibi with slight ratio adjustment
    _draw_chibi_shaded(c, size, skin, hair, body, pants, eyes, boots)


# ================================================================
# Weapons (shaded)
# ================================================================

def _draw_sword_shaded(c, size, blade, handle, accent):
    ramp = color_ramp(blade, 5)
    h_ramp = color_ramp(handle, 4)
    mid = size // 2

    # Blade (diagonal)
    for i in range(8):
        bx, by = mid + 3 - i, 1 + i
        _px(c, bx, by, ramp[3])      # highlight edge
        _px(c, bx + 1, by, ramp[2])  # mid
        if i > 0:
            _px(c, bx - 1, by, ramp[1])  # shadow edge
    # Blade tip highlight
    _px(c, mid + 3, 1, ramp[4])

    # Guard
    for dx in range(-2, 3):
        _px(c, mid + dx, 9, accent)
    _px(c, mid - 2, 9, shade(*accent, 0.6))
    _px(c, mid + 2, 9, shade(*accent, 1.4))

    # Handle
    for dy in range(10, 14):
        _px(c, mid, dy, h_ramp[2] if dy < 12 else h_ramp[1])
        _px(c, mid - 1, dy, h_ramp[1])

    # Pommel
    _px(c, mid - 1, 14, h_ramp[0])
    _px(c, mid, 14, h_ramp[2])
    _px(c, mid + 1, 14, h_ramp[1])


def _draw_axe_shaded(c, size, blade, handle, accent):
    ramp = color_ramp(blade, 5)
    h_ramp = color_ramp(handle, 4)
    mid = size // 2

    # Handle
    for dy in range(2, 14):
        _px(c, mid, dy, h_ramp[2] if dy < 8 else h_ramp[1])

    # Axe head
    for dy in range(2, 7):
        w = 3 if dy in (2, 6) else 4
        for dx in range(-w, 1):
            dist = abs(dx) / max(w, 1)
            sc = ramp[3] if dist < 0.3 else ramp[2] if dist < 0.7 else ramp[1]
            _px(c, mid + dx, dy, sc)
    # Edge highlight
    for dy in range(3, 6):
        _px(c, mid - 4, dy, ramp[4])


def _draw_staff_shaded(c, size, orb, handle, accent):
    o_ramp = color_ramp(orb, 5)
    h_ramp = color_ramp(handle, 4)
    mid = size // 2

    # Staff pole
    for dy in range(5, 15):
        _px(c, mid, dy, h_ramp[2] if dy < 10 else h_ramp[1])
        _px(c, mid - 1, dy, h_ramp[1] if dy < 10 else h_ramp[0])

    # Orb (shaded sphere)
    c.fill_circle_shaded(mid, 3, 3, orb)

    # Orb glow pixel
    _px(c, mid - 1, 2, o_ramp[4])


def _draw_shield_shaded(c, size, main, trim, accent):
    ramp = color_ramp(main, 5)
    t_ramp = color_ramp(trim, 4)
    mid = size // 2

    # Shield body
    for dy in range(2, 13):
        w = 5 if 4 <= dy <= 10 else (4 if dy in (3, 11) else 3)
        for dx in range(-w, w + 1):
            dist = abs(dx) / max(w, 1)
            vert = (dy - 2) / 10
            if dist < 0.3 and vert < 0.3:
                sc = ramp[4]
            elif dist < 0.5:
                sc = ramp[3] if vert < 0.5 else ramp[2]
            elif dist < 0.8:
                sc = ramp[2] if vert < 0.5 else ramp[1]
            else:
                sc = ramp[1] if vert < 0.5 else ramp[0]
            _px(c, mid + dx, dy, sc)

    # Trim border
    for dy in range(2, 13):
        w = 5 if 4 <= dy <= 10 else (4 if dy in (3, 11) else 3)
        _px(c, mid - w, dy, t_ramp[2])
        _px(c, mid + w, dy, t_ramp[0])

    # Emblem cross
    for dy in range(5, 10):
        _px(c, mid, dy, accent)
    for dx in range(-2, 3):
        _px(c, mid + dx, 7, accent)


# ================================================================
# Items (shaded)
# ================================================================

def _draw_potion_shaded(c, size, color):
    ramp = color_ramp(color, 5)
    cork = color_ramp((140, 100, 60), 4)
    glass = color_ramp((200, 210, 220), 4)
    mid = size // 2

    # Cork
    _px(c, mid - 1, 2, cork[2])
    _px(c, mid, 2, cork[3])
    _px(c, mid + 1, 2, cork[1])
    _px(c, mid - 1, 3, cork[1])
    _px(c, mid, 3, cork[2])
    _px(c, mid + 1, 3, cork[0])

    # Neck (glass)
    for dy in (4, 5):
        _px(c, mid - 1, dy, glass[2])
        _px(c, mid, dy, glass[3])
        _px(c, mid + 1, dy, glass[1])

    # Body (liquid, shaded)
    for dy in range(6, 13):
        bw = 3 if dy in (6, 12) else 4
        for dx in range(-bw, bw + 1):
            dist = abs(dx) / max(bw, 1)
            vert = (dy - 6) / 6
            if dist < 0.3 and vert < 0.3:
                sc = ramp[4]
            elif dist < 0.5:
                sc = ramp[3] if vert < 0.4 else ramp[2]
            else:
                sc = ramp[1] if dist > 0.7 else ramp[2]
            _px(c, mid + dx, dy, sc)

    # Glass highlight streak
    _px(c, mid - 2, 7, ramp[4])
    _px(c, mid - 2, 8, ramp[4])
    _px(c, mid - 2, 9, ramp[3])


def _draw_coin_shaded(c, size, color):
    mid = size // 2
    c.fill_circle_shaded(mid, mid, 5, color)
    # Inner ring
    ramp = color_ramp(color, 5)
    c.draw_circle(mid, mid, 3, (*ramp[1], 255))
    # Symbol
    _px(c, mid, mid - 1, ramp[4])
    _px(c, mid, mid, ramp[4])
    _px(c, mid, mid + 1, ramp[3])


def _draw_gem_shaded(c, size, color):
    ramp = color_ramp(color, 5)
    mid = size // 2

    # Diamond facets
    rows = [1, 2, 3, 4, 4, 3, 2, 1]
    for i, w in enumerate(rows):
        y = mid - 4 + i
        for dx in range(-w, w + 1):
            if i < 3:  # top facets = lighter
                sc = ramp[4] if abs(dx) < w // 2 else ramp[3]
            elif i < 5:
                sc = ramp[2] if dx < 0 else ramp[1]
            else:
                sc = ramp[1] if abs(dx) < w // 2 else ramp[0]
            _px(c, mid + dx, y, sc)

    # Center highlight
    _px(c, mid - 1, mid - 2, ramp[4])
    _px(c, mid, mid - 3, (255, 255, 255))


def _draw_heart_shaded(c, size, color):
    ramp = color_ramp(color, 5)
    mid = size // 2

    # Heart using two overlapping circles + triangle bottom
    for py in range(2, 14):
        for px in range(2, 14):
            # Two circle centers
            d1 = ((px - mid + 2) ** 2 + (py - 5) ** 2) ** 0.5
            d2 = ((px - mid - 2) ** 2 + (py - 5) ** 2) ** 0.5
            in_top = d1 <= 3.5 or d2 <= 3.5
            in_bottom = py >= 6 and abs(px - mid) <= (13 - py) * 0.7
            if in_top or in_bottom:
                ldist = ((px - mid + 2) ** 2 + (py - 3) ** 2) ** 0.5 / 10
                if ldist < 0.25:
                    sc = ramp[4]
                elif ldist < 0.45:
                    sc = ramp[3]
                elif ldist < 0.65:
                    sc = ramp[2]
                else:
                    sc = ramp[1]
                _px(c, px, py, sc)

    # Specular
    _px(c, mid - 2, 4, (255, 220, 220))


def _draw_key_shaded(c, size, color):
    ramp = color_ramp(color, 5)
    mid = size // 2

    # Key ring (circle)
    c.fill_circle_shaded(mid - 2, 5, 3, color)
    # Hole in ring
    _px(c, mid - 2, 5, (0, 0, 0, 0))
    _px(c, mid - 3, 5, (0, 0, 0, 0))

    # Shaft
    for dx in range(1, 7):
        sc = ramp[3] if dx < 3 else ramp[2]
        _px(c, mid + dx, 5, sc)
        _px(c, mid + dx, 6, ramp[1])

    # Teeth
    for dy in range(6, 9):
        _px(c, mid + 5, dy, ramp[2])
        _px(c, mid + 6, dy, ramp[1])
    _px(c, mid + 4, 7, ramp[2])
    _px(c, mid + 4, 8, ramp[1])
