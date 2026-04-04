"""End-to-end pixel art asset pipeline.

One function call: description → ComfyUI generation → auto-processing →
animation frames → SpriteSheet + GIF export.

This is the final integrated pipeline that combines everything:
1. ComfyUI generates high-quality pixel art via SD + LoRA
2. Auto post-processing: remove bg, crop, resize, palette quantize, outline
3. Multi-pose generation for animation sheets
4. Frame interpolation for smooth animations
5. Export to all formats (PNG, SpriteSheet, GIF, Godot, Phaser)

Example:
    >>> from gclub_pixel.pipeline import PixelPipeline
    >>> pipe = PixelPipeline()
    >>> assets = pipe.create_character("medieval knight with silver armor")
    >>> # → outputs: idle.gif, walk.gif, attack.gif, spritesheet.png, all individual frames
"""

from __future__ import annotations

import json
import os
import random
import time
import urllib.parse
import urllib.request
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

from gclub_pixel.canvas import PixelCanvas
from gclub_pixel.animation import Animation
from gclub_pixel.palette import get_palette, color_ramp, shade
from gclub_pixel.export import export_spritesheet_with_meta, export_phaser_atlas


# ================================================================
# Prompt engineering templates
# ================================================================

_PIXEL_POSITIVE_BASE = (
    "pixel art, pixel sprite, 16-bit retro game character, "
    "{description}, "
    "{pose_prompt}, "
    "full body, centered, plain white background, white backdrop, "
    "clean sharp pixels, no anti-aliasing, limited color palette, "
    "dark pixel outlines, RPG game sprite, masterpiece, high quality pixel art"
)

_PIXEL_NEGATIVE = (
    "blurry, realistic, photographic, 3d render, smooth gradients, "
    "anti-aliased, text, watermark, signature, multiple characters, "
    "detailed background, scenery, low quality, deformed, ugly, "
    "painted, oil painting, sketch, line art"
)

_POSE_PROMPTS = {
    "idle":      "front view, standing idle pose, relaxed stance, arms at sides",
    "walk_1":    "front view, walking pose left foot forward, mid-stride",
    "walk_2":    "front view, walking pose right foot forward, mid-stride",
    "attack_1":  "front view, attack wind-up pose, weapon pulled back, ready to strike",
    "attack_2":  "front view, attack swing pose, weapon swinging forward, action pose",
    "attack_3":  "front view, attack follow-through pose, weapon extended",
    "hurt":      "front view, taking damage pose, recoiling backward, pained expression",
    "cast":      "front view, casting magic spell, hands glowing with energy, magical pose",
    "jump":      "front view, jumping in air pose, feet off ground, arms up",
    "crouch":    "front view, crouching low, defensive stance",
    "dead":      "lying on ground, defeated pose, fallen",
}

_STYLE_MODIFIERS = {
    "stardew":   "stardew valley style, warm colors, cute chibi, cozy",
    "deadcells": "dead cells style, dark moody, detailed shading, glowing accents",
    "terraria":  "terraria style, colorful vibrant, visible armor details",
    "celeste":   "celeste style, clean minimal, strong silhouette, expressive",
    "classic":   "SNES RPG style, Final Fantasy style, chrono trigger, 16-bit era",
    "default":   "retro RPG style, clean pixel art, balanced proportions",
}


class PixelPipeline:
    """Complete pixel art asset generation pipeline.

    Connects to a local ComfyUI instance, generates images via
    Stable Diffusion + LoRA, and auto-processes into game-ready assets.

    Args:
        comfyui_url: ComfyUI server URL.
        model: Checkpoint model filename.
        lora: LoRA filename for pixel art style.
        lora_strength: LoRA weight (0.8-1.3 recommended).
        target_size: Output sprite size in pixels.
        style: Art style preset name.

    Example:
        >>> pipe = PixelPipeline()
        >>> pipe.create_character("fire mage with red robes", output_dir="./assets/")
    """

    def __init__(
        self,
        comfyui_url: str = "http://localhost:8188",
        model: str = "dreamshaper_8.safetensors",
        lora: str = "pixel-art-sd15.safetensors",
        lora_strength: float = 1.2,
        target_size: int = 32,
        style: str = "default",
    ):
        self.url = comfyui_url.rstrip("/")
        self.model = model
        self.lora = lora
        self.lora_strength = lora_strength
        self.target_size = target_size
        self.style = style

    def _check_server(self) -> bool:
        try:
            urllib.request.urlopen(f"{self.url}/system_stats", timeout=3)
            return True
        except Exception:
            return False

    # ================================================================
    # Core generation
    # ================================================================

    def _build_workflow(self, description: str, pose: str = "idle", seed: int = -1) -> dict:
        """Build ComfyUI API workflow."""
        if seed < 0:
            seed = random.randint(0, 2**32)

        pose_prompt = _POSE_PROMPTS.get(pose, _POSE_PROMPTS["idle"])
        style_mod = _STYLE_MODIFIERS.get(self.style, _STYLE_MODIFIERS["default"])

        positive = _PIXEL_POSITIVE_BASE.format(
            description=description,
            pose_prompt=pose_prompt,
        ) + f", {style_mod}"

        return {
            "3": {"class_type": "KSampler", "inputs": {
                "seed": seed, "steps": 30, "cfg": 8.0,
                "sampler_name": "euler_ancestral", "scheduler": "normal",
                "denoise": 1.0, "model": ["10", 0], "positive": ["6", 0],
                "negative": ["7", 0], "latent_image": ["5", 0],
            }},
            "4": {"class_type": "CheckpointLoaderSimple",
                  "inputs": {"ckpt_name": self.model}},
            "5": {"class_type": "EmptyLatentImage",
                  "inputs": {"width": 512, "height": 512, "batch_size": 1}},
            "6": {"class_type": "CLIPTextEncode",
                  "inputs": {"text": positive, "clip": ["10", 1]}},
            "7": {"class_type": "CLIPTextEncode",
                  "inputs": {"text": _PIXEL_NEGATIVE, "clip": ["10", 1]}},
            "8": {"class_type": "VAEDecode",
                  "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
            "9": {"class_type": "SaveImage",
                  "inputs": {"filename_prefix": "gclub_pipe", "images": ["8", 0]}},
            "10": {"class_type": "LoraLoader", "inputs": {
                "lora_name": self.lora,
                "strength_model": self.lora_strength,
                "strength_clip": 1.0,
                "model": ["4", 0], "clip": ["4", 1],
            }},
        }

    def _queue_and_wait(self, workflow: dict, timeout: int = 300) -> Image.Image:
        """Queue a workflow and wait for the result image."""
        data = json.dumps({"prompt": workflow}).encode()
        req = urllib.request.Request(
            f"{self.url}/prompt", data=data,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req)
        prompt_id = json.loads(resp.read())["prompt_id"]

        for _ in range(timeout):
            time.sleep(1)
            try:
                resp = urllib.request.urlopen(f"{self.url}/history/{prompt_id}")
                history = json.loads(resp.read())
                if prompt_id in history and history[prompt_id].get("outputs"):
                    for node_out in history[prompt_id]["outputs"].values():
                        if "images" in node_out:
                            img_info = node_out["images"][0]
                            params = urllib.parse.urlencode({
                                "filename": img_info["filename"],
                                "subfolder": img_info.get("subfolder", ""),
                                "type": "output",
                            })
                            img_data = urllib.request.urlopen(f"{self.url}/view?{params}").read()
                            return Image.open(BytesIO(img_data)).convert("RGBA")
            except Exception:
                pass

        raise TimeoutError(f"Generation timed out after {timeout}s")

    def generate_raw(self, description: str, pose: str = "idle", seed: int = -1) -> Image.Image:
        """Generate a single raw 512x512 pixel art image."""
        workflow = self._build_workflow(description, pose, seed)
        return self._queue_and_wait(workflow)

    # ================================================================
    # Post-processing
    # ================================================================

    def process_image(self, img: Image.Image, palette_name: str = None) -> PixelCanvas:
        """Process raw SD output → game-ready PixelCanvas.

        Strategy: white bg prompt → remove white/near-white → crop → resize → outline.
        """
        w, h = img.size
        pixels = img.load()

        # 1. Remove white/light background (prompt forces white bg)
        for y in range(h):
            for x in range(w):
                r, g, b, a = pixels[x, y]
                # If pixel is near-white or very light gray → transparent
                if r > 210 and g > 210 and b > 210:
                    pixels[x, y] = (0, 0, 0, 0)

        # 2. Also flood-fill from edges to catch off-white backgrounds
        visited = set()
        border_seeds = []
        for bx in range(w):
            border_seeds.extend([(bx, 0), (bx, h-1)])
        for by in range(h):
            border_seeds.extend([(0, by), (w-1, by)])

        for sx, sy in border_seeds:
            if (sx, sy) in visited:
                continue
            stack = [(sx, sy)]
            while stack:
                cx, cy = stack.pop()
                if (cx, cy) in visited or not (0 <= cx < w and 0 <= cy < h):
                    continue
                visited.add((cx, cy))
                r, g, b, a = pixels[cx, cy]
                if a == 0 or (r > 180 and g > 180 and b > 180):
                    pixels[cx, cy] = (0, 0, 0, 0)
                    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        stack.append((cx+dx, cy+dy))

        # 3. Crop to content bounding box
        bbox = img.getbbox()
        if bbox:
            pad = 4
            x1 = max(0, bbox[0] - pad)
            y1 = max(0, bbox[1] - pad)
            x2 = min(w, bbox[2] + pad)
            y2 = min(h, bbox[3] + pad)
            # Make square
            cw, ch = x2 - x1, y2 - y1
            side = max(cw, ch)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            x1 = max(0, cx - side // 2)
            y1 = max(0, cy - side // 2)
            x2 = min(w, x1 + side)
            y2 = min(h, y1 + side)
            img = img.crop((x1, y1, x2, y2))

        # 4. Resize to target
        img = img.resize((self.target_size, self.target_size), Image.LANCZOS)

        # 5. Palette quantize
        if palette_name:
            img = self._quantize_palette(img, palette_name)

        # 6. Clean alpha
        pixels = img.load()
        for y in range(self.target_size):
            for x in range(self.target_size):
                r, g, b, a = pixels[x, y]
                pixels[x, y] = (r, g, b, 255 if a > 50 else 0)

        # 7. Convert to PixelCanvas
        canvas = PixelCanvas(self.target_size, self.target_size)
        for y in range(self.target_size):
            for x in range(self.target_size):
                r, g, b, a = img.getpixel((x, y))
                if a > 0:
                    canvas._pixels[y][x] = (r, g, b, 255)

        # 8. Colored outline
        canvas.colored_outline()
        return canvas

    def _remove_bg(self, img: Image.Image) -> Image.Image:
        """Remove background via edge-only flood fill.

        Only floods from the image borders inward, never starts from center.
        This protects the character even if it shares colors with the background.
        Uses a two-pass approach: first identify definite background from edges,
        then clean up remaining noise.
        """
        pixels = img.load()
        w, h = img.size

        # Sample background color from the 4 edge midpoints (more reliable than corners)
        edge_samples = [
            pixels[w//2, 0], pixels[w//2, h-1],
            pixels[0, h//2], pixels[w-1, h//2],
            pixels[0, 0], pixels[w-1, 0], pixels[0, h-1], pixels[w-1, h-1],
        ]
        # Find most common edge color
        from collections import Counter
        color_counts = Counter()
        for p in edge_samples:
            # Round to nearest 10 to group similar colors
            key = (p[0]//10*10, p[1]//10*10, p[2]//10*10)
            color_counts[key] += 1
        bg_key = color_counts.most_common(1)[0][0]
        bg_r, bg_g, bg_b = bg_key

        tolerance = 55
        visited = set()

        # ONLY seed from border pixels — never from interior
        border_seeds = []
        for x in range(w):
            border_seeds.append((x, 0))
            border_seeds.append((x, h - 1))
        for y in range(h):
            border_seeds.append((0, y))
            border_seeds.append((w - 1, y))

        stack = border_seeds[:]
        while stack:
            x, y = stack.pop()
            if (x, y) in visited or not (0 <= x < w and 0 <= y < h):
                continue
            visited.add((x, y))
            r, g, b = pixels[x, y][0], pixels[x, y][1], pixels[x, y][2]
            # Compare with rounded bg color
            dist = abs(r//10*10 - bg_r) + abs(g//10*10 - bg_g) + abs(b//10*10 - bg_b)
            if dist < tolerance:
                pixels[x, y] = (0, 0, 0, 0)
                for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                    stack.append((x + dx, y + dy))

        return img

    def _crop_center(self, img: Image.Image) -> Image.Image:
        """Crop to bounding box of content, keep square."""
        bbox = img.getbbox()
        if not bbox:
            return img
        x1, y1, x2, y2 = bbox
        # Pad slightly
        pad = max((x2-x1), (y2-y1)) // 10
        x1, y1 = max(0, x1-pad), max(0, y1-pad)
        x2, y2 = min(img.width, x2+pad), min(img.height, y2+pad)
        # Make square
        w, h = x2 - x1, y2 - y1
        side = max(w, h)
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        x1 = max(0, cx - side // 2)
        y1 = max(0, cy - side // 2)
        return img.crop((x1, y1, x1 + side, y1 + side))

    def _quantize_palette(self, img: Image.Image, palette_name: str) -> Image.Image:
        pal = get_palette(palette_name)
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                if a > 0:
                    pixels[x, y] = (*pal.closest(r, g, b), a)
        return img

    def _clean_alpha(self, img: Image.Image) -> Image.Image:
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                pixels[x, y] = (r, g, b, 255 if a > 80 else 0)
        return img

    # ================================================================
    # High-level API
    # ================================================================

    def create_character(
        self,
        description: str,
        output_dir: str = "./pixel_assets",
        name: str = "character",
        animations: List[str] = None,
        palette: str = None,
        seed: int = -1,
    ) -> dict:
        """Generate a complete character asset pack.

        Creates: idle sprite, animation frames for each requested animation,
        spritesheet, GIF, and individual frame PNGs.

        Args:
            description: Character description (e.g., "medieval knight with silver armor").
            output_dir: Where to save all assets.
            name: Character name (used for filenames).
            animations: List of animations to generate. Default: ["idle", "walk", "attack", "hurt"].
                       Each animation generates 3-4 pose variants → interpolated into smooth frames.
            palette: Optional palette name for color quantization.
            seed: Random seed for reproducibility (-1 = random).

        Returns:
            Dict with paths to all generated assets.

        Example:
            >>> pipe = PixelPipeline(style="deadcells")
            >>> assets = pipe.create_character(
            ...     "fire mage with red robes and flame staff",
            ...     name="fire_mage",
            ...     output_dir="./game_assets/"
            ... )
            >>> print(assets["idle_gif"])  # → ./game_assets/fire_mage/fire_mage_idle.gif
        """
        if not self._check_server():
            raise ConnectionError(
                "Cannot connect to ComfyUI. Start it with: "
                "cd ~/ComfyUI && source venv/bin/activate && python main.py --listen"
            )

        if animations is None:
            animations = ["idle", "walk", "attack", "hurt"]

        if seed < 0:
            seed = random.randint(0, 2**32)

        out = Path(output_dir) / name
        out.mkdir(parents=True, exist_ok=True)
        (out / "frames").mkdir(exist_ok=True)

        result = {"name": name, "dir": str(out), "sprites": {}, "sheets": {}, "gifs": {}}

        # --- Generate base idle sprite ---
        print(f"[{name}] Generating idle sprite...")
        raw = self.generate_raw(description, pose="idle", seed=seed)
        idle_canvas = self.process_image(raw, palette)
        idle_path = str(out / f"{name}_idle.png")
        idle_canvas.save(idle_path, scale=1)
        idle_canvas.save(str(out / f"{name}_idle_preview.png"), scale=8)
        result["sprites"]["idle"] = idle_path
        print(f"  idle: done")

        # --- Generate animation poses ---
        pose_map = {
            "idle":   ["idle"],
            "walk":   ["idle", "walk_1", "idle", "walk_2"],
            "attack": ["idle", "attack_1", "attack_2", "attack_3", "idle"],
            "hurt":   ["idle", "hurt", "hurt", "idle"],
            "cast":   ["idle", "cast", "cast", "idle"],
            "jump":   ["crouch", "jump", "jump", "idle"],
            "death":  ["hurt", "dead"],
        }

        all_anim_frames = {}

        for anim_name in animations:
            poses = pose_map.get(anim_name, ["idle"])
            frames = []

            print(f"[{name}] Generating {anim_name} ({len(poses)} poses)...")
            for i, pose in enumerate(poses):
                # Use consistent seed per character, vary by pose index
                pose_seed = seed + hash(pose) % 1000 + i
                raw = self.generate_raw(description, pose=pose, seed=pose_seed)
                canvas = self.process_image(raw, palette)
                frames.append(canvas)

                # Save individual frame
                frame_path = str(out / "frames" / f"{name}_{anim_name}_{i:02d}.png")
                canvas.save(frame_path)
                print(f"  {anim_name} frame {i+1}/{len(poses)}: done")

            all_anim_frames[anim_name] = frames

            # --- Build animation from frames ---
            anim = Animation(frames[0], fps=6)
            anim.frames = frames

            # Export SpriteSheet
            sheet_path = str(out / f"{name}_{anim_name}_sheet.png")
            anim.export_spritesheet(sheet_path, scale=1)
            anim.export_spritesheet(
                str(out / f"{name}_{anim_name}_sheet_preview.png"), scale=4
            )
            result["sheets"][anim_name] = sheet_path

            # Export GIF
            gif_path = str(out / f"{name}_{anim_name}.gif")
            anim.export_gif(gif_path, scale=4)
            result["gifs"][anim_name] = gif_path

            print(f"  {anim_name}: sheet + gif exported")

        # --- Export combined master spritesheet ---
        all_frames = []
        anim_ranges = {}
        idx = 0
        for anim_name in animations:
            frames = all_anim_frames.get(anim_name, [])
            anim_ranges[anim_name] = {"start": idx, "count": len(frames)}
            all_frames.extend(frames)
            idx += len(frames)

        if all_frames:
            meta = export_spritesheet_with_meta(
                all_frames, name, str(out), columns=max(len(f) for f in all_anim_frames.values())
            )
            meta["animations"] = anim_ranges
            # Overwrite meta with animation info
            (Path(out) / f"{name}.json").write_text(json.dumps(meta, indent=2))
            result["master_sheet"] = str(out / f"{name}.png")
            result["master_meta"] = str(out / f"{name}.json")

        # --- Summary ---
        total_frames = sum(len(f) for f in all_anim_frames.values())
        print(f"\n{'='*40}")
        print(f"  Character: {name}")
        print(f"  Size: {self.target_size}x{self.target_size}px")
        print(f"  Animations: {', '.join(animations)}")
        print(f"  Total frames: {total_frames}")
        print(f"  Output: {out}/")
        print(f"{'='*40}")

        return result

    def create_party(
        self,
        characters: Dict[str, str],
        output_dir: str = "./pixel_assets",
        animations: List[str] = None,
        palette: str = None,
    ) -> Dict[str, dict]:
        """Generate a full party of characters with consistent style.

        Args:
            characters: Dict of {name: description}.
            output_dir: Output directory.
            animations: Animations to generate per character.

        Returns:
            Dict of {name: asset_result}.

        Example:
            >>> pipe = PixelPipeline(style="classic")
            >>> party = pipe.create_party({
            ...     "knight": "medieval knight with silver armor and red cape",
            ...     "mage": "wizard in purple robes with magic staff",
            ...     "archer": "ranger with green cloak and bow",
            ... })
        """
        results = {}
        for name, desc in characters.items():
            print(f"\n--- Generating {name} ---")
            results[name] = self.create_character(
                desc, output_dir=output_dir, name=name,
                animations=animations, palette=palette,
            )
        return results

    def create_item(
        self,
        description: str,
        output_dir: str = "./pixel_assets",
        name: str = "item",
        palette: str = None,
    ) -> str:
        """Generate a single item/icon sprite.

        Example:
            >>> pipe.create_item("red health potion", name="hp_potion")
        """
        if not self._check_server():
            raise ConnectionError("ComfyUI not running")

        out = Path(output_dir) / "items"
        out.mkdir(parents=True, exist_ok=True)

        print(f"[item] Generating {name}...")
        prompt_desc = f"pixel art game item icon, {description}, single item, centered, no character"
        raw = self.generate_raw(prompt_desc, pose="idle")
        canvas = self.process_image(raw, palette)
        path = str(out / f"{name}.png")
        canvas.save(path)
        canvas.save(str(out / f"{name}_preview.png"), scale=8)
        print(f"  {name}: done → {path}")
        return path


# ================================================================
# One-shot convenience functions
# ================================================================

def create_game_assets(
    characters: Dict[str, str],
    items: Optional[Dict[str, str]] = None,
    output_dir: str = "./pixel_assets",
    style: str = "default",
    size: int = 32,
    animations: List[str] = None,
    palette: str = None,
) -> dict:
    """One function to generate a complete game asset pack.

    This is THE function LLMs should call. Everything is automatic.

    Args:
        characters: Dict of {name: description} for each character.
        items: Optional dict of {name: description} for items.
        output_dir: Where to save everything.
        style: Art style ("stardew", "deadcells", "terraria", "celeste", "classic").
        size: Sprite pixel size (32, 48, or 64).
        animations: List of animations per character (default: idle, walk, attack, hurt).
        palette: Optional palette name for color consistency.

    Returns:
        Dict with all asset paths.

    Example:
        >>> from gclub_pixel.pipeline import create_game_assets
        >>> assets = create_game_assets(
        ...     characters={
        ...         "knight": "medieval knight with silver plate armor and red cape, holding sword",
        ...         "mage": "wizard in purple robes with pointed hat and glowing staff",
        ...     },
        ...     items={
        ...         "hp_potion": "red health potion in glass bottle",
        ...         "mana_potion": "blue mana potion in crystal vial",
        ...     },
        ...     style="classic",
        ...     size=32,
        ... )
    """
    pipe = PixelPipeline(target_size=size, style=style)
    result = {"characters": {}, "items": {}}

    # Characters
    result["characters"] = pipe.create_party(
        characters, output_dir=output_dir,
        animations=animations, palette=palette,
    )

    # Items
    if items:
        for item_name, item_desc in items.items():
            result["items"][item_name] = pipe.create_item(
                item_desc, output_dir=output_dir,
                name=item_name, palette=palette,
            )

    print(f"\n{'='*50}")
    print(f"  ASSET PACK COMPLETE")
    print(f"  Characters: {len(characters)}")
    print(f"  Items: {len(items) if items else 0}")
    print(f"  Style: {style}")
    print(f"  Output: {output_dir}/")
    print(f"{'='*50}")

    return result
