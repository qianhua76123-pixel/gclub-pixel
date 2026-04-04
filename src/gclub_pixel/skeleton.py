"""Skeletal animation system for layered pixel sprites.

Instead of shifting the entire sprite, this system transforms individual
body part layers (head bob, arm swing, leg walk, torso lean) to create
fluid, natural-looking animations based on the 12 principles of animation.

Works with CharacterBody's layered rendering: each body part is transformed
independently per frame, then composited.

Key animation principles implemented:
- Squash & Stretch: compress on impact, elongate during movement
- Anticipation: counter-movement before action
- Follow-through: delay after main action
- Ease in/out: slow start and end, fast middle

Example:
    >>> body = CharacterBody(64)
    >>> body.set_skin((220, 185, 145))
    >>> body.set_hair("short", (130, 90, 45))
    >>> body.set_armor("plate", (170, 175, 190))
    >>>
    >>> sa = SkeletalAnimation(body, fps=8)
    >>> sa.walk(frames=8)
    >>> sa.export_gif("knight_walk.gif", scale=4)
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

from gclub_pixel.canvas import PixelCanvas
from gclub_pixel.body import CharacterBody


class BoneTransform:
    """Transform applied to a body part layer for one frame.

    Attributes:
        dx, dy: Translation offset in pixels.
        scale_x, scale_y: Scale factors (1.0 = normal, <1 = squash, >1 = stretch).
        rotation: Rotation in degrees (only 0/90/180/270 for pixel-perfect).
    """

    def __init__(
        self,
        dx: int = 0,
        dy: int = 0,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
    ):
        self.dx = dx
        self.dy = dy
        self.scale_x = scale_x
        self.scale_y = scale_y


class FramePose:
    """A complete pose for one animation frame.

    Maps body part names to their transforms for this frame.
    """

    def __init__(self):
        self.transforms: Dict[str, BoneTransform] = {}

    def set(self, part: str, dx: int = 0, dy: int = 0,
            scale_x: float = 1.0, scale_y: float = 1.0) -> "FramePose":
        self.transforms[part] = BoneTransform(dx, dy, scale_x, scale_y)
        return self


def _ease_in_out(t: float) -> float:
    """Smooth ease-in-out curve (cubic)."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - (-2 * t + 2) ** 3 / 2


def _ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


def _bounce(t: float) -> float:
    """Bounce curve: high at 0.5, low at 0 and 1."""
    return math.sin(t * math.pi)


class SkeletalAnimation:
    """Skeletal animation system for CharacterBody.

    Creates frame-by-frame animations by applying per-part transforms
    to a CharacterBody's layered rendering.

    Args:
        body: CharacterBody instance.
        fps: Frames per second.

    Example:
        >>> sa = SkeletalAnimation(body, fps=8)
        >>> sa.idle(frames=6)
        >>> sa.export_gif("idle.gif", scale=4)
    """

    def __init__(self, body: CharacterBody, fps: int = 8):
        self.body = body
        self.fps = fps
        self.frames: List[PixelCanvas] = []
        self._poses: List[FramePose] = []

    def _render_frame(self, pose: FramePose) -> PixelCanvas:
        """Render a single frame with the given pose transforms."""
        s = self.body.size

        # First render the base body
        base = self.body.render()

        # Apply transforms by re-rendering with offsets
        result = PixelCanvas(s, s)

        # Get sorted parts
        sorted_parts = sorted(self.body._parts.values(), key=lambda p: p.z_order)

        for part in sorted_parts:
            t = pose.transforms.get(part.name, BoneTransform())

            if t.dx == 0 and t.dy == 0 and t.scale_x == 1.0 and t.scale_y == 1.0:
                # No transform, paste directly
                result.paste(part.canvas, part.anchor_x, part.anchor_y)
            else:
                # Apply translation
                ax = part.anchor_x + t.dx
                ay = part.anchor_y + t.dy

                if t.scale_x != 1.0 or t.scale_y != 1.0:
                    # Scale the part canvas
                    img = part.canvas.to_image()
                    new_w = max(1, round(part.canvas.width * t.scale_x))
                    new_h = max(1, round(part.canvas.height * t.scale_y))
                    img = img.resize((new_w, new_h), Image.NEAREST)
                    # Center the scaled image
                    offset_x = (part.canvas.width - new_w) // 2
                    offset_y = (part.canvas.height - new_h) // 2
                    temp = PixelCanvas(part.canvas.width, part.canvas.height)
                    for py in range(new_h):
                        for px in range(new_w):
                            r, g, b, a = img.getpixel((px, py))
                            if a > 0:
                                temp.set_pixel(px + offset_x, py + offset_y, (r, g, b, a))
                    result.paste(temp, ax, ay)
                else:
                    result.paste(part.canvas, ax, ay)

        # Re-apply colored outline on the composited result
        result.colored_outline()
        return result

    # ==================== Animation Presets ====================

    def idle(self, frames: int = 6, amplitude: int = 1) -> "SkeletalAnimation":
        """Breathing idle animation.

        Head and torso bob gently. Arms sway slightly.
        Uses ease-in-out for smooth organic motion.

        Args:
            frames: Number of frames (6-8 recommended).
            amplitude: Vertical bob range in pixels.

        Example:
            >>> sa.idle(frames=6)
        """
        self.frames = []
        self._poses = []
        a = amplitude

        for i in range(frames):
            t = i / frames
            ease = math.sin(t * 2 * math.pi)

            pose = FramePose()
            # Head bobs slightly
            pose.set("head", dy=round(ease * a))
            pose.set("hair", dy=round(ease * a))
            pose.set("face", dy=round(ease * a))
            # Torso breathes
            pose.set("torso", dy=round(ease * a * 0.5))
            # Arms follow torso with slight delay
            arm_ease = math.sin((t - 0.1) * 2 * math.pi)
            pose.set("front_arm", dy=round(arm_ease * a * 0.3))
            pose.set("back_arm", dy=round(arm_ease * a * 0.3))

            self._poses.append(pose)
            self.frames.append(self._render_frame(pose))
        return self

    def walk(self, frames: int = 8, stride: int = 2, bob: int = 1) -> "SkeletalAnimation":
        """Walking animation with arm swing and body bob.

        Alternating leg positions, opposite arm swing, and vertical bob.
        Follows the animation principle of overlap & offset.

        Args:
            frames: Frame count (8 recommended for smooth walk).
            stride: Horizontal leg movement range.
            bob: Vertical body bob amplitude.

        Example:
            >>> sa.walk(frames=8)
        """
        self.frames = []
        self._poses = []

        for i in range(frames):
            t = i / frames
            # Walk cycle: legs alternate, body bobs at double frequency
            leg_phase = math.sin(t * 2 * math.pi)
            body_bob = -abs(math.sin(t * 4 * math.pi)) * bob

            pose = FramePose()
            # Body bobs up at mid-stride
            pose.set("torso", dy=round(body_bob))

            # Head follows body with slight offset (overlap principle)
            head_bob = -abs(math.sin((t + 0.05) * 4 * math.pi)) * bob
            pose.set("head", dy=round(head_bob))
            pose.set("hair", dy=round(head_bob))
            pose.set("face", dy=round(head_bob))

            # Arms swing opposite to legs
            arm_swing = round(leg_phase * stride)
            pose.set("front_arm", dx=-arm_swing, dy=round(body_bob * 0.5))
            pose.set("back_arm", dx=arm_swing, dy=round(body_bob * 0.5))

            # Legs stride
            pose.set("legs", dy=round(body_bob * 0.3))

            self._poses.append(pose)
            self.frames.append(self._render_frame(pose))
        return self

    def attack(self, frames: int = 8) -> "SkeletalAnimation":
        """Melee attack animation with anticipation and follow-through.

        Phase 1: Wind-up (anticipation) - lean back
        Phase 2: Strike - lunge forward
        Phase 3: Recovery (follow-through) - settle back

        Example:
            >>> sa.attack(frames=8)
        """
        self.frames = []
        self._poses = []

        for i in range(frames):
            t = i / frames
            pose = FramePose()

            if t < 0.25:
                # Anticipation: lean back, pull arm back
                p = t / 0.25  # 0-1 within this phase
                ease = _ease_in_out(p)
                pose.set("torso", dx=round(-2 * ease))
                pose.set("head", dx=round(-1 * ease), dy=round(-1 * ease))
                pose.set("hair", dx=round(-1 * ease), dy=round(-1 * ease))
                pose.set("face", dx=round(-1 * ease), dy=round(-1 * ease))
                pose.set("front_arm", dx=round(-3 * ease), dy=round(-1 * ease))
                pose.set("back_arm", dx=round(-1 * ease))
            elif t < 0.5:
                # Strike: lunge forward fast
                p = (t - 0.25) / 0.25
                ease = _ease_out(p)
                pose.set("torso", dx=round(3 * ease - 2))
                pose.set("head", dx=round(2 * ease - 1))
                pose.set("hair", dx=round(2 * ease - 1))
                pose.set("face", dx=round(2 * ease - 1))
                pose.set("front_arm", dx=round(5 * ease - 3), dy=round(1 * ease))
                pose.set("back_arm", dx=round(1 * ease - 1))
                # Squash on contact
                if p > 0.7:
                    pose.set("torso", dx=round(3 * ease - 2), scale_x=1.05, scale_y=0.95)
            else:
                # Recovery: settle back to neutral
                p = (t - 0.5) / 0.5
                ease = _ease_in_out(p)
                remain = 1 - ease
                pose.set("torso", dx=round(1 * remain))
                pose.set("head", dx=round(1 * remain))
                pose.set("hair", dx=round(1 * remain))
                pose.set("face", dx=round(1 * remain))
                pose.set("front_arm", dx=round(2 * remain))

            self._poses.append(pose)
            self.frames.append(self._render_frame(pose))
        return self

    def jump(self, frames: int = 10, height: int = 6) -> "SkeletalAnimation":
        """Jump animation with squash, launch, airborne, and land.

        Follows classic squash-and-stretch principles:
        - Frame 1-2: Anticipation (crouch/squash)
        - Frame 3-6: Launch and peak (stretch upward)
        - Frame 7-9: Fall
        - Frame 10: Land (squash again)

        Example:
            >>> sa.jump(frames=10, height=6)
        """
        self.frames = []
        self._poses = []

        for i in range(frames):
            t = i / frames
            pose = FramePose()

            if t < 0.2:
                # Anticipation: squash down
                p = t / 0.2
                ease = _ease_in_out(p)
                dy = round(2 * ease)  # move down
                pose.set("head", dy=dy)
                pose.set("hair", dy=dy)
                pose.set("face", dy=dy)
                pose.set("torso", dy=dy, scale_x=1.1, scale_y=0.9)
                pose.set("front_arm", dy=dy)
                pose.set("back_arm", dy=dy)
                pose.set("legs", scale_y=0.85)
            elif t < 0.5:
                # Launch and rise
                p = (t - 0.2) / 0.3
                ease = _ease_out(p)
                dy = round(-height * ease + 2 * (1 - ease))
                pose.set("head", dy=dy)
                pose.set("hair", dy=dy)
                pose.set("face", dy=dy)
                pose.set("torso", dy=dy, scale_x=0.95, scale_y=1.08)
                pose.set("front_arm", dy=dy - 1)
                pose.set("back_arm", dy=dy - 1)
                pose.set("legs", dy=round(dy * 0.7))
            elif t < 0.8:
                # Peak and fall
                p = (t - 0.5) / 0.3
                ease = _ease_in_out(p)
                peak_dy = -height
                land_dy = 0
                dy = round(peak_dy + (land_dy - peak_dy) * ease)
                pose.set("head", dy=dy)
                pose.set("hair", dy=dy)
                pose.set("face", dy=dy)
                pose.set("torso", dy=dy)
                pose.set("front_arm", dy=dy + 1)
                pose.set("back_arm", dy=dy + 1)
                pose.set("legs", dy=round(dy * 0.8))
            else:
                # Land: squash
                p = (t - 0.8) / 0.2
                ease = _bounce(p)
                dy = round(2 * ease)
                pose.set("head", dy=dy)
                pose.set("hair", dy=dy)
                pose.set("face", dy=dy)
                pose.set("torso", dy=dy, scale_x=1.08, scale_y=0.92)
                pose.set("front_arm", dy=dy)
                pose.set("back_arm", dy=dy)

            self._poses.append(pose)
            self.frames.append(self._render_frame(pose))
        return self

    def hit(self, frames: int = 6) -> "SkeletalAnimation":
        """Damage/hit reaction animation.

        Quick knockback then recovery, with flash frames.

        Example:
            >>> sa.hit(frames=6)
        """
        self.frames = []
        self._poses = []

        for i in range(frames):
            t = i / frames
            pose = FramePose()

            if t < 0.3:
                # Knockback
                p = t / 0.3
                ease = _ease_out(p)
                pose.set("head", dx=round(-3 * ease), dy=round(-1 * ease))
                pose.set("hair", dx=round(-3 * ease), dy=round(-1 * ease))
                pose.set("face", dx=round(-3 * ease), dy=round(-1 * ease))
                pose.set("torso", dx=round(-2 * ease))
                pose.set("front_arm", dx=round(-2 * ease), dy=round(1 * ease))
                pose.set("back_arm", dx=round(-3 * ease))
            else:
                # Recovery
                p = (t - 0.3) / 0.7
                ease = _ease_in_out(p)
                remain = 1 - ease
                pose.set("head", dx=round(-3 * remain))
                pose.set("hair", dx=round(-3 * remain))
                pose.set("face", dx=round(-3 * remain))
                pose.set("torso", dx=round(-2 * remain))
                pose.set("front_arm", dx=round(-2 * remain))
                pose.set("back_arm", dx=round(-3 * remain))

            self._poses.append(pose)

            # Flash white on odd frames during knockback
            frame = self._render_frame(pose)
            if t < 0.3 and i % 2 == 1:
                for y in range(frame.height):
                    for x in range(frame.width):
                        if frame._pixels[y][x][3] > 0:
                            frame._pixels[y][x] = (255, 255, 255, 255)
            self.frames.append(frame)
        return self

    # ==================== Export ====================

    def export_gif(self, path: str, scale: int = 1, loop: bool = True) -> "SkeletalAnimation":
        """Export as animated GIF.

        Example:
            >>> sa.export_gif("walk.gif", scale=4)
        """
        if not self.frames:
            return self
        images = []
        for f in self.frames:
            img = f.to_image()
            if scale > 1:
                img = img.resize((f.width * scale, f.height * scale), Image.NEAREST)
            images.append(img)

        duration = int(1000 / self.fps)
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        images[0].save(str(p), save_all=True, append_images=images[1:],
                       duration=duration, loop=0 if loop else 1, disposal=2)
        return self

    def export_spritesheet(self, path: str, scale: int = 1) -> "SkeletalAnimation":
        """Export as horizontal spritesheet PNG."""
        if not self.frames:
            return self
        n = len(self.frames)
        fw, fh = self.frames[0].width, self.frames[0].height
        sheet = Image.new("RGBA", (fw * n, fh), (0, 0, 0, 0))
        for i, f in enumerate(self.frames):
            sheet.paste(f.to_image(), (i * fw, 0))
        if scale > 1:
            sheet = sheet.resize((fw * n * scale, fh * scale), Image.NEAREST)
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(str(p), "PNG")
        return self

    def __len__(self):
        return len(self.frames)

    def __repr__(self):
        return f"SkeletalAnimation({len(self.frames)} frames, {self.fps}fps)"
