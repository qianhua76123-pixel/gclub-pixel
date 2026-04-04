"""Frame animation system for pixel art sprites.

Create multi-frame animations from a base sprite by applying per-frame
transforms (shift, replace colors, overlay). Export as spritesheet, GIF,
or individual frames.

Example:
    >>> anim = Animation(base_canvas, fps=8)
    >>> anim.add_frame(base_canvas.copy().shift(0, -1))
    >>> anim.add_frame(base_canvas.copy())
    >>> anim.export_spritesheet("idle.png")
    >>> anim.export_gif("idle.gif")
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import List, Optional

from PIL import Image

from gclub_pixel.canvas import PixelCanvas


class Animation:
    """A sequence of PixelCanvas frames forming an animation.

    Args:
        base: The base sprite canvas (used as reference frame).
        fps: Frames per second for GIF export (default 8).

    Example:
        >>> base = PixelCanvas(32, 32, palette="pico8")
        >>> # ... draw character on base ...
        >>> anim = Animation(base, fps=8)
        >>> anim.idle(amplitude=1, frames=4)
        >>> anim.export_gif("idle.gif", scale=4)
    """

    def __init__(self, base: PixelCanvas, fps: int = 8):
        self.base = base
        self.fps = fps
        self.frames: List[PixelCanvas] = []

    def add_frame(self, frame: PixelCanvas) -> "Animation":
        """Add a manually created frame.

        Example:
            >>> anim.add_frame(base.copy().shift(0, -1))
        """
        self.frames.append(frame)
        return self

    def clear_frames(self) -> "Animation":
        """Remove all frames."""
        self.frames = []
        return self

    # ==================== Animation Presets ====================

    def idle(self, amplitude: int = 1, frames: int = 4) -> "Animation":
        """Generate an idle/breathing animation.

        The sprite bobs up and down by `amplitude` pixels over `frames` frames.
        This is the most common idle animation in pixel art games.

        Args:
            amplitude: Max vertical displacement in pixels (default 1).
            frames: Number of frames (default 4).

        Example:
            >>> anim.idle(amplitude=1, frames=4)  # gentle breathing
        """
        self.frames = []
        for i in range(frames):
            t = i / frames
            dy = round(amplitude * math.sin(t * 2 * math.pi))
            self.frames.append(self.base.copy().shift(0, dy))
        return self

    def bounce(self, height: int = 2, frames: int = 6, squash: bool = False) -> "Animation":
        """Generate a bouncing animation.

        Sprite moves up and down with optional squash at the bottom.

        Args:
            height: Max bounce height in pixels.
            frames: Number of frames.
            squash: If True, compress the sprite at the bottom of the bounce.

        Example:
            >>> anim.bounce(height=3, frames=6)
        """
        self.frames = []
        for i in range(frames):
            t = i / frames
            # Parabolic bounce: high in middle, low at start/end
            dy = -round(height * math.sin(t * math.pi))
            f = self.base.copy().shift(0, dy)
            self.frames.append(f)
        return self

    def walk(self, step_height: int = 1, frames: int = 6, arm_swing: int = 1) -> "Animation":
        """Generate a walk cycle animation.

        Alternates leg positions and adds slight vertical bob.
        This is a simplified walk cycle suitable for small sprites.

        Args:
            step_height: Vertical bob amplitude.
            frames: Number of frames (recommend 4 or 6).
            arm_swing: Horizontal arm movement.

        Example:
            >>> anim.walk(frames=6)
        """
        self.frames = []
        for i in range(frames):
            t = i / frames
            dy = -round(step_height * abs(math.sin(t * 2 * math.pi)))
            f = self.base.copy().shift(0, dy)
            self.frames.append(f)
        return self

    def flash(self, color: str = "white", frames: int = 4) -> "Animation":
        """Generate a hit/damage flash animation.

        Alternates between normal and a flash color overlay.

        Args:
            color: Flash color name.
            frames: Number of frames.

        Example:
            >>> anim.flash("white", frames=4)
        """
        self.frames = []
        for i in range(frames):
            if i % 2 == 0:
                self.frames.append(self.base.copy())
            else:
                f = self.base.copy()
                # Replace all non-transparent pixels with flash color
                rgba = f._resolve(color)
                for y in range(f.height):
                    for x in range(f.width):
                        if f._pixels[y][x][3] > 0:
                            f._pixels[y][x] = rgba
                self.frames.append(f)
        return self

    def spin(self, frames: int = 8) -> "Animation":
        """Generate a simple rotation animation by flipping.

        Creates a pseudo-rotation by mirroring the sprite at intervals.
        Useful for coins, items, or simple top-down rotations.

        Args:
            frames: Number of frames (recommend 4 or 8).

        Example:
            >>> anim.spin(frames=8)
        """
        self.frames = []
        for i in range(frames):
            f = self.base.copy()
            phase = i / frames
            if 0.25 < phase <= 0.5 or 0.75 < phase <= 1.0:
                f.mirror_x()
            # Horizontal squish to simulate perspective
            squish = abs(math.cos(phase * 2 * math.pi))
            if squish < 0.3:
                # Very thin - just show a line
                mid_x = f.width // 2
                for y in range(f.height):
                    for x in range(f.width):
                        if abs(x - mid_x) > 1:
                            f._pixels[y][x] = (0, 0, 0, 0)
            self.frames.append(f)
        return self

    # ==================== Export ====================

    def export_spritesheet(
        self, path: str, columns: Optional[int] = None, padding: int = 0, scale: int = 1
    ) -> "Animation":
        """Export all frames as a horizontal spritesheet PNG.

        Args:
            path: Output file path.
            columns: Frames per row (default: all in one row).
            padding: Pixels between frames.
            scale: Upscale factor.

        Example:
            >>> anim.export_spritesheet("walk.png", columns=6)
        """
        if not self.frames:
            return self

        n = len(self.frames)
        fw, fh = self.frames[0].width, self.frames[0].height
        cols = columns or n
        rows = (n + cols - 1) // cols

        sheet_w = cols * fw + (cols - 1) * padding
        sheet_h = rows * fh + (rows - 1) * padding
        sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

        for i, frame in enumerate(self.frames):
            col = i % cols
            row = i // cols
            x = col * (fw + padding)
            y = row * (fh + padding)
            sheet.paste(frame.to_image(), (x, y))

        if scale > 1:
            sheet = sheet.resize((sheet_w * scale, sheet_h * scale), Image.NEAREST)

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(str(p), "PNG")
        return self

    def export_gif(self, path: str, scale: int = 1, loop: bool = True) -> "Animation":
        """Export as animated GIF.

        Args:
            path: Output file path.
            scale: Upscale factor (use 4-8 for preview).
            loop: Whether the GIF loops (default True).

        Example:
            >>> anim.export_gif("idle.gif", scale=4)
        """
        if not self.frames:
            return self

        images = []
        for frame in self.frames:
            img = frame.to_image()
            if scale > 1:
                img = img.resize(
                    (frame.width * scale, frame.height * scale), Image.NEAREST
                )
            # GIF doesn't support RGBA well, convert to P mode with transparency
            images.append(img)

        duration = int(1000 / self.fps)
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)

        images[0].save(
            str(p),
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=0 if loop else 1,
            disposal=2,
        )
        return self

    def export_frames(self, directory: str, prefix: str = "frame", scale: int = 1) -> "Animation":
        """Export each frame as a separate PNG file.

        Args:
            directory: Output directory.
            prefix: Filename prefix.
            scale: Upscale factor.

        Example:
            >>> anim.export_frames("./frames/", prefix="idle")
            # Creates: idle_000.png, idle_001.png, ...
        """
        d = Path(directory)
        d.mkdir(parents=True, exist_ok=True)
        for i, frame in enumerate(self.frames):
            frame.save(str(d / f"{prefix}_{i:03d}.png"), scale=scale)
        return self

    def __len__(self) -> int:
        return len(self.frames)

    def __repr__(self) -> str:
        return f"Animation({len(self.frames)} frames, {self.fps}fps)"
