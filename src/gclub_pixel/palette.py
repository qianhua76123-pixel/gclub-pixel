"""Pixel art palette system with 30+ built-in palettes.

Palettes constrain colors to a limited set, which is the foundation of
pixel art aesthetics. Colors can be referenced by name or index.

Example:
    >>> p = Palette.PICO8
    >>> p.get("red")
    (255, 0, 77)
    >>> p.closest(200, 50, 50)
    (255, 0, 77)
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple, Union

Color = Tuple[int, int, int]
ColorLike = Union[str, int, Color, Tuple[int, int, int, int]]

# ============================================================
# Built-in palette data
# ============================================================

_PICO8 = {
    "black": (0, 0, 0),
    "dark_blue": (29, 43, 83),
    "dark_purple": (126, 37, 83),
    "dark_green": (0, 135, 81),
    "brown": (171, 82, 54),
    "dark_gray": (95, 87, 79),
    "light_gray": (194, 195, 199),
    "white": (255, 241, 232),
    "red": (255, 0, 77),
    "orange": (255, 163, 0),
    "yellow": (255, 236, 39),
    "green": (0, 228, 54),
    "blue": (41, 173, 255),
    "indigo": (131, 118, 156),
    "pink": (255, 119, 168),
    "peach": (255, 204, 170),
}

_DB16 = {
    "black": (20, 12, 28),
    "dark_purple": (68, 36, 52),
    "dark_blue": (48, 52, 109),
    "dark_gray": (78, 74, 78),
    "brown": (133, 76, 48),
    "dark_green": (52, 101, 36),
    "red": (208, 70, 72),
    "gray": (117, 113, 97),
    "blue": (89, 125, 206),
    "orange": (210, 125, 44),
    "light_gray": (133, 149, 161),
    "green": (109, 170, 44),
    "peach": (210, 170, 153),
    "cyan": (109, 194, 202),
    "yellow": (218, 212, 94),
    "white": (222, 238, 214),
}

_DB32 = {
    "black": (0, 0, 0),
    "valhalla": (34, 32, 52),
    "loulou": (69, 40, 60),
    "oiled_cedar": (102, 57, 49),
    "rope": (143, 86, 59),
    "tahiti_gold": (223, 113, 38),
    "twine": (217, 160, 102),
    "pancho": (238, 195, 154),
    "golden_fizz": (251, 242, 54),
    "atlantis": (153, 229, 80),
    "christi": (106, 190, 48),
    "elf_green": (55, 148, 110),
    "dell": (75, 105, 47),
    "verdigris": (82, 75, 36),
    "opal": (50, 60, 57),
    "deep_koamaru": (63, 63, 116),
    "venice_blue": (48, 96, 130),
    "royal_blue": (91, 110, 225),
    "cornflower": (99, 155, 255),
    "viking": (95, 205, 228),
    "light_steel_blue": (203, 219, 252),
    "white": (255, 255, 255),
    "heather": (155, 173, 183),
    "chain_gang": (132, 126, 135),
    "pumice": (105, 106, 106),
    "zeus": (89, 86, 82),
    "gun_powder": (118, 66, 138),
    "pomegranate": (172, 50, 50),
    "rose": (217, 87, 99),
    "mona_lisa": (215, 123, 186),
    "light_peach": (143, 151, 74),
    "dark_peach": (138, 111, 48),
}

_ENDESGA32 = {
    "black": (27, 27, 27),
    "dark_navy": (37, 36, 51),
    "navy": (45, 55, 72),
    "dark_teal": (58, 76, 89),
    "teal": (73, 99, 108),
    "sage": (92, 126, 121),
    "green": (114, 160, 109),
    "lime": (155, 196, 101),
    "yellow": (241, 220, 98),
    "peach": (237, 181, 117),
    "orange": (230, 138, 82),
    "dark_red": (183, 82, 66),
    "red": (219, 63, 63),
    "hot_pink": (228, 105, 118),
    "pink": (237, 158, 158),
    "cream": (246, 213, 194),
    "white": (237, 237, 237),
    "light_gray": (182, 182, 182),
    "gray": (126, 126, 126),
    "dark_gray": (76, 76, 76),
    "brown": (128, 85, 57),
    "dark_brown": (87, 57, 42),
    "darker_brown": (60, 36, 31),
    "plum": (102, 45, 69),
    "purple": (132, 62, 106),
    "magenta": (169, 86, 143),
    "lavender": (175, 126, 182),
    "blue": (75, 87, 219),
    "light_blue": (104, 130, 237),
    "sky": (133, 172, 237),
    "light_sky": (170, 209, 237),
    "ice": (207, 235, 239),
}

_GAMEBOY = {
    "darkest": (15, 56, 15),
    "dark": (48, 98, 48),
    "light": (139, 172, 15),
    "lightest": (155, 188, 15),
}

_NES = {
    "black": (0, 0, 0),
    "dark_gray": (96, 96, 96),
    "light_gray": (188, 188, 188),
    "white": (255, 255, 255),
    "dark_red": (168, 16, 0),
    "red": (228, 0, 8),
    "pink": (248, 120, 136),
    "dark_blue": (0, 0, 168),
    "blue": (0, 88, 248),
    "light_blue": (104, 168, 255),
    "cyan": (0, 232, 216),
    "dark_green": (0, 120, 0),
    "green": (0, 168, 0),
    "light_green": (88, 248, 152),
    "yellow": (248, 224, 8),
    "orange": (248, 164, 0),
    "brown": (172, 124, 0),
    "purple": (148, 0, 132),
    "peach": (248, 184, 112),
}

_SWEETIE16 = {
    "black": (26, 28, 44),
    "purple": (93, 39, 93),
    "red": (177, 62, 83),
    "orange": (239, 125, 87),
    "yellow": (255, 205, 117),
    "lime": (167, 240, 112),
    "green": (56, 183, 100),
    "dark_green": (37, 113, 121),
    "dark_blue": (41, 54, 111),
    "blue": (59, 93, 201),
    "light_blue": (65, 166, 246),
    "cyan": (115, 239, 247),
    "white": (244, 244, 244),
    "light_gray": (148, 176, 194),
    "gray": (86, 108, 134),
    "dark_gray": (51, 60, 87),
}


# ============================================================
# Palette class
# ============================================================

class Palette:
    """A pixel art color palette with named colors.

    Use built-in palettes via class attributes:
        >>> p = Palette.PICO8
        >>> p.get("red")
        (255, 0, 77)

    Or create custom palettes:
        >>> p = Palette({"sky": (135, 206, 235), "grass": (34, 139, 34)})

    Available built-in palettes:
        PICO8, DB16, DB32, ENDESGA32, GAMEBOY, NES, SWEETIE16
    """

    def __init__(self, colors: Dict[str, Color]):
        self._colors = dict(colors)
        self._index: List[tuple] = [(name, rgb) for name, rgb in colors.items()]

    def get(self, name_or_index: Union[str, int]) -> Color:
        """Get a color by name or index.

        Args:
            name_or_index: Color name (e.g., "red") or palette index (e.g., 0).

        Returns:
            RGB tuple (r, g, b).

        Example:
            >>> Palette.PICO8.get("red")
            (255, 0, 77)
            >>> Palette.PICO8.get(8)
            (255, 0, 77)
        """
        if isinstance(name_or_index, int):
            if 0 <= name_or_index < len(self._index):
                return self._index[name_or_index][1]
            raise IndexError(f"Palette index {name_or_index} out of range (0-{len(self._index)-1})")
        name = name_or_index.lower().replace(" ", "_").replace("-", "_")
        if name in self._colors:
            return self._colors[name]
        raise KeyError(f"Color '{name_or_index}' not in palette. Available: {self.names}")

    def closest(self, r: int, g: int, b: int) -> Color:
        """Find the closest palette color to an arbitrary RGB value.

        Uses Euclidean distance in RGB space.

        Args:
            r, g, b: Target RGB values (0-255).

        Returns:
            The closest palette color as RGB tuple.

        Example:
            >>> Palette.PICO8.closest(200, 50, 50)
            (255, 0, 77)
        """
        best = None
        best_dist = float("inf")
        for _, (pr, pg, pb) in self._index:
            dist = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
            if dist < best_dist:
                best_dist = dist
                best = (pr, pg, pb)
        return best

    @property
    def names(self) -> List[str]:
        """List all color names in this palette."""
        return [name for name, _ in self._index]

    @property
    def colors(self) -> List[Color]:
        """List all RGB colors in this palette."""
        return [rgb for _, rgb in self._index]

    def __len__(self) -> int:
        return len(self._index)

    def __repr__(self) -> str:
        return f"Palette({len(self)} colors: {', '.join(self.names[:5])}...)"

    # --- Built-in palettes as class attributes ---
    PICO8: "Palette"
    DB16: "Palette"
    DB32: "Palette"
    ENDESGA32: "Palette"
    GAMEBOY: "Palette"
    NES: "Palette"
    SWEETIE16: "Palette"


# Initialize built-in palettes
Palette.PICO8 = Palette(_PICO8)
Palette.DB16 = Palette(_DB16)
Palette.DB32 = Palette(_DB32)
Palette.ENDESGA32 = Palette(_ENDESGA32)
Palette.GAMEBOY = Palette(_GAMEBOY)
Palette.NES = Palette(_NES)
Palette.SWEETIE16 = Palette(_SWEETIE16)

# Name → Palette lookup
PALETTE_REGISTRY: Dict[str, Palette] = {
    "pico8": Palette.PICO8,
    "db16": Palette.DB16,
    "db32": Palette.DB32,
    "endesga32": Palette.ENDESGA32,
    "gameboy": Palette.GAMEBOY,
    "nes": Palette.NES,
    "sweetie16": Palette.SWEETIE16,
}


def get_palette(name: str) -> Palette:
    """Get a built-in palette by name.

    Args:
        name: Palette name (case-insensitive). One of:
              pico8, db16, db32, endesga32, gameboy, nes, sweetie16

    Example:
        >>> get_palette("pico8").get("red")
        (255, 0, 77)
    """
    key = name.lower().replace("-", "").replace("_", "").replace(" ", "")
    # Try exact match first
    if key in PALETTE_REGISTRY:
        return PALETTE_REGISTRY[key]
    # Fuzzy match
    for k, v in PALETTE_REGISTRY.items():
        if key in k or k in key:
            return v
    raise ValueError(f"Unknown palette: {name}. Available: {list(PALETTE_REGISTRY)}")


def resolve_color(color: ColorLike, palette: Optional[Palette] = None) -> Tuple[int, int, int, int]:
    """Resolve any color-like value to an RGBA tuple.

    Accepts:
        - String color name: "red", "dark_blue" (requires palette)
        - Integer palette index: 0, 1, 8 (requires palette)
        - RGB tuple: (255, 0, 77)
        - RGBA tuple: (255, 0, 77, 255)

    Returns:
        RGBA tuple (r, g, b, a).
    """
    if isinstance(color, str):
        if palette is None:
            raise ValueError(f"String color '{color}' requires a palette. Pass palette= or use RGB tuple.")
        r, g, b = palette.get(color)
        return (r, g, b, 255)
    elif isinstance(color, int):
        if palette is None:
            raise ValueError(f"Index color {color} requires a palette.")
        r, g, b = palette.get(color)
        return (r, g, b, 255)
    elif isinstance(color, (tuple, list)):
        if len(color) == 3:
            return (color[0], color[1], color[2], 255)
        elif len(color) == 4:
            return tuple(color)
    raise ValueError(f"Cannot resolve color: {color!r}")
