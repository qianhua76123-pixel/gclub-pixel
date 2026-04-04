"""Game art style presets - generate characters in the style of famous pixel art games.

Each style defines proportions, shading intensity, color philosophy, detail level,
and rendering rules. LLMs pick a style name, the engine handles the rest.

Available styles:
    - "stardew": Warm, friendly, 16x32, Stardew Valley style
    - "deadcells": Dark, detailed, 64x64, Dead Cells style
    - "terraria": Colorful, equipment-heavy, 40x40, Terraria style
    - "celeste": Clean, expressive, 32x32, Celeste style
    - "undertale": Minimal, iconic, 32x32, Undertale style

Example:
    >>> from gclub_pixel.styles import create_styled_character
    >>> knight = create_styled_character("deadcells", role="knight",
    ...     hair_color=(140, 90, 40), armor_color=(160, 165, 180))
    >>> knight.save("dc_knight.png", scale=4)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from gclub_pixel.canvas import PixelCanvas
from gclub_pixel.palette import Color, color_ramp, shade, colored_outline


@dataclass
class StyleConfig:
    """Configuration for a pixel art style."""
    name: str
    width: int
    height: int
    head_ratio: float      # head height as fraction of total (0.3 = chibi, 0.2 = tall)
    body_width_ratio: float  # body width as fraction of total width
    shade_steps: int       # 3 = flat, 5 = detailed shading
    outline_style: str     # "black", "colored", "none"
    eye_style: str         # "dot", "anime", "detailed", "minimal"
    color_saturation: float  # 0.5 = muted, 1.0 = vivid
    detail_level: str      # "minimal", "medium", "high"
    bg_style: str          # "clean", "glow", "shadow"
    description: str


STYLES = {
    "stardew": StyleConfig(
        name="stardew",
        width=16, height=32,
        head_ratio=0.28, body_width_ratio=0.65,
        shade_steps=3, outline_style="colored",
        eye_style="dot", color_saturation=0.85,
        detail_level="minimal", bg_style="clean",
        description="Warm, cozy, Stardew Valley style. Small 16x32 sprites with big personality.",
    ),
    "deadcells": StyleConfig(
        name="deadcells",
        width=48, height=64,
        head_ratio=0.22, body_width_ratio=0.45,
        shade_steps=5, outline_style="colored",
        eye_style="minimal", color_saturation=0.7,
        detail_level="high", bg_style="glow",
        description="Dark, atmospheric, Dead Cells style. Tall proportions, heavy shading, moody palette.",
    ),
    "terraria": StyleConfig(
        name="terraria",
        width=26, height=48,
        head_ratio=0.25, body_width_ratio=0.5,
        shade_steps=4, outline_style="black",
        eye_style="anime", color_saturation=1.0,
        detail_level="medium", bg_style="clean",
        description="Colorful, equipment-focused, Terraria style. Visible armor details, vivid colors.",
    ),
    "celeste": StyleConfig(
        name="celeste",
        width=16, height=24,
        head_ratio=0.35, body_width_ratio=0.6,
        shade_steps=3, outline_style="colored",
        eye_style="dot", color_saturation=0.9,
        detail_level="minimal", bg_style="clean",
        description="Clean, expressive, Celeste style. Tiny but readable, strong silhouettes.",
    ),
    "undertale": StyleConfig(
        name="undertale",
        width=20, height=32,
        head_ratio=0.3, body_width_ratio=0.5,
        shade_steps=3, outline_style="black",
        eye_style="dot", color_saturation=0.8,
        detail_level="minimal", bg_style="clean",
        description="Charming retro, Undertale style. Simple shapes, bold outlines, iconic readability.",
    ),
}


def get_style(name: str) -> StyleConfig:
    """Get a style configuration by name.

    Available: stardew, deadcells, terraria, celeste, undertale

    Example:
        >>> style = get_style("deadcells")
        >>> print(style.width, style.height)
        48 64
    """
    key = name.lower().replace(" ", "").replace("_", "").replace("-", "")
    for k, v in STYLES.items():
        if key == k or key in k:
            return v
    raise ValueError(f"Unknown style: {name}. Available: {list(STYLES)}")


def list_styles() -> dict:
    """List all available styles with descriptions.

    Example:
        >>> for name, desc in list_styles().items():
        ...     print(f"{name}: {desc}")
    """
    return {k: v.description for k, v in STYLES.items()}


def create_styled_character(
    style: str = "deadcells",
    role: str = "warrior",
    skin_color: Color = (215, 175, 135),
    hair_color: Color = (100, 65, 35),
    hair_style: str = "short",
    armor_color: Color = (120, 120, 140),
    accent_color: Color = (180, 50, 50),
    eye_color: Color = (50, 70, 120),
) -> PixelCanvas:
    """Create a character sprite in a specific game art style.

    This is the main API for LLMs. Pick a style, set colors, get a sprite.

    Args:
        style: Art style name ("stardew", "deadcells", "terraria", "celeste", "undertale").
        role: Character archetype ("warrior", "mage", "archer", "rogue", "healer").
        skin_color: RGB skin midtone.
        hair_color: RGB hair midtone.
        hair_style: "short", "long", "spiky", "messy", "ponytail", "bald".
        armor_color: RGB armor/clothing midtone.
        accent_color: RGB accent (cape, belt, trim).
        eye_color: RGB eye color.

    Returns:
        PixelCanvas with the styled character.

    Example:
        >>> # Stardew Valley farmer
        >>> farmer = create_styled_character("stardew", role="warrior",
        ...     hair_color=(180, 120, 50), armor_color=(80, 120, 180))
        >>> farmer.save("farmer.png", scale=8)
        >>>
        >>> # Dead Cells knight
        >>> knight = create_styled_character("deadcells", role="warrior",
        ...     armor_color=(160, 165, 180), accent_color=(180, 40, 40))
        >>> knight.save("knight.png", scale=4)
    """
    cfg = get_style(style)
    c = PixelCanvas(cfg.width, cfg.height)

    skin_r = color_ramp(skin_color, cfg.shade_steps)
    hair_r = color_ramp(hair_color, cfg.shade_steps)
    armor_r = color_ramp(armor_color, cfg.shade_steps)
    accent_r = color_ramp(accent_color, cfg.shade_steps)

    mid_x = cfg.width // 2
    head_h = round(cfg.height * cfg.head_ratio)
    body_w = round(cfg.width * cfg.body_width_ratio)

    # Dispatch to style-specific renderer
    if cfg.name == "stardew":
        _render_stardew(c, cfg, mid_x, head_h, body_w, skin_r, hair_r, armor_r, accent_r, eye_color, hair_style, role)
    elif cfg.name == "deadcells":
        _render_deadcells(c, cfg, mid_x, head_h, body_w, skin_r, hair_r, armor_r, accent_r, eye_color, hair_style, role)
    elif cfg.name == "terraria":
        _render_terraria(c, cfg, mid_x, head_h, body_w, skin_r, hair_r, armor_r, accent_r, eye_color, hair_style, role)
    elif cfg.name == "celeste":
        _render_celeste(c, cfg, mid_x, head_h, body_w, skin_r, hair_r, armor_r, accent_r, eye_color, hair_style, role)
    elif cfg.name == "undertale":
        _render_undertale(c, cfg, mid_x, head_h, body_w, skin_r, hair_r, armor_r, accent_r, eye_color, hair_style, role)

    # Apply outline
    if cfg.outline_style == "colored":
        c.colored_outline()
    elif cfg.outline_style == "black":
        c.outline((0, 0, 0))

    return c


# ================================================================
# Style-specific renderers
# ================================================================

def _px(c, x, y, color):
    if 0 <= x < c.width and 0 <= y < c.height:
        c._pixels[y][x] = (*color, 255)

def _rect(c, x, y, w, h, color):
    for py in range(max(0, y), min(c.height, y + h)):
        for px in range(max(0, x), min(c.width, x + w)):
            c._pixels[py][px] = (*color, 255)

def _shaded_rect(c, x, y, w, h, ramp, shade_steps):
    """Draw rectangle with style-appropriate shading level."""
    base = ramp[len(ramp) // 2]
    highlight = ramp[-1] if len(ramp) > 2 else base
    shadow = ramp[0]
    mid_shade = ramp[max(0, len(ramp) // 2 - 1)]

    for py in range(max(0, y), min(c.height, y + h)):
        for px in range(max(0, x), min(c.width, x + w)):
            # Edge-based shading
            edge_x = (px - x) / max(w - 1, 1)
            edge_y = (py - y) / max(h - 1, 1)

            if shade_steps <= 3:
                # Flat style: just base with edge highlights
                if edge_y < 0.15 or edge_x < 0.15:
                    c._pixels[py][px] = (*highlight, 255)
                elif edge_y > 0.85 or edge_x > 0.85:
                    c._pixels[py][px] = (*shadow, 255)
                else:
                    c._pixels[py][px] = (*base, 255)
            else:
                # Detailed style: gradient shading
                light = (edge_x + edge_y) / 2  # distance from top-left
                if light < 0.15:
                    c._pixels[py][px] = (*highlight, 255)
                elif light < 0.35:
                    sc = ramp[-2] if len(ramp) > 3 else highlight
                    c._pixels[py][px] = (*sc, 255)
                elif light < 0.6:
                    c._pixels[py][px] = (*base, 255)
                elif light < 0.8:
                    c._pixels[py][px] = (*mid_shade, 255)
                else:
                    c._pixels[py][px] = (*shadow, 255)


def _shaded_oval(c, cx, cy, rx, ry, ramp, shade_steps):
    """Draw shaded oval/ellipse for heads."""
    highlight = ramp[-1]
    base = ramp[len(ramp) // 2]
    shadow = ramp[0]
    mid_shade = ramp[max(0, len(ramp) // 2 - 1)]

    for py in range(cy - ry, cy + ry + 1):
        for px in range(cx - rx, cx + rx + 1):
            dx = (px - cx) / max(rx, 1)
            dy = (py - cy) / max(ry, 1)
            if dx * dx + dy * dy > 1.0:
                continue
            # Spherical light from top-left
            ldist = ((dx + 0.35) ** 2 + (dy + 0.35) ** 2) ** 0.5 / 1.8
            ldist = min(1.0, max(0.0, ldist))

            if shade_steps <= 3:
                sc = highlight if ldist < 0.35 else (base if ldist < 0.7 else shadow)
            else:
                if ldist < 0.15: sc = highlight
                elif ldist < 0.35: sc = ramp[-2] if len(ramp) > 3 else highlight
                elif ldist < 0.55: sc = base
                elif ldist < 0.75: sc = mid_shade
                else: sc = shadow
            _px(c, px, py, sc)


# ---- STARDEW VALLEY (16x32) ----
def _render_stardew(c, cfg, mid, head_h, body_w, skin_r, hair_r, armor_r, accent_r, eye_color, hair_style, role):
    W, H = cfg.width, cfg.height
    # Hair (top cap)
    _shaded_rect(c, mid - 4, 1, 8, 4, hair_r, 3)
    _shaded_rect(c, mid - 5, 3, 10, 2, hair_r, 3)
    # Head
    _shaded_oval(c, mid, 6, 4, 4, skin_r, 3)
    # Eyes (simple dots)
    _px(c, mid - 2, 6, eye_color)
    _px(c, mid + 1, 6, eye_color)
    # Mouth
    _px(c, mid - 1, 8, shade(*skin_r[0], 1.2))
    _px(c, mid, 8, shade(*skin_r[0], 1.2))
    # Body
    _shaded_rect(c, mid - 4, 11, 8, 10, armor_r, 3)
    # Belt
    _rect(c, mid - 4, 17, 8, 1, accent_r[len(accent_r) // 2])
    # Arms
    for dy in range(7):
        _px(c, mid - 5, 12 + dy, skin_r[2] if len(skin_r) > 2 else skin_r[-1])
        _px(c, mid + 4, 12 + dy, skin_r[0])
    # Legs
    _shaded_rect(c, mid - 3, 21, 3, 8, armor_r, 3)
    _shaded_rect(c, mid, 21, 3, 8, [shade(*x, 0.8) for x in armor_r], 3)
    # Boots
    _rect(c, mid - 4, 28, 4, 3, accent_r[0])
    _rect(c, mid, 28, 4, 3, shade(*accent_r[0], 0.7))


# ---- DEAD CELLS (48x64) ----
def _render_deadcells(c, cfg, mid, head_h, body_w, skin_r, hair_r, armor_r, accent_r, eye_color, hair_style, role):
    W, H = cfg.width, cfg.height
    # Dead Cells: tall, dark, detailed, moody
    # Head (smaller relative to body, elongated)
    head_cy = 10
    head_rx, head_ry = 6, 7
    _shaded_oval(c, mid, head_cy, head_rx, head_ry, skin_r, 5)

    # Hair
    if hair_style == "spiky":
        for i, dx in enumerate([-4, -1, 2, 5]):
            spike_h = 5 - abs(i - 1)
            for dy in range(spike_h):
                _px(c, mid + dx, 2 - dy, hair_r[3 if dy < 2 else 2])
                _px(c, mid + dx + 1, 2 - dy, hair_r[2 if dy < 2 else 1])
    else:
        _shaded_rect(c, mid - 7, 2, 14, 6, hair_r, 5)
    # Hair sides
    for dy in range(8):
        _px(c, mid - 7, 4 + dy, hair_r[1])
        _px(c, mid + 6, 4 + dy, hair_r[0])

    # Eyes (narrow slits, Dead Cells style - glowing)
    eye_glow = shade(*eye_color, 1.8)
    for dx in [-3, -2, 2, 3]:
        _px(c, mid + dx, 9, eye_color)
    _px(c, mid - 3, 9, eye_glow)
    _px(c, mid + 2, 9, eye_glow)

    # Neck
    _shaded_rect(c, mid - 2, 17, 4, 3, skin_r, 5)

    # Torso (tall, armored)
    torso_top = 20
    torso_h = 18
    bw = body_w // 2
    _shaded_rect(c, mid - bw, torso_top, body_w, torso_h, armor_r, 5)

    # Armor detail: chest plate lines
    for dy in range(2, torso_h - 2):
        _px(c, mid, torso_top + dy, shade(*armor_r[len(armor_r) // 2], 0.6))
    # Shoulder pauldrons
    for dy in range(4):
        for dx in range(3):
            _px(c, mid - bw - 2 + dx, torso_top + dy, armor_r[3 if dx > 0 else 4])
            _px(c, mid + bw - 1 + dx, torso_top + dy, armor_r[1 if dx > 0 else 0])
    # Belt
    _rect(c, mid - bw, torso_top + torso_h - 3, body_w, 2, accent_r[len(accent_r) // 2])
    # Buckle
    _px(c, mid, torso_top + torso_h - 3, accent_r[-1])
    _px(c, mid - 1, torso_top + torso_h - 3, accent_r[-1])

    # Cape/accent on one shoulder
    if role in ("warrior", "mage"):
        for dy in range(14):
            cape_w = 3 if dy < 8 else 2
            for dx in range(cape_w):
                _px(c, mid + bw + dx, torso_top + 2 + dy, accent_r[2 if dx == 0 else 1])

    # Arms
    arm_top = torso_top + 1
    for dy in range(14):
        # Left arm (lit)
        _px(c, mid - bw - 1, arm_top + dy, armor_r[3] if dy < 7 else skin_r[2])
        _px(c, mid - bw - 2, arm_top + dy, armor_r[2] if dy < 7 else skin_r[1])
        # Right arm (shadow)
        _px(c, mid + bw, arm_top + dy, armor_r[1] if dy < 7 else skin_r[1])
        _px(c, mid + bw + 1, arm_top + dy, armor_r[0] if dy < 7 else skin_r[0])

    # Hands
    _px(c, mid - bw - 2, arm_top + 14, skin_r[2])
    _px(c, mid - bw - 1, arm_top + 14, skin_r[1])
    _px(c, mid + bw, arm_top + 14, skin_r[1])
    _px(c, mid + bw + 1, arm_top + 14, skin_r[0])

    # Legs
    leg_top = torso_top + torso_h
    leg_h = 14
    leg_w = 4
    gap = 2
    # Left leg
    _shaded_rect(c, mid - leg_w - gap // 2, leg_top, leg_w, leg_h, armor_r, 5)
    # Right leg
    darker_armor = [shade(*x, 0.85) for x in armor_r]
    _shaded_rect(c, mid + gap // 2, leg_top, leg_w, leg_h, darker_armor, 5)

    # Boots (darker, heavier)
    boot_top = leg_top + leg_h - 3
    boot_color = [shade(*x, 0.5) for x in armor_r]
    _shaded_rect(c, mid - leg_w - gap // 2 - 1, boot_top, leg_w + 2, 4, boot_color, 5)
    _shaded_rect(c, mid + gap // 2 - 1, boot_top, leg_w + 2, 4, boot_color, 5)

    # Ground glow (Dead Cells signature)
    for dx in range(-8, 9):
        alpha = max(10, 40 - abs(dx) * 4)
        if 0 <= mid + dx < W and H - 1 >= 0:
            c._pixels[H - 1][mid + dx] = (*accent_r[len(accent_r) // 2], alpha)


# ---- TERRARIA (26x48) ----
def _render_terraria(c, cfg, mid, head_h, body_w, skin_r, hair_r, armor_r, accent_r, eye_color, hair_style, role):
    W, H = cfg.width, cfg.height
    # Head
    head_cy = 7
    _shaded_oval(c, mid, head_cy, 5, 5, skin_r, 4)
    # Hair (Terraria: prominent, colorful)
    for dy in range(5):
        w = 6 if dy > 1 else 5 - dy
        for dx in range(-w, w + 1):
            sc = hair_r[3] if dx < 0 and dy < 2 else (hair_r[2] if dy < 3 else hair_r[1])
            _px(c, mid + dx, 1 + dy, sc)

    # Eyes (Terraria anime style: 3px wide white with colored pupil)
    for ex in [mid - 3, mid + 1]:
        _px(c, ex, 7, (240, 240, 240))
        _px(c, ex + 1, 7, eye_color)
        _px(c, ex + 2, 7, (240, 240, 240))
        _px(c, ex + 1, 6, (240, 240, 240))

    # Body (Terraria: clearly visible armor layers)
    torso_top = 13
    _shaded_rect(c, mid - 6, torso_top, 12, 12, armor_r, 4)
    # Armor trim lines
    for dy in [0, 5, 11]:
        for dx in range(-6, 7):
            _px(c, mid + dx, torso_top + dy, accent_r[2] if dx < 0 else accent_r[1])
    # Armor emblem (center dot pattern)
    _px(c, mid - 1, torso_top + 3, accent_r[-1])
    _px(c, mid, torso_top + 3, accent_r[-1])
    _px(c, mid, torso_top + 4, accent_r[-2 if len(accent_r) > 1 else -1])

    # Arms
    for dy in range(10):
        _px(c, mid - 7, torso_top + 1 + dy, armor_r[3 if dy < 5 else 2])
        _px(c, mid - 8, torso_top + 1 + dy, skin_r[2] if dy > 6 else armor_r[2])
        _px(c, mid + 6, torso_top + 1 + dy, armor_r[1 if dy < 5 else 0])
        _px(c, mid + 7, torso_top + 1 + dy, skin_r[1] if dy > 6 else armor_r[1])

    # Legs
    leg_top = torso_top + 12
    _shaded_rect(c, mid - 4, leg_top, 4, 14, armor_r, 4)
    darker = [shade(*x, 0.8) for x in armor_r]
    _shaded_rect(c, mid, leg_top, 4, 14, darker, 4)

    # Boots
    _shaded_rect(c, mid - 5, leg_top + 11, 5, 4, [shade(*x, 0.5) for x in armor_r], 4)
    _shaded_rect(c, mid, leg_top + 11, 5, 4, [shade(*x, 0.4) for x in armor_r], 4)


# ---- CELESTE (16x24) ----
def _render_celeste(c, cfg, mid, head_h, body_w, skin_r, hair_r, armor_r, accent_r, eye_color, hair_style, role):
    W, H = cfg.width, cfg.height
    # Celeste: very small, clean, strong silhouette
    # Hair
    _rect(c, mid - 4, 1, 8, 3, hair_r[len(hair_r) // 2])
    _rect(c, mid - 3, 0, 6, 1, hair_r[-1])
    # Head
    _shaded_oval(c, mid, 5, 3, 3, skin_r, 3)
    # Eyes (single pixel each)
    _px(c, mid - 2, 5, eye_color)
    _px(c, mid + 1, 5, eye_color)
    # Body
    _shaded_rect(c, mid - 3, 9, 6, 6, armor_r, 3)
    # Arms
    for dy in range(4):
        _px(c, mid - 4, 10 + dy, skin_r[-1])
        _px(c, mid + 3, 10 + dy, skin_r[0])
    # Legs
    _rect(c, mid - 2, 15, 2, 6, armor_r[len(armor_r) // 2])
    _rect(c, mid, 15, 2, 6, shade(*armor_r[len(armor_r) // 2], 0.7))
    # Boots
    _rect(c, mid - 3, 20, 3, 3, accent_r[0])
    _rect(c, mid, 20, 3, 3, shade(*accent_r[0], 0.7))
    # Hair bang detail
    _px(c, mid - 4, 3, hair_r[-1])
    _px(c, mid - 4, 4, hair_r[-2 if len(hair_r) > 1 else -1])


# ---- UNDERTALE (20x32) ----
def _render_undertale(c, cfg, mid, head_h, body_w, skin_r, hair_r, armor_r, accent_r, eye_color, hair_style, role):
    W, H = cfg.width, cfg.height
    # Undertale: bold black outlines, minimal shading, iconic shapes
    base_skin = skin_r[len(skin_r) // 2]
    base_hair = hair_r[len(hair_r) // 2]
    base_armor = armor_r[len(armor_r) // 2]
    base_accent = accent_r[len(accent_r) // 2]

    # Hair
    _rect(c, mid - 5, 2, 10, 4, base_hair)
    _rect(c, mid - 4, 1, 8, 2, base_hair)
    # Head
    _rect(c, mid - 4, 4, 8, 7, base_skin)
    # Eyes (Undertale: simple 2x1 or 1x1)
    _px(c, mid - 2, 7, eye_color)
    _px(c, mid - 1, 7, eye_color)
    _px(c, mid + 1, 7, eye_color)
    _px(c, mid + 2, 7, eye_color)
    # Mouth
    _px(c, mid - 1, 9, shade(*base_skin, 0.5))
    _px(c, mid, 9, shade(*base_skin, 0.5))
    # Body
    _rect(c, mid - 5, 11, 10, 9, base_armor)
    # Stripe (Undertale loves stripes)
    _rect(c, mid - 5, 14, 10, 2, base_accent)
    # Arms
    for dy in range(6):
        _px(c, mid - 6, 12 + dy, base_skin)
        _px(c, mid + 5, 12 + dy, base_skin)
    # Legs
    _rect(c, mid - 4, 20, 3, 8, base_armor)
    _rect(c, mid + 1, 20, 3, 8, shade(*base_armor, 0.8))
    # Shoes
    _rect(c, mid - 5, 27, 4, 3, accent_r[0])
    _rect(c, mid + 1, 27, 4, 3, shade(*accent_r[0], 0.8))
