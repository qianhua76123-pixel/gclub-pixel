"""High-level sprite generation templates.

Provides preset character and object generators that LLMs can call
with simple parameters to create game-ready sprites.

Example:
    >>> char = Sprite.character(size=32, body_color="blue", hair_color="red")
    >>> char.save("hero.png", scale=4)
    >>> sword = Sprite.weapon("sword", size=16)
    >>> potion = Sprite.item("potion", color="red", size=16)
"""

from __future__ import annotations

from typing import Optional

from gclub_pixel.canvas import PixelCanvas
from gclub_pixel.palette import Palette, ColorLike


class Sprite:
    """Factory class for generating common game sprite types.

    All methods are static and return a PixelCanvas that can be
    further modified, animated, or saved directly.
    """

    @staticmethod
    def character(
        size: int = 32,
        palette: str = "pico8",
        skin_color: ColorLike = "peach",
        hair_color: ColorLike = "brown",
        body_color: ColorLike = "blue",
        pants_color: ColorLike = "indigo",
        eye_color: ColorLike = "dark_blue",
        outline_color: ColorLike = "black",
        style: str = "chibi",
    ) -> PixelCanvas:
        """Generate a character sprite with basic body parts.

        Creates a simple front-facing character with head, body, arms, legs.
        The proportions adapt to the requested style.

        Args:
            size: Sprite size in pixels (16, 24, 32, or 48 recommended).
            palette: Palette name.
            skin_color: Skin/face color name.
            hair_color: Hair color name.
            body_color: Torso/shirt color name.
            pants_color: Leg/pants color name.
            eye_color: Eye color name.
            outline_color: Outline color name. Set to None to skip.
            style: Body proportions. "chibi" (big head), "tall", or "squat".

        Returns:
            PixelCanvas with the character drawn.

        Example:
            >>> hero = Sprite.character(size=32, body_color="red", hair_color="yellow")
            >>> hero.save("hero.png", scale=4)
        """
        c = PixelCanvas(size, size, palette=palette)
        u = max(1, size // 16)  # base unit scales with size

        if style == "chibi":
            _draw_chibi(c, u, skin_color, hair_color, body_color, pants_color, eye_color)
        elif style == "tall":
            _draw_tall(c, u, skin_color, hair_color, body_color, pants_color, eye_color)
        else:
            _draw_chibi(c, u, skin_color, hair_color, body_color, pants_color, eye_color)

        if outline_color is not None:
            c.outline(outline_color)

        return c

    @staticmethod
    def weapon(
        weapon_type: str = "sword",
        size: int = 16,
        palette: str = "pico8",
        blade_color: ColorLike = "light_gray",
        handle_color: ColorLike = "brown",
        outline_color: ColorLike = "black",
    ) -> PixelCanvas:
        """Generate a weapon icon sprite.

        Args:
            weapon_type: "sword", "axe", "staff", "bow", "shield".
            size: Sprite size.
            palette: Palette name.
            blade_color: Main weapon color.
            handle_color: Handle/grip color.
            outline_color: Outline color.

        Example:
            >>> sword = Sprite.weapon("sword", blade_color="light_gray")
            >>> sword.save("sword.png", scale=4)
        """
        c = PixelCanvas(size, size, palette=palette)
        u = max(1, size // 16)

        if weapon_type == "sword":
            _draw_sword(c, u, blade_color, handle_color)
        elif weapon_type == "axe":
            _draw_axe(c, u, blade_color, handle_color)
        elif weapon_type == "staff":
            _draw_staff(c, u, blade_color, handle_color)
        elif weapon_type == "shield":
            _draw_shield(c, u, blade_color, handle_color)
        else:
            _draw_sword(c, u, blade_color, handle_color)

        if outline_color is not None:
            c.outline(outline_color)
        return c

    @staticmethod
    def item(
        item_type: str = "potion",
        size: int = 16,
        palette: str = "pico8",
        color: ColorLike = "red",
        outline_color: ColorLike = "black",
    ) -> PixelCanvas:
        """Generate an item icon sprite.

        Args:
            item_type: "potion", "coin", "gem", "heart", "key", "chest".
            size: Sprite size.
            palette: Palette name.
            color: Main item color.
            outline_color: Outline color.

        Example:
            >>> hp = Sprite.item("potion", color="red")
            >>> hp.save("hp_potion.png", scale=4)
        """
        c = PixelCanvas(size, size, palette=palette)
        u = max(1, size // 16)

        if item_type == "potion":
            _draw_potion(c, u, color)
        elif item_type == "coin":
            _draw_coin(c, u, color)
        elif item_type == "gem":
            _draw_gem(c, u, color)
        elif item_type == "heart":
            _draw_heart(c, u, color)
        elif item_type == "key":
            _draw_key(c, u, color)
        else:
            _draw_potion(c, u, color)

        if outline_color is not None:
            c.outline(outline_color)
        return c


# ==================== Internal Drawers ====================

def _draw_chibi(c: PixelCanvas, u: int, skin, hair, body, pants, eyes):
    """Draw a chibi-proportioned character (big head, small body)."""
    s = c.width
    mid = s // 2

    # Hair (top of head)
    c.fill_rect(mid - 4*u, 1*u, 8*u, 3*u, hair)
    c.fill_rect(mid - 5*u, 2*u, 10*u, 2*u, hair)

    # Head/face
    c.fill_rect(mid - 4*u, 3*u, 8*u, 6*u, skin)

    # Eyes
    c.fill_rect(mid - 3*u, 5*u, u, u, eyes)
    c.fill_rect(mid + 2*u, 5*u, u, u, eyes)

    # Body/torso
    c.fill_rect(mid - 4*u, 9*u, 8*u, 5*u, body)

    # Arms
    c.fill_rect(mid - 5*u, 9*u, u, 4*u, skin)
    c.fill_rect(mid + 4*u, 9*u, u, 4*u, skin)

    # Legs
    c.fill_rect(mid - 3*u, 14*u, 3*u, 2*u, pants)
    c.fill_rect(mid, 14*u, 3*u, 2*u, pants)


def _draw_tall(c: PixelCanvas, u: int, skin, hair, body, pants, eyes):
    """Draw a taller-proportioned character."""
    s = c.width
    mid = s // 2

    # Hair
    c.fill_rect(mid - 3*u, 0, 6*u, 2*u, hair)
    c.fill_rect(mid - 4*u, 1*u, 8*u, 2*u, hair)

    # Head
    c.fill_rect(mid - 3*u, 2*u, 6*u, 5*u, skin)

    # Eyes
    c.fill_rect(mid - 2*u, 4*u, u, u, eyes)
    c.fill_rect(mid + 1*u, 4*u, u, u, eyes)

    # Body
    c.fill_rect(mid - 3*u, 7*u, 6*u, 5*u, body)

    # Arms
    c.fill_rect(mid - 4*u, 7*u, u, 4*u, skin)
    c.fill_rect(mid + 3*u, 7*u, u, 4*u, skin)

    # Legs
    c.fill_rect(mid - 2*u, 12*u, 2*u, 4*u, pants)
    c.fill_rect(mid, 12*u, 2*u, 4*u, pants)


def _draw_sword(c: PixelCanvas, u: int, blade, handle):
    s = c.width
    mid = s // 2
    # Blade (diagonal from top-right to center)
    for i in range(6):
        c.fill_rect(mid + (3-i)*u, (1+i)*u, u, u, blade)
        if i > 0:
            c.fill_rect(mid + (4-i)*u, (1+i)*u, u, u, blade)
    # Guard
    c.fill_rect(mid - 2*u, 7*u, 5*u, u, handle)
    # Handle
    c.fill_rect(mid, 8*u, u, 4*u, handle)
    # Pommel
    c.fill_rect(mid - u//2, 12*u, u + u//2, u, handle)


def _draw_axe(c: PixelCanvas, u: int, blade, handle):
    s = c.width
    mid = s // 2
    # Handle
    c.fill_rect(mid, 2*u, u, 12*u, handle)
    # Blade head
    c.fill_rect(mid - 3*u, 2*u, 4*u, 5*u, blade)


def _draw_staff(c: PixelCanvas, u: int, orb, handle):
    s = c.width
    mid = s // 2
    # Staff pole
    c.fill_rect(mid, 3*u, u, 12*u, handle)
    # Orb on top
    c.fill_circle(mid, 2*u, 2*u, orb)


def _draw_shield(c: PixelCanvas, u: int, main, trim):
    s = c.width
    mid = s // 2
    # Shield body
    c.fill_rect(mid - 4*u, 2*u, 8*u, 10*u, main)
    # Trim
    c.draw_rect(mid - 4*u, 2*u, 8*u, 10*u, trim)
    # Emblem (cross)
    c.fill_rect(mid - u//2, 4*u, u, 6*u, trim)
    c.fill_rect(mid - 2*u, 6*u, 4*u, u, trim)


def _draw_potion(c: PixelCanvas, u: int, color):
    s = c.width
    mid = s // 2
    # Cork
    c.fill_rect(mid - u, 2*u, 2*u, 2*u, "brown")
    # Neck
    c.fill_rect(mid - u, 4*u, 2*u, 2*u, "light_gray")
    # Body
    c.fill_rect(mid - 3*u, 6*u, 6*u, 7*u, color)
    # Highlight
    c.fill_rect(mid - 2*u, 7*u, u, 2*u, "white")


def _draw_coin(c: PixelCanvas, u: int, color):
    s = c.width
    mid = s // 2
    c.fill_circle(mid, mid, 5*u, color)
    c.draw_circle(mid, mid, 5*u, "brown")
    # Dollar sign or symbol
    c.fill_rect(mid - u//2, mid - 2*u, u, 4*u, "white")


def _draw_gem(c: PixelCanvas, u: int, color):
    s = c.width
    mid = s // 2
    # Diamond shape
    for i in range(4):
        c.fill_rect(mid - i*u - u, mid - (4-i)*u, (2*i+2)*u, u, color)
    for i in range(4):
        c.fill_rect(mid - (3-i)*u - u, mid + i*u, (2*(3-i)+2)*u, u, color)
    # Highlight
    c.fill_rect(mid - u, mid - 2*u, u, u, "white")


def _draw_heart(c: PixelCanvas, u: int, color):
    s = c.width
    mid = s // 2
    # Heart shape using circles + triangle
    c.fill_circle(mid - 2*u, 5*u, 3*u, color)
    c.fill_circle(mid + 2*u, 5*u, 3*u, color)
    # Bottom triangle
    for i in range(5):
        w = 5 - i
        c.fill_rect(mid - w*u, 7*u + i*u, 2*w*u, u, color)


def _draw_key(c: PixelCanvas, u: int, color):
    s = c.width
    mid = s // 2
    # Key head (circle)
    c.draw_circle(mid - 2*u, 5*u, 3*u, color)
    # Shaft
    c.fill_rect(mid, 5*u, 6*u, u, color)
    # Teeth
    c.fill_rect(mid + 4*u, 5*u, u, 3*u, color)
    c.fill_rect(mid + 6*u, 5*u, u, 2*u, color)
