"""Layered body parts system for detailed character sprites.

Characters are built from independent layers (head, hair, torso, arms, legs,
equipment) that can be separately drawn, shaded, and animated. This is the
"paper doll" approach used in games like Stardew Valley and Terraria.

Each body part is its own PixelCanvas, composited together at render time.
This enables:
- Swapping equipment without redrawing the character
- Animating individual limbs (arm swing, leg walk)
- Much higher detail at 48x48 and 64x64

Example:
    >>> body = CharacterBody(size=64, palette="endesga32")
    >>> body.set_skin((215, 175, 135))
    >>> body.set_hair("spiky", color=(140, 70, 30))
    >>> body.set_armor("plate", color=(170, 175, 185))
    >>> body.set_weapon("sword")
    >>> result = body.render()
    >>> result.save("knight_64.png", scale=4)
"""

from __future__ import annotations

import math
from typing import Optional, Tuple, Dict, List

from gclub_pixel.canvas import PixelCanvas
from gclub_pixel.palette import Color, color_ramp, shade, colored_outline


class BodyPart:
    """A single body part layer with its own canvas and anchor point."""

    def __init__(self, name: str, width: int, height: int, anchor_x: int = 0, anchor_y: int = 0):
        self.name = name
        self.canvas = PixelCanvas(width, height)
        self.anchor_x = anchor_x  # attachment point relative to body origin
        self.anchor_y = anchor_y
        self.z_order = 0  # drawing order (higher = on top)

    def clear(self):
        self.canvas.clear()
        return self


class CharacterBody:
    """Layered character body with detailed shading.

    Builds a character from separate body parts, each independently
    drawable and animatable. Supports sizes 32, 48, 64.

    Args:
        size: Character sprite size (32, 48, or 64).

    Example:
        >>> body = CharacterBody(64)
        >>> body.set_skin((215, 175, 135))
        >>> body.set_hair("messy", (100, 60, 30))
        >>> body.set_armor("leather", (130, 90, 50))
        >>> sprite = body.render()
        >>> sprite.save("char.png", scale=4)
    """

    def __init__(self, size: int = 64):
        self.size = size
        self.u = size / 64.0  # unit scale factor (1.0 at 64px)
        self._skin: Color = (215, 175, 135)
        self._parts: Dict[str, BodyPart] = {}
        self._init_parts()

    def _s(self, v: float) -> int:
        """Scale a 64px-base value to current size."""
        return max(1, round(v * self.u))

    def _init_parts(self):
        s = self.size
        # Create all body part layers
        self._parts = {
            "shadow": BodyPart("shadow", s, s, 0, 0),
            "back_arm": BodyPart("back_arm", s, s, 0, 0),
            "legs": BodyPart("legs", s, s, 0, 0),
            "torso": BodyPart("torso", s, s, 0, 0),
            "front_arm": BodyPart("front_arm", s, s, 0, 0),
            "head": BodyPart("head", s, s, 0, 0),
            "hair": BodyPart("hair", s, s, 0, 0),
            "face": BodyPart("face", s, s, 0, 0),
            "equipment": BodyPart("equipment", s, s, 0, 0),
        }
        # Z-order
        for i, name in enumerate(["shadow", "back_arm", "legs", "torso", "front_arm", "head", "hair", "face", "equipment"]):
            self._parts[name].z_order = i

    def set_skin(self, color: Color) -> "CharacterBody":
        """Set skin color. Affects head, arms, and hands."""
        self._skin = color
        return self

    def set_hair(self, style: str = "messy", color: Color = (100, 60, 30)) -> "CharacterBody":
        """Set hair style and color.

        Styles: "messy", "spiky", "long", "short", "ponytail", "bald"

        Example:
            >>> body.set_hair("spiky", (200, 50, 30))  # red spiky hair
        """
        p = self._parts["hair"].canvas
        p.clear()
        r = color_ramp(color, 5)
        mid = self.size // 2

        if style == "spiky":
            self._draw_spiky_hair(p, mid, r)
        elif style == "long":
            self._draw_long_hair(p, mid, r)
        elif style == "ponytail":
            self._draw_ponytail_hair(p, mid, r)
        elif style == "short":
            self._draw_short_hair(p, mid, r)
        elif style == "bald":
            pass  # no hair drawn
        else:  # messy
            self._draw_messy_hair(p, mid, r)
        return self

    def set_armor(self, style: str = "leather", color: Color = (130, 100, 60)) -> "CharacterBody":
        """Set armor/clothing on the torso.

        Styles: "cloth", "leather", "chain", "plate", "robe"

        Example:
            >>> body.set_armor("plate", (165, 170, 185))  # silver plate
        """
        self._armor_style = style
        self._armor_color = color
        return self

    def set_weapon(self, weapon: str = "none") -> "CharacterBody":
        """Set held weapon. Drawn on the equipment layer.

        Weapons: "none", "sword", "axe", "staff", "bow", "shield"
        """
        self._weapon = weapon
        return self

    def set_eyes(self, color: Color = (40, 50, 80), style: str = "normal") -> "CharacterBody":
        """Set eye color and style.

        Styles: "normal", "narrow", "wide", "angry", "happy"
        """
        self._eye_color = color
        self._eye_style = style
        return self

    def render(self) -> PixelCanvas:
        """Render all layers into a final composite sprite.

        Returns:
            PixelCanvas with the complete character.

        Example:
            >>> sprite = body.render()
            >>> sprite.save("character.png", scale=4)
        """
        s = self.size
        mid = s // 2

        skin = self._skin
        armor_color = getattr(self, '_armor_color', (130, 100, 60))
        armor_style = getattr(self, '_armor_style', 'leather')
        eye_color = getattr(self, '_eye_color', (40, 50, 80))
        eye_style = getattr(self, '_eye_style', 'normal')

        # Draw each body part on its layer
        self._draw_head(self._parts["head"].canvas, mid, skin)
        self._draw_face(self._parts["face"].canvas, mid, skin, eye_color, eye_style)
        self._draw_torso(self._parts["torso"].canvas, mid, armor_color, armor_style)
        self._draw_legs(self._parts["legs"].canvas, mid)
        self._draw_arms(self._parts["front_arm"].canvas, self._parts["back_arm"].canvas, mid, skin, armor_color)
        self._draw_ground_shadow(self._parts["shadow"].canvas, mid)

        # Composite all layers
        result = PixelCanvas(s, s)
        sorted_parts = sorted(self._parts.values(), key=lambda p: p.z_order)
        for part in sorted_parts:
            result.paste(part.canvas, part.anchor_x, part.anchor_y)

        # Final colored outline
        result.colored_outline()
        return result

    # ===================== Internal Drawers =====================

    def _px(self, canvas: PixelCanvas, x: int, y: int, color: Color):
        if 0 <= x < canvas.width and 0 <= y < canvas.height:
            canvas._pixels[y][x] = (*color, 255)

    def _draw_head(self, c: PixelCanvas, mid: int, skin: Color):
        """Draw head with spherical shading."""
        c.clear()
        r = color_ramp(skin, 5)
        head_r = self._s(10)
        head_cy = self._s(16)

        # Spherical head
        for py in range(head_cy - head_r, head_cy + head_r + 1):
            for px in range(mid - head_r, mid + head_r + 1):
                dx, dy = px - mid, py - head_cy
                if dx * dx + dy * dy > head_r * head_r:
                    continue
                # Light from top-left
                ldist = ((dx + head_r * 0.35) ** 2 + (dy + head_r * 0.35) ** 2) ** 0.5 / (head_r * 1.8)
                ldist = min(1.0, max(0.0, ldist))
                if ldist < 0.2:
                    self._px(c, px, py, r[4])
                elif ldist < 0.4:
                    self._px(c, px, py, r[3])
                elif ldist < 0.65:
                    self._px(c, px, py, r[2])
                elif ldist < 0.85:
                    self._px(c, px, py, r[1])
                else:
                    self._px(c, px, py, r[0])

        # Ear bumps
        ear_y = head_cy
        self._px(c, mid - head_r, ear_y, r[2])
        self._px(c, mid - head_r, ear_y - 1, r[3])
        self._px(c, mid + head_r, ear_y, r[1])
        self._px(c, mid + head_r, ear_y + 1, r[0])

        # Neck
        neck_top = head_cy + head_r
        nw = self._s(4)
        for dy in range(self._s(3)):
            y = neck_top + dy
            for dx in range(-nw, nw + 1):
                bright = r[3] if dx < 0 else r[1]
                self._px(c, mid + dx, y, r[2] if abs(dx) < nw - 1 else bright)

    def _draw_face(self, c: PixelCanvas, mid: int, skin: Color, eye_color: Color, eye_style: str):
        """Draw facial features: eyes, eyebrows, nose, mouth."""
        c.clear()
        head_cy = self._s(16)
        er = color_ramp(eye_color, 5)

        # Eye positions
        eye_y = head_cy - self._s(2)
        eye_lx = mid - self._s(4)
        eye_rx = mid + self._s(3)
        eye_w = self._s(3)
        eye_h = self._s(3)

        # Draw eyes (2x3 or 3x3 pixel blocks with sclera + iris + highlight)
        for ex_start, is_left in [(eye_lx, True), (eye_rx, False)]:
            # Sclera (white)
            for dy in range(eye_h):
                for dx in range(eye_w):
                    self._px(c, ex_start + dx, eye_y + dy, (235, 235, 240))

            # Iris (colored, center-bottom of eye)
            iris_x = ex_start + (0 if eye_w <= 2 else 1)
            iris_y = eye_y + (1 if eye_h > 2 else 0)
            for dy in range(min(2, eye_h)):
                for dx in range(min(2, eye_w)):
                    self._px(c, iris_x + dx, iris_y + dy, er[2])

            # Pupil (dark center)
            self._px(c, iris_x, iris_y + (1 if eye_h > 2 else 0), er[0])

            # Highlight (top-left of eye, white dot)
            hl_x = ex_start + (0 if is_left else eye_w - 1)
            self._px(c, hl_x, eye_y, (255, 255, 255))

        # Eyebrows
        brow_y = eye_y - self._s(2)
        brow_color = shade(*skin, 0.35)
        for dx in range(eye_w + 1):
            self._px(c, eye_lx + dx, brow_y, brow_color)
            self._px(c, eye_rx + dx, brow_y, brow_color)
        # Brow arch (inner ends slightly lower for expression)
        if eye_style == "angry":
            self._px(c, eye_lx + eye_w, brow_y + 1, brow_color)
            self._px(c, eye_rx, brow_y + 1, brow_color)

        # Nose (subtle, just 1-2 shadow pixels)
        nose_y = head_cy + self._s(2)
        nose_shadow = shade(*skin, 0.7)
        self._px(c, mid, nose_y, nose_shadow)
        self._px(c, mid + 1, nose_y, shade(*skin, 0.8))

        # Mouth
        mouth_y = head_cy + self._s(4)
        mouth_color = shade(*skin, 0.55)
        mouth_hl = shade(*skin, 0.75)
        for dx in range(-self._s(2), self._s(2) + 1):
            self._px(c, mid + dx, mouth_y, mouth_color)
        # Lower lip highlight
        self._px(c, mid - 1, mouth_y + 1, mouth_hl)
        self._px(c, mid, mouth_y + 1, mouth_hl)

    def _draw_torso(self, c: PixelCanvas, mid: int, armor_color: Color, armor_style: str):
        """Draw torso with armor/clothing detail."""
        c.clear()
        r = color_ramp(armor_color, 5)
        torso_top = self._s(27)
        torso_h = self._s(16)
        torso_w = self._s(12)

        # Main torso shape (shaded cylinder)
        for dy in range(torso_h):
            y = torso_top + dy
            w = torso_w if dy > 1 else torso_w - 1  # slight shoulder taper
            for dx in range(-w, w + 1):
                edge = abs(dx) / max(w, 1)
                vert = dy / max(torso_h - 1, 1)

                # Cylindrical shading
                if edge > 0.85:
                    sc = r[0]
                elif edge > 0.65:
                    sc = r[1] if dx > 0 else r[2]
                elif vert < 0.15:
                    sc = r[3] if edge < 0.3 else r[2]
                elif vert > 0.85:
                    sc = r[1]
                else:
                    sc = r[2] if dx > -2 else r[3]

                self._px(c, mid + dx, y, sc)

        # Armor details based on style
        if armor_style == "plate":
            self._draw_plate_detail(c, mid, torso_top, torso_h, torso_w, r)
        elif armor_style == "chain":
            self._draw_chain_detail(c, mid, torso_top, torso_h, torso_w, r)
        elif armor_style == "robe":
            self._draw_robe_detail(c, mid, torso_top, torso_h, torso_w, r)
        else:  # leather or cloth
            self._draw_leather_detail(c, mid, torso_top, torso_h, torso_w, r)

    def _draw_plate_detail(self, c, mid, top, h, w, r):
        """Add plate armor details: chest plate seam, rivets, gorget."""
        # Center seam
        seam = shade(*r[2], 0.7)
        for dy in range(2, h - 2):
            self._px(c, mid, top + dy, seam)

        # Shoulder plate highlights
        for dx in [-w + 1, -w + 2]:
            for dy in range(3):
                self._px(c, mid + dx, top + dy, r[4])
        # Right shoulder shadow
        for dx in [w - 1, w - 2]:
            for dy in range(3):
                self._px(c, mid + dx, top + dy, r[0])

        # Rivets (bright dots along seam)
        rivet = r[4]
        for dy in [3, 6, 9]:
            if top + dy < c.height:
                self._px(c, mid - 1, top + dy, rivet)
                self._px(c, mid + 1, top + dy, rivet)

        # Belt
        belt = shade(*r[2], 0.4)
        belt_hl = shade(*r[2], 0.55)
        belt_y = top + h - self._s(4)
        for dx in range(-w, w + 1):
            self._px(c, mid + dx, belt_y, belt if dx > 0 else belt_hl)
            self._px(c, mid + dx, belt_y + 1, belt)
        # Buckle
        buckle = (210, 185, 60)
        self._px(c, mid - 1, belt_y, buckle)
        self._px(c, mid, belt_y, shade(*buckle, 1.3))
        self._px(c, mid + 1, belt_y, shade(*buckle, 0.7))

    def _draw_chain_detail(self, c, mid, top, h, w, r):
        """Chainmail texture: checkerboard pattern of light/dark."""
        for dy in range(2, h - 2):
            for dx in range(-w + 2, w - 1):
                if (dx + dy) % 2 == 0:
                    self._px(c, mid + dx, top + dy, r[3])

    def _draw_robe_detail(self, c, mid, top, h, w, r):
        """Robe details: vertical folds, sash."""
        fold_shadow = shade(*r[2], 0.75)
        # Vertical fold lines
        for dy in range(3, h):
            for fold_x in [-4, 4]:
                self._px(c, mid + self._s(fold_x), top + dy, fold_shadow)
        # Sash
        sash = (180, 150, 50)
        sash_y = top + self._s(8)
        for dx in range(-w, w + 1):
            self._px(c, mid + dx, sash_y, sash)

    def _draw_leather_detail(self, c, mid, top, h, w, r):
        """Leather armor: stitching, buckle straps."""
        stitch = shade(*r[2], 0.65)
        # Stitching line
        for dy in range(2, h - 2, 2):
            self._px(c, mid - self._s(4), top + dy, stitch)
            self._px(c, mid + self._s(4), top + dy, stitch)
        # Belt
        belt_y = top + h - self._s(3)
        belt_c = shade(*r[2], 0.5)
        for dx in range(-w, w + 1):
            self._px(c, mid + dx, belt_y, belt_c)

    def _draw_legs(self, c: PixelCanvas, mid: int):
        """Draw legs with shading."""
        c.clear()
        pants_color = getattr(self, '_armor_color', (80, 70, 60))
        # Use darker shade for pants
        pants = shade(*pants_color, 0.6)
        r = color_ramp(pants, 5)
        boot_color = (70, 50, 35)
        br = color_ramp(boot_color, 5)

        leg_top = self._s(43)
        leg_h = self._s(12)
        leg_w = self._s(5)
        gap = self._s(2)

        # Left leg (lit side)
        for dy in range(leg_h):
            y = leg_top + dy
            for dx in range(-leg_w - gap // 2, -gap // 2):
                edge = abs(dx + gap // 2 + leg_w // 2) / max(leg_w, 1)
                sc = r[3] if edge < 0.3 else (r[2] if edge < 0.6 else r[1])
                self._px(c, mid + dx, y, sc)

        # Right leg (shadow side)
        for dy in range(leg_h):
            y = leg_top + dy
            for dx in range(gap // 2, leg_w + gap // 2):
                edge = abs(dx - gap // 2 - leg_w // 2) / max(leg_w, 1)
                sc = r[2] if edge < 0.3 else (r[1] if edge < 0.6 else r[0])
                self._px(c, mid + dx, y, sc)

        # Boots
        boot_top = leg_top + leg_h
        boot_h = self._s(5)
        for dy in range(boot_h):
            y = boot_top + dy
            # Left boot
            for dx in range(-leg_w - gap // 2 - 1, -gap // 2 + 1):
                sc = br[3] if dy < 1 else (br[2] if dy < 3 else br[1])
                self._px(c, mid + dx, y, sc)
            # Right boot
            for dx in range(gap // 2 - 1, leg_w + gap // 2 + 1):
                sc = br[2] if dy < 1 else (br[1] if dy < 3 else br[0])
                self._px(c, mid + dx, y, sc)

        # Boot highlight (top edge)
        for dx in range(-leg_w - gap // 2, -gap // 2):
            self._px(c, mid + dx, boot_top, br[4])

    def _draw_arms(self, front: PixelCanvas, back: PixelCanvas, mid: int, skin: Color, armor_color: Color):
        """Draw arms on separate front/back layers."""
        front.clear()
        back.clear()
        sr = color_ramp(skin, 5)
        ar = color_ramp(armor_color, 5)

        arm_top = self._s(28)
        arm_h = self._s(14)
        arm_w = self._s(4)
        shoulder_offset = self._s(13)

        # Back arm (left side, further from viewer)
        for dy in range(arm_h):
            y = arm_top + dy
            # Upper arm (armor color)
            if dy < arm_h * 0.6:
                for dx in range(arm_w):
                    sc = ar[1] if dx < arm_w // 2 else ar[0]  # shadow side
                    self._px(back, mid - shoulder_offset - dx, y, sc)
            else:
                # Forearm (skin)
                for dx in range(arm_w - 1):
                    sc = sr[1] if dx == 0 else sr[0]
                    self._px(back, mid - shoulder_offset - dx, y, sc)

        # Front arm (right side, closer to viewer)
        for dy in range(arm_h):
            y = arm_top + dy
            if dy < arm_h * 0.6:
                for dx in range(arm_w):
                    sc = ar[3] if dx < arm_w // 2 else ar[2]  # lit side
                    self._px(front, mid + shoulder_offset + dx, y, sc)
            else:
                for dx in range(arm_w - 1):
                    sc = sr[3] if dx == 0 else sr[2]
                    self._px(front, mid + shoulder_offset + dx, y, sc)

        # Hands
        hand_y = arm_top + arm_h
        for dy in range(self._s(3)):
            self._px(back, mid - shoulder_offset, hand_y + dy, sr[1])
            self._px(back, mid - shoulder_offset - 1, hand_y + dy, sr[0])
            self._px(front, mid + shoulder_offset, hand_y + dy, sr[3])
            self._px(front, mid + shoulder_offset + 1, hand_y + dy, sr[2])

    def _draw_ground_shadow(self, c: PixelCanvas, mid: int):
        """Draw a subtle elliptical ground shadow."""
        c.clear()
        shadow_y = self._s(60)
        sw = self._s(10)
        shadow_color = (0, 0, 0)
        for dx in range(-sw, sw + 1):
            dist = abs(dx) / sw
            alpha = int(40 * (1 - dist * dist))
            if 0 <= mid + dx < c.width and 0 <= shadow_y < c.height:
                c._pixels[shadow_y][mid + dx] = (*shadow_color, max(0, alpha))
            if 0 <= shadow_y + 1 < c.height:
                c._pixels[shadow_y + 1][mid + dx] = (*shadow_color, max(0, alpha // 2))

    # ==================== Hair Styles ====================

    def _draw_messy_hair(self, c, mid, r):
        head_cy = self._s(16)
        head_r = self._s(10)
        top = head_cy - head_r - self._s(2)
        # Messy volume on top
        for dy in range(self._s(8)):
            y = top + dy
            w = self._s(8) + self._s(2) - abs(dy - self._s(3))
            for dx in range(-w, w + 1):
                ldist = ((dx + w * 0.3) ** 2 + (dy - 1) ** 2) ** 0.5 / (w * 1.5)
                sc = r[4] if ldist < 0.2 else (r[3] if ldist < 0.45 else (r[2] if ldist < 0.7 else r[1]))
                self._px(c, mid + dx, y, sc)
        # Hair strands (detail pixels)
        for i in range(3):
            sx = mid - self._s(3) + i * self._s(3)
            self._px(c, sx, top + 1, r[4])

    def _draw_spiky_hair(self, c, mid, r):
        head_cy = self._s(16)
        head_r = self._s(10)
        top = head_cy - head_r - self._s(4)
        # Spikes
        spikes = [(-5, 0), (-2, -3), (1, -2), (4, -1), (7, 0)]
        for sx, sy in spikes:
            spike_x = mid + self._s(sx)
            spike_y = top + self._s(sy)
            for dy in range(self._s(6)):
                w = max(1, self._s(3) - dy)
                for dx in range(-w, w + 1):
                    sc = r[3] if dy < 2 else (r[2] if dy < 4 else r[1])
                    self._px(c, spike_x + dx, spike_y + dy, sc)

    def _draw_long_hair(self, c, mid, r):
        head_cy = self._s(16)
        head_r = self._s(10)
        top = head_cy - head_r - self._s(1)
        # Volume on top
        for dy in range(self._s(6)):
            w = self._s(9) - abs(dy - self._s(2))
            for dx in range(-w, w + 1):
                sc = r[3] if dx < 0 else r[2]
                self._px(c, mid + dx, top + dy, sc)
        # Long sides flowing down
        for dy in range(self._s(6), self._s(22)):
            y = top + dy
            w = max(self._s(2), self._s(9) - dy // 3)
            for side in [-1, 1]:
                for dx in range(self._s(1), w):
                    sx = mid + side * (self._s(8) + dx)
                    sc = r[2] if side < 0 else r[1]
                    self._px(c, sx, y, sc)

    def _draw_ponytail_hair(self, c, mid, r):
        self._draw_short_hair(c, mid, r)
        head_cy = self._s(16)
        # Ponytail behind
        for dy in range(self._s(12)):
            y = head_cy + dy
            w = max(1, self._s(3) - dy // 4)
            for dx in range(-w, w + 1):
                self._px(c, mid + self._s(1) + dx, y, r[1] if dx > 0 else r[2])

    def _draw_short_hair(self, c, mid, r):
        head_cy = self._s(16)
        head_r = self._s(10)
        top = head_cy - head_r - self._s(1)
        for dy in range(self._s(6)):
            w = self._s(8) - abs(dy - self._s(2))
            for dx in range(-w, w + 1):
                ldist = ((dx + w * 0.3) ** 2 + dy ** 2) ** 0.5 / (w * 1.5)
                sc = r[3] if ldist < 0.35 else (r[2] if ldist < 0.65 else r[1])
                self._px(c, mid + dx, top + dy, sc)
