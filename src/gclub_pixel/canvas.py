"""PixelCanvas - the core drawing surface for pixel art.

PixelCanvas is a grid of pixels with a fixed size and optional palette.
All drawing methods return self for chaining.

Example:
    >>> c = PixelCanvas(32, 32, palette="pico8")
    >>> c.fill_rect(4, 4, 24, 24, "blue").outline("black").save("box.png")
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import List, Optional, Tuple, Union

from PIL import Image

from gclub_pixel.palette import (
    Color,
    ColorLike,
    Palette,
    get_palette,
    resolve_color,
    color_ramp,
    colored_outline,
    shade,
)

TRANSPARENT = (0, 0, 0, 0)


class PixelCanvas:
    """A pixel art canvas with drawing primitives and palette support.

    Args:
        width: Canvas width in pixels (typically 8-128).
        height: Canvas height in pixels.
        palette: Palette name ("pico8", "db16", etc.) or Palette instance.
                 When set, colors can be referenced by name: "red", "blue".
        bg: Background color. Default is transparent.

    Example:
        >>> c = PixelCanvas(16, 16, palette="pico8")
        >>> c.fill_rect(2, 2, 12, 12, "red")
        >>> c.save("square.png", scale=8)
    """

    def __init__(
        self,
        width: int,
        height: int,
        palette: Union[str, Palette, None] = None,
        bg: ColorLike = TRANSPARENT,
    ):
        self.width = width
        self.height = height

        if isinstance(palette, str):
            self.palette = get_palette(palette)
        elif isinstance(palette, Palette):
            self.palette = palette
        else:
            self.palette = None

        bg_rgba = resolve_color(bg, self.palette) if bg != TRANSPARENT else TRANSPARENT
        self._pixels: List[List[Tuple[int, int, int, int]]] = [
            [bg_rgba for _ in range(width)] for _ in range(height)
        ]

    def _resolve(self, color: ColorLike) -> Tuple[int, int, int, int]:
        return resolve_color(color, self.palette)

    def _in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    # ==================== Basic Drawing ====================

    def set_pixel(self, x: int, y: int, color: ColorLike) -> "PixelCanvas":
        """Set a single pixel.

        Args:
            x: X coordinate (0 = left).
            y: Y coordinate (0 = top).
            color: Color name, index, or RGB(A) tuple.

        Example:
            >>> c.set_pixel(5, 5, "red")
            >>> c.set_pixel(6, 6, (255, 0, 0))
        """
        if self._in_bounds(x, y):
            self._pixels[y][x] = self._resolve(color)
        return self

    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int, int]:
        """Get the RGBA value of a pixel."""
        if self._in_bounds(x, y):
            return self._pixels[y][x]
        return TRANSPARENT

    def fill(self, color: ColorLike) -> "PixelCanvas":
        """Fill the entire canvas with a color.

        Example:
            >>> c.fill("black")
        """
        rgba = self._resolve(color)
        self._pixels = [[rgba for _ in range(self.width)] for _ in range(self.height)]
        return self

    def clear(self) -> "PixelCanvas":
        """Clear the canvas to transparent."""
        self._pixels = [[TRANSPARENT for _ in range(self.width)] for _ in range(self.height)]
        return self

    # ==================== Shape Drawing ====================

    def fill_rect(self, x: int, y: int, w: int, h: int, color: ColorLike) -> "PixelCanvas":
        """Draw a filled rectangle.

        Args:
            x, y: Top-left corner position.
            w, h: Width and height in pixels.
            color: Fill color.

        Example:
            >>> c.fill_rect(4, 4, 8, 8, "blue")  # 8x8 blue square at (4,4)
        """
        rgba = self._resolve(color)
        for py in range(max(0, y), min(self.height, y + h)):
            for px in range(max(0, x), min(self.width, x + w)):
                self._pixels[py][px] = rgba
        return self

    def draw_rect(self, x: int, y: int, w: int, h: int, color: ColorLike) -> "PixelCanvas":
        """Draw a rectangle outline (1px border).

        Example:
            >>> c.draw_rect(2, 2, 12, 12, "white")
        """
        rgba = self._resolve(color)
        for px in range(x, x + w):
            if self._in_bounds(px, y): self._pixels[y][px] = rgba
            if self._in_bounds(px, y + h - 1): self._pixels[y + h - 1][px] = rgba
        for py in range(y, y + h):
            if self._in_bounds(x, py): self._pixels[py][x] = rgba
            if self._in_bounds(x + w - 1, py): self._pixels[py][x + w - 1] = rgba
        return self

    def draw_circle(self, cx: int, cy: int, r: int, color: ColorLike) -> "PixelCanvas":
        """Draw a circle outline using Bresenham's algorithm.

        Args:
            cx, cy: Center position.
            r: Radius in pixels.
            color: Line color.

        Example:
            >>> c.draw_circle(16, 16, 8, "white")
        """
        rgba = self._resolve(color)
        x, y, d = 0, r, 3 - 2 * r
        while x <= y:
            for px, py in [
                (cx + x, cy + y), (cx - x, cy + y), (cx + x, cy - y), (cx - x, cy - y),
                (cx + y, cy + x), (cx - y, cy + x), (cx + y, cy - x), (cx - y, cy - x),
            ]:
                if self._in_bounds(px, py):
                    self._pixels[py][px] = rgba
            if d < 0:
                d += 4 * x + 6
            else:
                d += 4 * (x - y) + 10
                y -= 1
            x += 1
        return self

    def fill_circle(self, cx: int, cy: int, r: int, color: ColorLike) -> "PixelCanvas":
        """Draw a filled circle.

        Example:
            >>> c.fill_circle(16, 16, 6, "red")
        """
        rgba = self._resolve(color)
        for py in range(max(0, cy - r), min(self.height, cy + r + 1)):
            for px in range(max(0, cx - r), min(self.width, cx + r + 1)):
                if (px - cx) ** 2 + (py - cy) ** 2 <= r ** 2:
                    self._pixels[py][px] = rgba
        return self

    def draw_line(self, x1: int, y1: int, x2: int, y2: int, color: ColorLike) -> "PixelCanvas":
        """Draw a line using Bresenham's algorithm.

        Example:
            >>> c.draw_line(0, 0, 31, 31, "white")  # diagonal
        """
        rgba = self._resolve(color)
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy
        while True:
            if self._in_bounds(x1, y1):
                self._pixels[y1][x1] = rgba
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy
        return self

    def flood_fill(self, x: int, y: int, color: ColorLike) -> "PixelCanvas":
        """Flood fill (bucket fill) from a starting pixel.

        Fills all connected pixels of the same color.

        Example:
            >>> c.flood_fill(0, 0, "blue")  # fill background
        """
        if not self._in_bounds(x, y):
            return self
        target = self._pixels[y][x]
        rgba = self._resolve(color)
        if target == rgba:
            return self
        stack = [(x, y)]
        while stack:
            px, py = stack.pop()
            if not self._in_bounds(px, py) or self._pixels[py][px] != target:
                continue
            self._pixels[py][px] = rgba
            stack.extend([(px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)])
        return self

    # ==================== Transforms ====================

    def mirror_x(self) -> "PixelCanvas":
        """Mirror the canvas horizontally (flip left-right).

        Example:
            >>> c.mirror_x()  # left side mirrors to right
        """
        for y in range(self.height):
            self._pixels[y] = self._pixels[y][::-1]
        return self

    def mirror_y(self) -> "PixelCanvas":
        """Mirror the canvas vertically (flip top-bottom)."""
        self._pixels = self._pixels[::-1]
        return self

    def copy_half_x(self) -> "PixelCanvas":
        """Copy the left half to the right half (for symmetrical sprites).

        Useful for creating symmetrical characters: draw the left half,
        then call this to mirror it to the right.

        Example:
            >>> c.fill_rect(0, 4, 8, 8, "blue")  # draw left half
            >>> c.copy_half_x()                    # mirror to right
        """
        mid = self.width // 2
        for y in range(self.height):
            for x in range(mid):
                self._pixels[y][self.width - 1 - x] = self._pixels[y][x]
        return self

    def shift(self, dx: int, dy: int) -> "PixelCanvas":
        """Shift all pixels by (dx, dy). Pixels that go out of bounds are lost.

        Example:
            >>> c.shift(0, -2)  # shift everything up by 2 pixels
        """
        new_pixels = [[TRANSPARENT for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                nx, ny = x + dx, y + dy
                if self._in_bounds(nx, ny):
                    new_pixels[ny][nx] = self._pixels[y][x]
        self._pixels = new_pixels
        return self

    # ==================== Shaded Drawing ====================

    def fill_rect_shaded(
        self, x: int, y: int, w: int, h: int, base_color: Color,
        light_dir: str = "top_left",
    ) -> "PixelCanvas":
        """Draw a rectangle with automatic 3-tone shading.

        Creates volume by applying highlight on the light-facing edge,
        mid-tone in the center, and shadow on the opposite edge.
        This is the core technique that makes pixel art look professional.

        Args:
            x, y, w, h: Rectangle position and size.
            base_color: RGB tuple for the mid-tone.
            light_dir: Light direction ("top_left" default).

        Example:
            >>> c.fill_rect_shaded(4, 4, 16, 12, (100, 100, 200))
        """
        ramp = color_ramp(base_color, 5)
        deep_shadow, shadow_c, base, highlight, bright = ramp

        # Fill base
        for py in range(max(0, y), min(self.height, y + h)):
            for px in range(max(0, x), min(self.width, x + w)):
                self._pixels[py][px] = (*base, 255)

        if w < 3 or h < 3:
            return self

        # Top edge = highlight (light from top-left)
        for px in range(max(0, x), min(self.width, x + w)):
            if self._in_bounds(px, y):
                self._pixels[y][px] = (*highlight, 255)
            if h > 4 and self._in_bounds(px, y + 1):
                self._pixels[y + 1][px] = (*highlight, 255)

        # Left edge = highlight
        for py in range(max(0, y), min(self.height, y + h)):
            if self._in_bounds(x, py):
                self._pixels[py][x] = (*highlight, 255)

        # Top-left corner = bright highlight (specular)
        if self._in_bounds(x + 1, y + 1):
            self._pixels[y + 1][x + 1] = (*bright, 255)
        if self._in_bounds(x, y):
            self._pixels[y][x] = (*bright, 255)

        # Bottom edge = shadow
        for px in range(max(0, x), min(self.width, x + w)):
            bot = y + h - 1
            if self._in_bounds(px, bot):
                self._pixels[bot][px] = (*shadow_c, 255)
            if h > 4 and self._in_bounds(px, bot - 1):
                self._pixels[bot - 1][px] = (*shadow_c, 255)

        # Right edge = shadow
        for py in range(max(0, y), min(self.height, y + h)):
            right = x + w - 1
            if self._in_bounds(right, py):
                self._pixels[py][right] = (*shadow_c, 255)

        # Bottom-right corner = deep shadow
        br_x, br_y = x + w - 1, y + h - 1
        if self._in_bounds(br_x, br_y):
            self._pixels[br_y][br_x] = (*deep_shadow, 255)
        if self._in_bounds(br_x - 1, br_y):
            self._pixels[br_y][br_x - 1] = (*deep_shadow, 255)
        if self._in_bounds(br_x, br_y - 1):
            self._pixels[br_y - 1][br_x] = (*deep_shadow, 255)

        return self

    def fill_circle_shaded(
        self, cx: int, cy: int, r: int, base_color: Color,
    ) -> "PixelCanvas":
        """Draw a filled circle with spherical shading.

        Applies radial shading: bright highlight offset toward light source,
        gradient falloff to shadow on the far side.

        Example:
            >>> c.fill_circle_shaded(16, 8, 6, (220, 180, 140))  # shaded head
        """
        ramp = color_ramp(base_color, 5)
        deep_shadow, shadow_c, base, highlight, bright = ramp

        # Light offset (top-left)
        lx, ly = cx - r * 0.3, cy - r * 0.3

        for py in range(max(0, cy - r), min(self.height, cy + r + 1)):
            for px in range(max(0, cx - r), min(self.width, cx + r + 1)):
                dx, dy = px - cx, py - cy
                dist_sq = dx * dx + dy * dy
                if dist_sq > r * r:
                    continue
                # Distance from light source (normalized 0-1)
                ldx, ldy = px - lx, py - ly
                light_dist = (ldx * ldx + ldy * ldy) ** 0.5 / (r * 2.2)
                light_dist = min(1.0, max(0.0, light_dist))

                if light_dist < 0.2:
                    c = bright
                elif light_dist < 0.4:
                    c = highlight
                elif light_dist < 0.65:
                    c = base
                elif light_dist < 0.85:
                    c = shadow_c
                else:
                    c = deep_shadow

                self._pixels[py][px] = (*c, 255)
        return self

    def colored_outline(self) -> "PixelCanvas":
        """Add colored outlines instead of black.

        Each outline pixel takes a darker version of its nearest
        non-transparent neighbor's color. This is the professional
        pixel art technique used in games like Celeste and Dead Cells.

        Example:
            >>> c.colored_outline()  # much better than .outline("black")
        """
        to_fill = {}
        for y in range(self.height):
            for x in range(self.width):
                if self._pixels[y][x][3] > 0:
                    for dy, dx in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                        nx, ny = x + dx, y + dy
                        if self._in_bounds(nx, ny) and self._pixels[ny][nx][3] == 0:
                            if (nx, ny) not in to_fill:
                                # Use the source pixel's color to derive outline
                                sr, sg, sb, _ = self._pixels[y][x]
                                outline_c = colored_outline((sr, sg, sb))
                                to_fill[(nx, ny)] = (*outline_c, 255)

        for (x, y), rgba in to_fill.items():
            self._pixels[y][x] = rgba
        return self

    # ==================== Effects ====================

    def outline(self, color: ColorLike, thickness: int = 1) -> "PixelCanvas":
        """Add an outline around all non-transparent pixels.

        This is the most important pixel art effect - it adds a dark border
        that makes sprites readable on any background.

        Args:
            color: Outline color (usually "black").
            thickness: Outline thickness in pixels (default 1).

        Example:
            >>> c.outline("black")  # standard 1px black outline
        """
        rgba = self._resolve(color)
        to_fill = set()
        for y in range(self.height):
            for x in range(self.width):
                if self._pixels[y][x][3] > 0:  # non-transparent pixel
                    for dy in range(-thickness, thickness + 1):
                        for dx in range(-thickness, thickness + 1):
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if self._in_bounds(nx, ny) and self._pixels[ny][nx][3] == 0:
                                to_fill.add((nx, ny))
        for x, y in to_fill:
            self._pixels[y][x] = rgba
        return self

    def shadow(self, color: ColorLike = (0, 0, 0, 80), dx: int = 1, dy: int = 1) -> "PixelCanvas":
        """Add a drop shadow to all non-transparent pixels.

        Args:
            color: Shadow color with alpha.
            dx, dy: Shadow offset.

        Example:
            >>> c.shadow()  # subtle default shadow
        """
        rgba = self._resolve(color) if not isinstance(color, tuple) or len(color) != 4 else color
        to_fill = []
        for y in range(self.height):
            for x in range(self.width):
                if self._pixels[y][x][3] > 0:
                    nx, ny = x + dx, y + dy
                    if self._in_bounds(nx, ny) and self._pixels[ny][nx][3] == 0:
                        to_fill.append((nx, ny))
        for x, y in to_fill:
            self._pixels[y][x] = rgba
        return self

    # ==================== Copy / Composite ====================

    def copy(self) -> "PixelCanvas":
        """Create a deep copy of this canvas.

        Example:
            >>> frame2 = c.copy().shift(0, -1)  # copy and shift up
        """
        new = PixelCanvas.__new__(PixelCanvas)
        new.width = self.width
        new.height = self.height
        new.palette = self.palette
        new._pixels = [row[:] for row in self._pixels]
        return new

    def paste(self, other: "PixelCanvas", x: int = 0, y: int = 0, transparent: bool = True) -> "PixelCanvas":
        """Paste another canvas onto this one.

        Args:
            other: Source canvas to paste.
            x, y: Position to paste at.
            transparent: If True, skip transparent pixels from source.

        Example:
            >>> bg.paste(character, 10, 5)
        """
        for sy in range(other.height):
            for sx in range(other.width):
                px, py = x + sx, y + sy
                if not self._in_bounds(px, py):
                    continue
                pixel = other._pixels[sy][sx]
                if transparent and pixel[3] == 0:
                    continue
                self._pixels[py][px] = pixel
        return self

    # ==================== Export ====================

    def to_image(self) -> Image.Image:
        """Convert to a PIL Image object."""
        img = Image.new("RGBA", (self.width, self.height))
        for y in range(self.height):
            for x in range(self.width):
                img.putpixel((x, y), self._pixels[y][x])
        return img

    def save(self, path: str, scale: int = 1) -> "PixelCanvas":
        """Save as PNG file.

        Args:
            path: Output file path (e.g., "sprite.png").
            scale: Integer upscale factor using nearest-neighbor.
                   Use scale=4 or scale=8 for preview images.

        Example:
            >>> c.save("character.png")          # 1x for game use
            >>> c.save("character_preview.png", scale=8)  # 8x for preview
        """
        img = self.to_image()
        if scale > 1:
            img = img.resize((self.width * scale, self.height * scale), Image.NEAREST)
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(p), "PNG")
        return self

    def __repr__(self) -> str:
        pal = f", palette={self.palette!r}" if self.palette else ""
        return f"PixelCanvas({self.width}x{self.height}{pal})"
