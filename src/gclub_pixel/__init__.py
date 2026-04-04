"""gclub-pixel: LLM-friendly pixel art generation toolkit.

Write Python code, get game-ready sprites and animations.

Quick Start:
    >>> from gclub_pixel import PixelCanvas, Palette, Sprite, Animation
    >>>
    >>> # Draw a character
    >>> hero = Sprite.character(size=32, body_color="blue", hair_color="red")
    >>> hero.save("hero.png", scale=4)
    >>>
    >>> # Animate it
    >>> anim = Animation(hero, fps=8)
    >>> anim.idle(frames=4)
    >>> anim.export_gif("hero_idle.gif", scale=4)
"""

__version__ = "0.1.0"

from gclub_pixel.canvas import PixelCanvas
from gclub_pixel.palette import Palette, get_palette
from gclub_pixel.sprite import Sprite
from gclub_pixel.animation import Animation
from gclub_pixel.export import (
    export_spritesheet_with_meta,
    export_phaser_atlas,
    export_godot_spriteframes,
)

__all__ = [
    "PixelCanvas",
    "Palette",
    "get_palette",
    "Sprite",
    "Animation",
    "export_spritesheet_with_meta",
    "export_phaser_atlas",
    "export_godot_spriteframes",
]
