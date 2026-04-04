"""Gemini-powered pixel art generation and auto-processing pipeline.

Uses Google's Gemini API (Nano Banana) to generate high-quality pixel art,
then automatically processes the output into game-ready assets:
1. Generate pixel art via Gemini image generation
2. Remove background (alpha channel)
3. Quantize to pixel art palette (reduce colors)
4. Resize to target game resolution
5. Auto-outline for clean edges
6. Export as PNG / SpriteSheet / GIF

Setup:
    pip install google-genai
    export GEMINI_API_KEY="your-api-key"

Example:
    >>> from gclub_pixel.gemini import GeminiPixel
    >>> gp = GeminiPixel()
    >>> knight = gp.generate("medieval knight", style="stardew", size=32)
    >>> knight.save("knight.png", scale=4)
    >>>
    >>> # Generate a full sprite sheet with multiple poses
    >>> sheet = gp.generate_sheet("warrior", poses=["idle", "walk", "attack"])
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import List, Optional, Tuple

from PIL import Image

from gclub_pixel.canvas import PixelCanvas
from gclub_pixel.palette import Palette, get_palette, color_ramp, shade


# ================================================================
# Prompt templates - the secret sauce for consistent pixel art
# ================================================================

STYLE_PROMPTS = {
    "stardew": (
        "16-bit pixel art character sprite, Stardew Valley style, "
        "warm colors, cute chibi proportions, 2-head-tall body, "
        "clean outlines, front-facing, centered on transparent background, "
        "simple shading, game-ready sprite, no background, single character"
    ),
    "deadcells": (
        "pixel art character sprite, Dead Cells style, "
        "dark moody atmosphere, detailed shading, tall proportions, "
        "glowing accents, front-facing, centered on transparent background, "
        "16-bit retro style with modern lighting, game-ready sprite, "
        "no background, single character"
    ),
    "terraria": (
        "pixel art character sprite, Terraria style, "
        "colorful vibrant, visible armor details, chibi proportions, "
        "front-facing, centered on transparent background, "
        "clean pixel art, game-ready sprite, no background, single character"
    ),
    "celeste": (
        "pixel art character sprite, Celeste game style, "
        "clean minimal, strong silhouette, small sprite, "
        "expressive with few pixels, front-facing, centered, "
        "transparent background, game-ready sprite, single character"
    ),
    "classic": (
        "pixel art character sprite, classic SNES RPG style, "
        "Final Fantasy VI / Chrono Trigger style, 16-bit era, "
        "front-facing, centered on transparent background, "
        "clean outlines, warm palette, game-ready sprite, single character"
    ),
    "modern": (
        "high quality pixel art character sprite, modern indie game style, "
        "detailed shading with 5+ color ramps per region, "
        "front-facing, centered on transparent background, "
        "professional game asset, single character, no background"
    ),
}

ROLE_PROMPTS = {
    "knight": "medieval knight with plate armor and sword, helmet or short hair",
    "warrior": "armored warrior with weapon, strong build",
    "mage": "magic user with robe and staff, long hair or pointed hat",
    "wizard": "old wizard with long beard, flowing robes, magical staff",
    "archer": "ranger with bow, hooded cloak, leather armor, quiver of arrows",
    "rogue": "stealthy rogue with dark leather, daggers, hood or mask",
    "healer": "white-robed cleric with holy symbol, gentle expression",
    "paladin": "holy knight with shining armor, cape, glowing weapon",
    "necromancer": "dark sorcerer with skull staff, tattered robes, purple energy",
    "bard": "musical adventurer with lute, colorful outfit, feathered hat",
    "monk": "martial artist with bandaged fists, simple robes",
    "princess": "royal figure with elegant dress, tiara, flowing hair",
    "villager": "simple townsperson, casual clothing, friendly expression",
    "blacksmith": "muscular smith with hammer, leather apron, soot marks",
    "merchant": "trader with coins, bag of goods, fancy outfit",
    "skeleton": "undead skeleton warrior with ancient armor, glowing eyes",
    "slime": "cute blob monster, translucent body, simple face",
    "goblin": "small green creature, ragged clothing, mischievous expression",
    "dragon": "small dragon creature, wings, scales, fiery breath",
}

POSE_PROMPTS = {
    "idle": "standing idle pose, relaxed stance",
    "walk": "mid-stride walking pose, one foot forward",
    "attack": "attacking pose with weapon raised",
    "cast": "casting magic, hands glowing with energy",
    "hurt": "recoiling from damage, pained expression",
    "dead": "fallen on ground, defeated",
    "jump": "jumping in air, arms up",
    "crouch": "crouching low, defensive stance",
}


class GeminiPixel:
    """Generate pixel art via Gemini API and auto-process into game assets.

    Args:
        api_key: Gemini API key. Falls back to GEMINI_API_KEY env var.
        model: Gemini model name for image generation.

    Example:
        >>> gp = GeminiPixel()
        >>> knight = gp.generate("medieval knight", style="deadcells", size=48)
        >>> knight.save("knight.png", scale=4)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash-preview-image-generation",
    ):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from google import genai
            except ImportError:
                raise ImportError(
                    "google-genai package required. Install with: pip install google-genai"
                )
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate(
        self,
        description: str,
        style: str = "modern",
        size: int = 32,
        palette_name: Optional[str] = None,
        remove_bg: bool = True,
        add_outline: bool = True,
    ) -> PixelCanvas:
        """Generate a pixel art character from a text description.

        The full pipeline: Gemini generates → remove background →
        resize to target → quantize palette → add outline.

        Args:
            description: Character description (e.g., "medieval knight with silver armor").
                         Can also use preset role names: "knight", "mage", "archer", etc.
            style: Art style preset. One of:
                   "stardew", "deadcells", "terraria", "celeste", "classic", "modern"
            size: Target sprite size in pixels (32, 48, or 64).
            palette_name: Optional palette to quantize to (e.g., "pico8", "endesga32").
            remove_bg: Whether to remove background (default True).
            add_outline: Whether to add colored outline (default True).

        Returns:
            PixelCanvas with the processed pixel art sprite.

        Example:
            >>> knight = gp.generate("knight", style="deadcells", size=48)
            >>> knight.save("knight.png", scale=4)
            >>>
            >>> # Custom description
            >>> char = gp.generate("female elf archer with green cloak", style="stardew")
            >>> char.save("elf.png", scale=8)
        """
        prompt = self._build_prompt(description, style, size)
        raw_image = self._generate_image(prompt)
        return self._process_image(raw_image, size, palette_name, remove_bg, add_outline)

    def generate_sheet(
        self,
        description: str,
        poses: List[str] = None,
        style: str = "modern",
        size: int = 32,
        palette_name: Optional[str] = None,
    ) -> List[PixelCanvas]:
        """Generate multiple poses of the same character.

        Each pose is generated separately with consistent style prompting.

        Args:
            description: Character description or role name.
            poses: List of pose names (default: ["idle", "walk", "attack"]).
            style: Art style preset.
            size: Target sprite size.

        Returns:
            List of PixelCanvas, one per pose.

        Example:
            >>> frames = gp.generate_sheet("knight", poses=["idle", "walk", "attack"])
            >>> for i, f in enumerate(frames):
            ...     f.save(f"knight_{i}.png", scale=4)
        """
        if poses is None:
            poses = ["idle", "walk", "attack"]

        results = []
        for pose in poses:
            prompt = self._build_prompt(description, style, size, pose=pose)
            raw = self._generate_image(prompt)
            canvas = self._process_image(raw, size, palette_name)
            results.append(canvas)
        return results

    def generate_batch(
        self,
        characters: List[str],
        style: str = "modern",
        size: int = 32,
        palette_name: Optional[str] = None,
    ) -> List[PixelCanvas]:
        """Generate multiple different characters in the same style.

        Useful for creating a consistent party or enemy set.

        Args:
            characters: List of descriptions or role names.
            style: Art style (applied to all).
            size: Target sprite size.

        Returns:
            List of PixelCanvas, one per character.

        Example:
            >>> party = gp.generate_batch(["knight", "mage", "archer"], style="stardew")
        """
        return [self.generate(desc, style=style, size=size, palette_name=palette_name)
                for desc in characters]

    # ================================================================
    # Internal methods
    # ================================================================

    def _build_prompt(self, description: str, style: str, size: int, pose: str = None) -> str:
        """Construct the full generation prompt."""
        parts = []

        # Style prefix
        style_key = style.lower().replace(" ", "").replace("-", "")
        style_prompt = STYLE_PROMPTS.get(style_key, STYLE_PROMPTS["modern"])
        parts.append(style_prompt)

        # Role/description
        role_key = description.lower().replace(" ", "_")
        if role_key in ROLE_PROMPTS:
            parts.append(ROLE_PROMPTS[role_key])
        else:
            parts.append(description)

        # Pose
        if pose:
            pose_key = pose.lower().replace(" ", "_")
            pose_prompt = POSE_PROMPTS.get(pose_key, f"{pose} pose")
            parts.append(pose_prompt)

        # Size hint
        parts.append(f"target resolution {size}x{size} pixels")
        parts.append("single character only, no text, no UI elements")

        return ", ".join(parts)

    def _generate_image(self, prompt: str) -> Image.Image:
        """Call Gemini API to generate an image."""
        client = self._get_client()

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_modalities": ["IMAGE", "TEXT"],
            },
        )

        # Extract image from response
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data is not None:
                image_bytes = part.inline_data.data
                return Image.open(io.BytesIO(image_bytes)).convert("RGBA")

        raise RuntimeError("Gemini did not return an image. Try a different prompt.")

    def _process_image(
        self,
        img: Image.Image,
        target_size: int,
        palette_name: Optional[str],
        remove_bg: bool = True,
        add_outline: bool = True,
    ) -> PixelCanvas:
        """Process raw Gemini output into a game-ready pixel art sprite."""

        # Step 1: Remove background
        if remove_bg:
            img = self._remove_background(img)

        # Step 2: Crop to content (remove empty space)
        img = self._crop_to_content(img)

        # Step 3: Resize to target with nearest-neighbor for crisp pixels
        # First resize with LANCZOS for quality, but if already small use NEAREST
        if img.width > target_size * 4:
            # Large image → LANCZOS downsample for smooth result
            img = img.resize((target_size, target_size), Image.LANCZOS)
        else:
            img = img.resize((target_size, target_size), Image.NEAREST)

        # Step 4: Palette quantization (optional)
        if palette_name:
            img = self._quantize_to_palette(img, palette_name)

        # Step 5: Clean up alpha (snap to fully opaque or transparent)
        img = self._clean_alpha(img)

        # Step 6: Convert to PixelCanvas
        canvas = PixelCanvas(target_size, target_size)
        for y in range(target_size):
            for x in range(target_size):
                r, g, b, a = img.getpixel((x, y))
                if a > 0:
                    canvas._pixels[y][x] = (r, g, b, 255)

        # Step 7: Add colored outline
        if add_outline:
            canvas.colored_outline()

        return canvas

    def _remove_background(self, img: Image.Image) -> Image.Image:
        """Remove background using corner color sampling."""
        pixels = img.load()
        w, h = img.size

        # Sample corners to determine background color
        corners = [
            pixels[0, 0], pixels[w-1, 0],
            pixels[0, h-1], pixels[w-1, h-1],
        ]
        # Most common corner color = background
        bg = max(set(corners), key=corners.count)
        bg_r, bg_g, bg_b = bg[0], bg[1], bg[2]

        # Flood fill from corners with tolerance
        tolerance = 40
        visited = set()
        stack = [(0, 0), (w-1, 0), (0, h-1), (w-1, h-1)]

        while stack:
            x, y = stack.pop()
            if (x, y) in visited or not (0 <= x < w and 0 <= y < h):
                continue
            visited.add((x, y))
            r, g, b, a = pixels[x, y]
            dist = abs(r - bg_r) + abs(g - bg_g) + abs(b - bg_b)
            if dist < tolerance:
                pixels[x, y] = (0, 0, 0, 0)
                for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    stack.append((x+dx, y+dy))

        return img

    def _crop_to_content(self, img: Image.Image) -> Image.Image:
        """Crop to the bounding box of non-transparent pixels."""
        bbox = img.getbbox()
        if bbox:
            # Add 1px padding
            x1, y1, x2, y2 = bbox
            x1 = max(0, x1 - 1)
            y1 = max(0, y1 - 1)
            x2 = min(img.width, x2 + 1)
            y2 = min(img.height, y2 + 1)

            # Make square (centered)
            w, h = x2 - x1, y2 - y1
            side = max(w, h)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            x1 = max(0, cx - side // 2)
            y1 = max(0, cy - side // 2)
            x2 = min(img.width, x1 + side)
            y2 = min(img.height, y1 + side)

            img = img.crop((x1, y1, x2, y2))
        return img

    def _quantize_to_palette(self, img: Image.Image, palette_name: str) -> Image.Image:
        """Reduce colors to match a pixel art palette."""
        pal = get_palette(palette_name)
        pixels = img.load()
        w, h = img.size

        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                if a > 0:
                    closest = pal.closest(r, g, b)
                    pixels[x, y] = (*closest, a)
        return img

    def _clean_alpha(self, img: Image.Image) -> Image.Image:
        """Snap alpha channel to binary (0 or 255)."""
        pixels = img.load()
        w, h = img.size
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                pixels[x, y] = (r, g, b, 255 if a > 80 else 0)
        return img


def gemini_generate(
    description: str,
    style: str = "modern",
    size: int = 32,
    api_key: Optional[str] = None,
    palette: Optional[str] = None,
) -> PixelCanvas:
    """One-shot function to generate a pixel art sprite via Gemini.

    This is the simplest API - one function call, one sprite.

    Args:
        description: What to generate (e.g., "medieval knight", "fire mage", "cute slime").
        style: Art style ("stardew", "deadcells", "terraria", "celeste", "classic", "modern").
        size: Output pixel size (32, 48, or 64).
        api_key: Gemini API key (or set GEMINI_API_KEY env var).
        palette: Optional palette quantization ("pico8", "endesga32", etc.).

    Returns:
        PixelCanvas ready to save or animate.

    Example:
        >>> from gclub_pixel.gemini import gemini_generate
        >>> knight = gemini_generate("knight", style="deadcells", size=48)
        >>> knight.save("knight.png", scale=4)
    """
    gp = GeminiPixel(api_key=api_key)
    return gp.generate(description, style=style, size=size, palette_name=palette)
