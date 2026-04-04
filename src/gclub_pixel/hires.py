"""High-resolution rendering pipeline: draw smooth, downsample to pixel art.

The trick: draw at 8x resolution with anti-aliased shapes (circles, ellipses,
bezier curves, gradients), then downsample to target pixel size. This gives
natural curves and professional shading that's impossible to achieve by
placing individual pixels.

This is the same approach Dead Cells uses (3D render → pixel shader),
but in pure 2D Python.

Pipeline:
    1. Create HiResCanvas at 8x target size (e.g., 256x256 for 32x32 output)
    2. Draw smooth shapes with PIL's anti-aliased drawing
    3. Apply lighting/shading at high res (easy and looks great)
    4. Downsample to target size with palette-aware quantization
    5. Auto-apply colored outline

Example:
    >>> hr = HiResCanvas(32, 32, scale=8)  # internal: 256x256
    >>> hr.ellipse(80, 20, 96, 80, fill=(220, 180, 140))  # smooth head
    >>> hr.ellipse(60, 80, 196, 200, fill=(100, 120, 180))  # body
    >>> result = hr.render()  # → beautiful 32x32 pixel art
    >>> result.save("character.png", scale=8)
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFilter

from gclub_pixel.canvas import PixelCanvas
from gclub_pixel.palette import Color, Palette, color_ramp, shade, colored_outline, get_palette


class HiResCanvas:
    """Draw at high resolution, output as pixel art.

    All coordinates are in the HIGH-RES space (e.g., 0-255 for a 32px target
    at 8x scale). This gives you sub-pixel precision and smooth curves.

    Args:
        target_w: Final pixel art width (e.g., 32).
        target_h: Final pixel art height (e.g., 32).
        scale: Internal supersampling factor (default 8).
        palette: Optional palette name for color quantization.

    Example:
        >>> hr = HiResCanvas(32, 32)
        >>> hr.ellipse(80, 30, 176, 110, fill=(220, 180, 140))  # head
        >>> result = hr.render()
        >>> result.save("test.png", scale=8)
    """

    def __init__(self, target_w: int, target_h: int, scale: int = 8, palette: str = None):
        self.target_w = target_w
        self.target_h = target_h
        self.scale = scale
        self.hi_w = target_w * scale
        self.hi_h = target_h * scale
        self._img = Image.new("RGBA", (self.hi_w, self.hi_h), (0, 0, 0, 0))
        self._draw = ImageDraw.Draw(self._img)
        self._palette = get_palette(palette) if palette else None

    # ==================== Drawing (hi-res coords) ====================

    def ellipse(self, x1: int, y1: int, x2: int, y2: int,
                fill: Color = None, outline: Color = None, width: int = 0) -> "HiResCanvas":
        """Draw a smooth anti-aliased ellipse.

        Example:
            >>> hr.ellipse(80, 30, 176, 110, fill=(220, 180, 140))
        """
        f = (*fill, 255) if fill else None
        o = (*outline, 255) if outline else None
        self._draw.ellipse([x1, y1, x2, y2], fill=f, outline=o, width=width or 0)
        return self

    def rect(self, x1: int, y1: int, x2: int, y2: int,
             fill: Color = None, outline: Color = None) -> "HiResCanvas":
        """Draw a rectangle."""
        f = (*fill, 255) if fill else None
        o = (*outline, 255) if outline else None
        self._draw.rectangle([x1, y1, x2, y2], fill=f, outline=o)
        return self

    def rounded_rect(self, x1: int, y1: int, x2: int, y2: int,
                     radius: int, fill: Color = None) -> "HiResCanvas":
        """Draw a rounded rectangle."""
        f = (*fill, 255) if fill else None
        self._draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=f)
        return self

    def polygon(self, points: List[Tuple[int, int]], fill: Color = None,
                outline: Color = None) -> "HiResCanvas":
        """Draw a polygon."""
        f = (*fill, 255) if fill else None
        o = (*outline, 255) if outline else None
        self._draw.polygon(points, fill=f, outline=o)
        return self

    def line(self, x1: int, y1: int, x2: int, y2: int,
             fill: Color = (255, 255, 255), width: int = 2) -> "HiResCanvas":
        """Draw a line."""
        self._draw.line([x1, y1, x2, y2], fill=(*fill, 255), width=width)
        return self

    # ==================== Shaded Drawing ====================

    def shaded_ellipse(self, x1: int, y1: int, x2: int, y2: int,
                       base_color: Color, light_angle: float = 135) -> "HiResCanvas":
        """Draw an ellipse with smooth spherical shading.

        Light comes from the specified angle (135 = top-left, default).
        Creates 5-tone gradient from highlight to deep shadow.

        Example:
            >>> hr.shaded_ellipse(80, 20, 176, 100, (220, 180, 140))  # shaded head
        """
        ramp = color_ramp(base_color, 5)
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        rx = (x2 - x1) / 2
        ry = (y2 - y1) / 2

        # Light direction
        lx = math.cos(math.radians(light_angle)) * rx * 0.4
        ly = math.sin(math.radians(light_angle)) * ry * 0.4
        light_cx = cx + lx
        light_cy = cy + ly

        pixels = self._img.load()
        for py in range(max(0, y1), min(self.hi_h, y2 + 1)):
            for px in range(max(0, x1), min(self.hi_w, x2 + 1)):
                dx = (px - cx) / max(rx, 1)
                dy = (py - cy) / max(ry, 1)
                if dx * dx + dy * dy > 1.0:
                    continue

                # Distance from light source (normalized)
                ldx = (px - light_cx) / max(rx * 2, 1)
                ldy = (py - light_cy) / max(ry * 2, 1)
                ldist = min(1.0, (ldx * ldx + ldy * ldy) ** 0.5)

                if ldist < 0.15:
                    c = ramp[4]
                elif ldist < 0.3:
                    c = ramp[3]
                elif ldist < 0.55:
                    c = ramp[2]
                elif ldist < 0.8:
                    c = ramp[1]
                else:
                    c = ramp[0]

                pixels[px, py] = (*c, 255)
        return self

    def shaded_rect(self, x1: int, y1: int, x2: int, y2: int,
                    base_color: Color) -> "HiResCanvas":
        """Draw a rectangle with cylindrical shading (left-lit)."""
        ramp = color_ramp(base_color, 5)
        w = x2 - x1
        h = y2 - y1
        pixels = self._img.load()

        for py in range(max(0, y1), min(self.hi_h, y2)):
            for px in range(max(0, x1), min(self.hi_w, x2)):
                edge_x = (px - x1) / max(w - 1, 1)
                edge_y = (py - y1) / max(h - 1, 1)
                # Cylindrical: brighter on left, darker on right
                light = edge_x * 0.7 + edge_y * 0.3
                if light < 0.15:
                    c = ramp[4]
                elif light < 0.3:
                    c = ramp[3]
                elif light < 0.55:
                    c = ramp[2]
                elif light < 0.75:
                    c = ramp[1]
                else:
                    c = ramp[0]
                pixels[px, py] = (*c, 255)
        return self

    def gradient_rect(self, x1: int, y1: int, x2: int, y2: int,
                      color_top: Color, color_bottom: Color) -> "HiResCanvas":
        """Draw a vertical gradient rectangle."""
        h = y2 - y1
        pixels = self._img.load()
        for py in range(max(0, y1), min(self.hi_h, y2)):
            t = (py - y1) / max(h - 1, 1)
            r = int(color_top[0] + (color_bottom[0] - color_top[0]) * t)
            g = int(color_top[1] + (color_bottom[1] - color_top[1]) * t)
            b = int(color_top[2] + (color_bottom[2] - color_top[2]) * t)
            for px in range(max(0, x1), min(self.hi_w, x2)):
                pixels[px, py] = (r, g, b, 255)
        return self

    # ==================== Compositing ====================

    def paste_canvas(self, other: "HiResCanvas", x: int = 0, y: int = 0) -> "HiResCanvas":
        """Paste another HiResCanvas onto this one."""
        self._img.paste(other._img, (x, y), other._img)
        self._draw = ImageDraw.Draw(self._img)
        return self

    # ==================== Render to pixel art ====================

    def render(self, outline: bool = True) -> PixelCanvas:
        """Downsample to target pixel art size.

        Uses LANCZOS resampling for smooth downscaling, then snaps
        to nearest-neighbor pixel grid.

        Args:
            outline: Whether to add colored outline (default True).

        Returns:
            PixelCanvas at target resolution.
        """
        # Downsample with high-quality filter
        small = self._img.resize(
            (self.target_w, self.target_h),
            Image.LANCZOS
        )

        # Convert to PixelCanvas
        result = PixelCanvas(self.target_w, self.target_h)
        for y in range(self.target_h):
            for x in range(self.target_w):
                r, g, b, a = small.getpixel((x, y))
                if a > 20:  # threshold out near-transparent AA artifacts
                    result._pixels[y][x] = (r, g, b, 255)

        if outline:
            result.colored_outline()
        return result

    def render_crisp(self, outline: bool = True) -> PixelCanvas:
        """Downsample with nearest-neighbor for a crisper, more retro look."""
        small = self._img.resize(
            (self.target_w, self.target_h),
            Image.NEAREST
        )
        result = PixelCanvas(self.target_w, self.target_h)
        for y in range(self.target_h):
            for x in range(self.target_w):
                r, g, b, a = small.getpixel((x, y))
                if a > 20:
                    result._pixels[y][x] = (r, g, b, 255)
        if outline:
            result.colored_outline()
        return result


def quick_character(
    target_size: int = 32,
    skin: Color = (220, 180, 140),
    hair: Color = (120, 75, 35),
    armor: Color = (100, 120, 180),
    pants: Color = (70, 65, 80),
    eye: Color = (50, 70, 120),
    boot: Color = (60, 45, 30),
    accent: Color = (180, 60, 50),
    hair_style: str = "short",
    scale: int = 8,
) -> PixelCanvas:
    """Generate a character using the hi-res pipeline.

    Draws smooth shapes at 8x resolution, then downsamples to pixel art.
    This produces much smoother, more natural-looking characters than
    the direct pixel-placement approach.

    Args:
        target_size: Output size (32, 48, or 64).
        skin: Skin midtone RGB.
        hair: Hair midtone RGB.
        armor: Armor/body midtone RGB.
        pants: Pants midtone RGB.
        eye: Eye color RGB.
        boot: Boot color RGB.
        accent: Accent color RGB.
        hair_style: "short", "long", "spiky", "messy", "ponytail".
        scale: Internal supersampling factor.

    Returns:
        PixelCanvas pixel art character.

    Example:
        >>> knight = quick_character(32, armor=(170, 175, 190), accent=(180, 50, 50))
        >>> knight.save("knight.png", scale=8)
    """
    hr = HiResCanvas(target_size, target_size, scale=scale)
    S = target_size * scale  # total hi-res size
    mid = S // 2

    skin_hi = shade(*skin, 1.15)
    skin_lo = shade(*skin, 0.65)
    hair_hi = shade(*hair, 1.3)
    hair_lo = shade(*hair, 0.5)

    # ---- HAIR (background layer, drawn first) ----
    hair_top = int(S * 0.02)
    hair_bot = int(S * 0.32)
    hair_w = int(S * 0.38)

    if hair_style == "long":
        # Long hair flows down past shoulders
        hr.shaded_ellipse(mid - hair_w, hair_top, mid + hair_w, hair_bot + int(S * 0.25), hair)
        # Side curtains
        hr.shaded_rect(mid - hair_w, int(S * 0.18), mid - hair_w + int(S * 0.08), int(S * 0.55), hair)
        hr.shaded_rect(mid + hair_w - int(S * 0.08), int(S * 0.18), mid + hair_w, int(S * 0.55), shade(*hair, 0.7))
    elif hair_style == "spiky":
        # Spiky: multiple pointed ellipses
        for dx, dy, rr in [(-0.15, -0.05, 0.12), (0, -0.08, 0.13), (0.15, -0.04, 0.11), (-0.08, -0.07, 0.1), (0.1, -0.06, 0.1)]:
            sx = mid + int(dx * S)
            sy = int(S * 0.08) + int(dy * S)
            r = int(rr * S)
            hr.shaded_ellipse(sx - r, sy - r, sx + r, sy + int(r * 1.8), hair)
    elif hair_style == "ponytail":
        hr.shaded_ellipse(mid - hair_w, hair_top, mid + hair_w, hair_bot, hair)
        # Ponytail strand
        hr.shaded_ellipse(mid + int(S * 0.05), int(S * 0.2), mid + int(S * 0.15), int(S * 0.55), shade(*hair, 0.85))
    elif hair_style == "messy":
        # Messy: larger, irregular
        hr.shaded_ellipse(mid - int(hair_w * 1.15), hair_top - int(S * 0.02), mid + int(hair_w * 1.15), hair_bot + int(S * 0.03), hair)
    else:
        # Short (default)
        hr.shaded_ellipse(mid - hair_w, hair_top, mid + hair_w, hair_bot, hair)

    # ---- HEAD (spherical shading) ----
    head_top = int(S * 0.08)
    head_bot = int(S * 0.32)
    head_w = int(S * 0.3)
    hr.shaded_ellipse(mid - head_w, head_top, mid + head_w, head_bot, skin)

    # ---- EARS ----
    ear_y = int(S * 0.18)
    ear_r = int(S * 0.03)
    hr.shaded_ellipse(mid - head_w - ear_r, ear_y - ear_r, mid - head_w + ear_r, ear_y + ear_r, skin)
    hr.shaded_ellipse(mid + head_w - ear_r, ear_y - ear_r, mid + head_w + ear_r, ear_y + ear_r, shade(*skin, 0.8))

    # ---- EYES ----
    eye_y = int(S * 0.19)
    eye_w = int(S * 0.055)
    eye_h = int(S * 0.045)
    eye_gap = int(S * 0.06)

    for side, lit in [(-1, True), (1, False)]:
        ex = mid + side * eye_gap
        # Sclera
        hr.ellipse(ex - eye_w, eye_y - eye_h, ex + eye_w, eye_y + eye_h,
                   fill=(240, 240, 245))
        # Iris
        iris_r = int(eye_w * 0.65)
        hr.ellipse(ex - iris_r, eye_y - iris_r + 1, ex + iris_r, eye_y + iris_r + 1,
                   fill=eye)
        # Pupil
        pupil_r = int(iris_r * 0.55)
        hr.ellipse(ex - pupil_r, eye_y - pupil_r + 1, ex + pupil_r, eye_y + pupil_r + 1,
                   fill=shade(*eye, 0.25))
        # Highlight
        hl_r = max(2, int(eye_w * 0.3))
        hl_x = ex - int(eye_w * 0.3) if lit else ex + int(eye_w * 0.3)
        hl_y = eye_y - int(eye_h * 0.3)
        hr.ellipse(hl_x - hl_r, hl_y - hl_r, hl_x + hl_r, hl_y + hl_r,
                   fill=(255, 255, 255))

    # ---- EYEBROWS ----
    brow_y = eye_y - int(S * 0.04)
    brow_w = int(S * 0.06)
    brow_thick = max(2, int(S * 0.012))
    for side in [-1, 1]:
        bx = mid + side * eye_gap
        hr.line(bx - brow_w, brow_y, bx + brow_w, brow_y + 1,
                fill=shade(*hair, 0.4), width=brow_thick)

    # ---- NOSE ----
    nose_y = int(S * 0.24)
    nose_r = int(S * 0.015)
    hr.ellipse(mid - nose_r, nose_y, mid + nose_r * 2, nose_y + nose_r * 2,
               fill=shade(*skin, 0.78))

    # ---- MOUTH ----
    mouth_y = int(S * 0.275)
    mouth_w = int(S * 0.04)
    hr.line(mid - mouth_w, mouth_y, mid + mouth_w, mouth_y,
            fill=shade(*skin, 0.55), width=max(2, int(S * 0.008)))
    # Lower lip highlight
    hr.line(mid - int(mouth_w * 0.6), mouth_y + 2, mid + int(mouth_w * 0.6), mouth_y + 2,
            fill=shade(*skin, 0.75), width=max(1, int(S * 0.006)))

    # ---- NECK ----
    neck_w = int(S * 0.08)
    neck_top = int(S * 0.30)
    neck_bot = int(S * 0.37)
    hr.shaded_rect(mid - neck_w, neck_top, mid + neck_w, neck_bot, shade(*skin, 0.9))

    # ---- TORSO (rounded rectangle, shaded) ----
    torso_top = int(S * 0.35)
    torso_bot = int(S * 0.62)
    torso_w = int(S * 0.22)
    hr.shaded_rect(mid - torso_w, torso_top, mid + torso_w, torso_bot, armor)

    # Collar highlight
    collar_h = int(S * 0.025)
    hr.rect(mid - torso_w + 2, torso_top, mid + torso_w - 2, torso_top + collar_h,
            fill=shade(*armor, 1.35))

    # Armor center seam
    seam_x = mid
    hr.line(seam_x, torso_top + collar_h, seam_x, torso_bot - int(S * 0.05),
            fill=shade(*armor, 0.55), width=max(1, int(S * 0.006)))

    # Shoulder pads
    pad_w = int(S * 0.06)
    pad_h = int(S * 0.05)
    hr.shaded_ellipse(mid - torso_w - pad_w, torso_top - 2,
                      mid - torso_w + pad_w, torso_top + pad_h * 2,
                      shade(*armor, 1.1))
    hr.shaded_ellipse(mid + torso_w - pad_w, torso_top - 2,
                      mid + torso_w + pad_w, torso_top + pad_h * 2,
                      shade(*armor, 0.75))

    # ---- BELT ----
    belt_y = int(S * 0.57)
    belt_h = int(S * 0.03)
    hr.rect(mid - torso_w, belt_y, mid + torso_w, belt_y + belt_h,
            fill=shade(*accent, 0.7))
    # Buckle
    buckle_r = int(S * 0.018)
    hr.ellipse(mid - buckle_r, belt_y - 1, mid + buckle_r, belt_y + belt_h + 1,
               fill=shade(*accent, 1.4))

    # ---- ARMS (smooth ellipses) ----
    arm_top = int(S * 0.36)
    arm_bot = int(S * 0.58)
    arm_w = int(S * 0.06)

    # Left arm (lit)
    hr.shaded_ellipse(mid - torso_w - arm_w * 2, arm_top,
                      mid - torso_w, arm_bot, shade(*armor, 1.05))
    # Right arm (shadow)
    hr.shaded_ellipse(mid + torso_w, arm_top,
                      mid + torso_w + arm_w * 2, arm_bot, shade(*armor, 0.8))

    # Forearms (skin)
    fa_top = int(S * 0.52)
    fa_bot = int(S * 0.65)
    hr.shaded_ellipse(mid - torso_w - arm_w * 2 + 2, fa_top,
                      mid - torso_w + 2, fa_bot, shade(*skin, 0.95))
    hr.shaded_ellipse(mid + torso_w - 2, fa_top,
                      mid + torso_w + arm_w * 2 - 2, fa_bot, shade(*skin, 0.8))

    # Hands
    hand_r = int(S * 0.03)
    hr.shaded_ellipse(mid - torso_w - arm_w - hand_r, fa_bot - hand_r,
                      mid - torso_w - arm_w + hand_r, fa_bot + hand_r, skin)
    hr.shaded_ellipse(mid + torso_w + arm_w - hand_r, fa_bot - hand_r,
                      mid + torso_w + arm_w + hand_r, fa_bot + hand_r, shade(*skin, 0.85))

    # ---- LEGS ----
    leg_top = int(S * 0.62)
    leg_bot = int(S * 0.82)
    leg_w = int(S * 0.09)
    gap = int(S * 0.03)

    # Left leg
    hr.shaded_rect(mid - leg_w - gap, leg_top, mid - gap, leg_bot, pants)
    # Right leg
    hr.shaded_rect(mid + gap, leg_top, mid + leg_w + gap, leg_bot, shade(*pants, 0.8))

    # ---- BOOTS ----
    boot_top = int(S * 0.80)
    boot_bot = int(S * 0.92)
    boot_extra = int(S * 0.02)

    hr.shaded_rect(mid - leg_w - gap - boot_extra, boot_top,
                   mid - gap + boot_extra, boot_bot, boot)
    hr.shaded_rect(mid + gap - boot_extra, boot_top,
                   mid + leg_w + gap + boot_extra, boot_bot, shade(*boot, 0.75))

    # Boot top highlight
    hr.rect(mid - leg_w - gap - boot_extra, boot_top,
            mid - gap + boot_extra, boot_top + 2,
            fill=shade(*boot, 1.4))

    return hr.render(outline=True)
