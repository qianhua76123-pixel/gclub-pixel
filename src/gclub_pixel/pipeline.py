"""End-to-end pixel art pipeline: ComfyUI → consistent characters → game assets.

Proven workflow:
1. txt2img generates reference idle frame (white background)
2. img2img uses reference to generate pose variants (consistent character)
3. White background removed via simple RGB threshold
4. Resize + outline → game-ready PixelCanvas
5. Assemble animation frames → SpriteSheet + GIF

Example:
    >>> from gclub_pixel.pipeline import PixelPipeline
    >>> pipe = PixelPipeline()
    >>> assets = pipe.create_character("medieval knight with silver armor")
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
from typing import Dict, List, Optional

from PIL import Image

from gclub_pixel.canvas import PixelCanvas
from gclub_pixel.animation import Animation
from gclub_pixel.export import export_spritesheet_with_meta


# ================================================================
# Prompts
# ================================================================

_STYLE_MODS = {
    "stardew":  "stardew valley style, warm colors, cute chibi, cozy",
    "deadcells": "dead cells style, dark detailed shading, glowing accents",
    "terraria": "terraria style, colorful vibrant, visible armor details",
    "celeste":  "celeste style, clean minimal, strong silhouette",
    "classic":  "SNES RPG style, final fantasy, chrono trigger, 16-bit era",
    "default":  "retro RPG style, clean pixel art",
}

_POSE_DESC = {
    "idle":     "standing idle, relaxed, arms at sides",
    "walk_1":   "walking, left foot forward, mid-stride",
    "walk_2":   "walking, right foot forward, mid-stride",
    "attack_1": "wind-up attack pose, weapon pulled back",
    "attack_2": "swinging weapon forward, action pose",
    "hurt":     "taking damage, recoiling backward",
    "cast":     "casting magic, hands glowing",
    "jump":     "jumping, feet off ground",
}

_NEGATIVE = (
    "blurry, realistic, 3d, smooth, anti-aliased, gradient, text, watermark, "
    "multiple characters, background scenery, low quality, deformed, ugly, painted"
)


def _build_positive(desc: str, pose: str, style: str) -> str:
    pose_text = _POSE_DESC.get(pose, "standing idle")
    style_text = _STYLE_MODS.get(style, _STYLE_MODS["default"])
    return (
        f"pixel art sprite, 16-bit game character, {desc}, "
        f"{pose_text}, front view, full body, centered, "
        f"plain white background, white backdrop, "
        f"sharp pixels, limited palette, dark outlines, "
        f"{style_text}, masterpiece, high quality"
    )


# ================================================================
# ComfyUI helpers
# ================================================================

def _comfy_request(url: str, data=None, method="GET") -> dict:
    """Make a request to ComfyUI API."""
    if data is not None:
        req = urllib.request.Request(
            url, data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"},
        )
    else:
        req = urllib.request.Request(url)
    resp = urllib.request.urlopen(req, timeout=10)
    return json.loads(resp.read())


def _upload_image(server: str, img: Image.Image, filename: str) -> str:
    """Upload a PIL Image to ComfyUI's input folder."""
    buf = BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    img_bytes = buf.getvalue()

    boundary = "----GClubUpload"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'.encode())
    body.extend(b"Content-Type: image/png\r\n\r\n")
    body.extend(img_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        f"{server}/upload/image",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    return result.get("name", filename)


def _queue_and_wait(server: str, workflow: dict, timeout: int = 180) -> Image.Image:
    """Queue a workflow and wait for result."""
    resp = _comfy_request(f"{server}/prompt", data={"prompt": workflow})
    prompt_id = resp["prompt_id"]

    for _ in range(timeout):
        time.sleep(1)
        try:
            hist_resp = urllib.request.urlopen(f"{server}/history/{prompt_id}", timeout=5)
            history = json.loads(hist_resp.read())
            if prompt_id in history and history[prompt_id].get("outputs"):
                for node_out in history[prompt_id]["outputs"].values():
                    if "images" in node_out:
                        info = node_out["images"][0]
                        params = urllib.parse.urlencode({
                            "filename": info["filename"],
                            "subfolder": info.get("subfolder", ""),
                            "type": "output",
                        })
                        img_data = urllib.request.urlopen(
                            f"{server}/view?{params}", timeout=15
                        ).read()
                        return Image.open(BytesIO(img_data)).convert("RGBA")
        except Exception:
            pass

    raise TimeoutError(f"Generation timed out ({timeout}s)")


# ================================================================
# Workflow builders
# ================================================================

def _txt2img_workflow(model: str, lora: str, lora_str: float,
                      positive: str, negative: str, seed: int) -> dict:
    """Standard txt2img with LoRA."""
    return {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": model}},
        "2": {"class_type": "LoraLoader", "inputs": {
            "lora_name": lora, "strength_model": lora_str,
            "strength_clip": 1.0, "model": ["1", 0], "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode",
              "inputs": {"text": positive, "clip": ["2", 1]}},
        "4": {"class_type": "CLIPTextEncode",
              "inputs": {"text": negative, "clip": ["2", 1]}},
        "5": {"class_type": "EmptyLatentImage",
              "inputs": {"width": 512, "height": 512, "batch_size": 1}},
        "6": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 28, "cfg": 7.5,
            "sampler_name": "euler_ancestral", "scheduler": "normal",
            "denoise": 1.0,
            "model": ["2", 0], "positive": ["3", 0],
            "negative": ["4", 0], "latent_image": ["5", 0]}},
        "7": {"class_type": "VAEDecode",
              "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
        "8": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "gclub_ref", "images": ["7", 0]}},
    }


def _img2img_workflow(model: str, lora: str, lora_str: float,
                      positive: str, negative: str,
                      ref_name: str, seed: int, denoise: float) -> dict:
    """img2img: uses reference image for character consistency."""
    return {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": model}},
        "2": {"class_type": "LoraLoader", "inputs": {
            "lora_name": lora, "strength_model": lora_str,
            "strength_clip": 1.0, "model": ["1", 0], "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode",
              "inputs": {"text": positive, "clip": ["2", 1]}},
        "4": {"class_type": "CLIPTextEncode",
              "inputs": {"text": negative, "clip": ["2", 1]}},
        "5": {"class_type": "LoadImage",
              "inputs": {"image": ref_name}},
        "6": {"class_type": "VAEEncode",
              "inputs": {"pixels": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "KSampler", "inputs": {
            "seed": seed, "steps": 28, "cfg": 7.5,
            "sampler_name": "euler_ancestral", "scheduler": "normal",
            "denoise": denoise,
            "model": ["2", 0], "positive": ["3", 0],
            "negative": ["4", 0], "latent_image": ["6", 0]}},
        "8": {"class_type": "VAEDecode",
              "inputs": {"samples": ["7", 0], "vae": ["1", 2]}},
        "9": {"class_type": "SaveImage",
              "inputs": {"filename_prefix": "gclub_pose", "images": ["8", 0]}},
    }


# ================================================================
# Image processing
# ================================================================

def remove_white_bg(img: Image.Image, threshold: int = 230) -> Image.Image:
    """Remove white/near-white background from a pixel art image.

    Simple and reliable: any pixel where R, G, B are all > threshold
    becomes transparent. This works perfectly for images generated with
    'white background' in the prompt.
    """
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r > threshold and g > threshold and b > threshold:
                pixels[x, y] = (0, 0, 0, 0)
    return img


def remove_dark_bg(img: Image.Image, threshold: int = 35) -> Image.Image:
    """Remove dark/near-black background. Fallback when SD ignores white bg prompt."""
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r < threshold and g < threshold and b < threshold:
                pixels[x, y] = (0, 0, 0, 0)
    return img


def smart_remove_bg(img: Image.Image) -> Image.Image:
    """Auto-detect background color and remove it.

    Samples corners to detect whether bg is white or dark, then applies
    the appropriate removal. Falls back to edge flood fill if needed.
    """
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size

    # Sample 4 corners + 4 edge midpoints
    samples = [
        pixels[2, 2], pixels[w-3, 2], pixels[2, h-3], pixels[w-3, h-3],
        pixels[w//2, 2], pixels[w//2, h-3], pixels[2, h//2], pixels[w-3, h//2],
    ]
    avg_r = sum(s[0] for s in samples) // len(samples)
    avg_g = sum(s[1] for s in samples) // len(samples)
    avg_b = sum(s[2] for s in samples) // len(samples)
    brightness = (avg_r + avg_g + avg_b) / 3

    if brightness > 180:
        # White/light background
        return remove_white_bg(img)
    elif brightness < 60:
        # Dark/black background
        return remove_dark_bg(img)
    else:
        # Mid-tone bg: flood fill from edges
        visited = set()
        border = []
        for bx in range(w):
            border.extend([(bx, 0), (bx, h-1)])
        for by in range(h):
            border.extend([(0, by), (w-1, by)])

        for sx, sy in border:
            if (sx, sy) in visited:
                continue
            stack = [(sx, sy)]
            while stack:
                cx, cy = stack.pop()
                if (cx, cy) in visited or not (0 <= cx < w and 0 <= cy < h):
                    continue
                visited.add((cx, cy))
                r, g, b, a = pixels[cx, cy]
                dist = abs(r - avg_r) + abs(g - avg_g) + abs(b - avg_b)
                if dist < 80:
                    pixels[cx, cy] = (0, 0, 0, 0)
                    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        stack.append((cx+dx, cy+dy))
        return img


def crop_to_content(img: Image.Image) -> Image.Image:
    """Crop to bounding box of non-transparent pixels, keep square."""
    bbox = img.getbbox()
    if not bbox:
        return img
    x1, y1, x2, y2 = bbox
    # Small padding
    pad = max(4, (x2 - x1) // 20)
    x1, y1 = max(0, x1 - pad), max(0, y1 - pad)
    x2, y2 = min(img.width, x2 + pad), min(img.height, y2 + pad)
    # Make square
    w, h = x2 - x1, y2 - y1
    side = max(w, h)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    x1 = max(0, cx - side // 2)
    y1 = max(0, cy - side // 2)
    x2 = min(img.width, x1 + side)
    y2 = min(img.height, y1 + side)
    return img.crop((x1, y1, x2, y2))


def to_pixel_canvas(img: Image.Image, size: int) -> PixelCanvas:
    """Convert PIL Image to PixelCanvas at target size."""
    img = img.resize((size, size), Image.LANCZOS)
    canvas = PixelCanvas(size, size)
    for y in range(size):
        for x in range(size):
            r, g, b, a = img.getpixel((x, y))
            if a > 50:
                canvas._pixels[y][x] = (r, g, b, 255)
    canvas.colored_outline()
    return canvas


def process_raw(img: Image.Image, size: int) -> PixelCanvas:
    """Full processing: smart bg removal → crop → resize → outline."""
    img = smart_remove_bg(img)
    img = crop_to_content(img)
    return to_pixel_canvas(img, size)


# ================================================================
# Pipeline
# ================================================================

class PixelPipeline:
    """Complete pixel art generation pipeline.

    Example:
        >>> pipe = PixelPipeline()
        >>> assets = pipe.create_character("knight with silver armor", name="knight")
    """

    def __init__(
        self,
        server: str = "http://localhost:8188",
        model: str = "dreamshaper_8.safetensors",
        lora: str = "pixel-art-sd15.safetensors",
        lora_strength: float = 1.2,
        size: int = 48,
        style: str = "default",
    ):
        self.server = server
        self.model = model
        self.lora = lora
        self.lora_str = lora_strength
        self.size = size
        self.style = style

    def _check(self):
        try:
            urllib.request.urlopen(f"{self.server}/system_stats", timeout=3)
            return True
        except:
            return False

    def generate_reference(self, desc: str, seed: int) -> Image.Image:
        """Step 1: Generate idle reference frame via txt2img."""
        prompt = _build_positive(desc, "idle", self.style)
        wf = _txt2img_workflow(self.model, self.lora, self.lora_str, prompt, _NEGATIVE, seed)
        return _queue_and_wait(self.server, wf)

    def generate_pose(self, desc: str, ref_image: Image.Image,
                      pose: str, seed: int, denoise: float = 0.5) -> Image.Image:
        """Step 2: Generate pose variant via img2img from reference."""
        ref_name = _upload_image(self.server, ref_image, f"gclub_ref_{pose}.png")
        prompt = _build_positive(desc, pose, self.style)
        wf = _img2img_workflow(self.model, self.lora, self.lora_str,
                               prompt, _NEGATIVE, ref_name, seed, denoise)
        return _queue_and_wait(self.server, wf)

    def create_character(
        self,
        description: str,
        name: str = "character",
        output_dir: str = "./pixel_assets",
        animations: List[str] = None,
        seed: int = -1,
    ) -> dict:
        """Generate a complete character asset pack with consistent appearance.

        Pipeline:
        1. txt2img → reference idle frame (establishes character look)
        2. img2img → pose variants from reference (consistent colors/style)
        3. Remove white background → crop → resize → outline
        4. Assemble into SpriteSheet + GIF

        Args:
            description: Character description.
            name: Character name for filenames.
            output_dir: Output directory.
            animations: Which animations to generate (default: idle, walk, attack, hurt).
            seed: Random seed (-1 = random).

        Returns:
            Dict with all asset file paths.
        """
        if not self._check():
            raise ConnectionError("ComfyUI not running. Start: cd ~/ComfyUI && source venv/bin/activate && python main.py --listen")

        if animations is None:
            animations = ["idle", "walk", "attack", "hurt"]
        if seed < 0:
            seed = random.randint(0, 2**32)

        out = Path(output_dir) / name
        out.mkdir(parents=True, exist_ok=True)
        (out / "frames").mkdir(exist_ok=True)

        result = {"name": name, "sprites": {}, "sheets": {}, "gifs": {}}

        # === Step 1: Reference idle frame ===
        print(f"[{name}] Step 1: Generating reference idle (txt2img)...")
        ref_raw = self.generate_reference(description, seed)
        ref_raw.save(str(out / "_reference_raw.png"))
        idle_canvas = process_raw(ref_raw, self.size)
        idle_canvas.save(str(out / f"{name}_idle.png"))
        idle_canvas.save(str(out / f"{name}_idle_8x.png"), scale=8)
        result["sprites"]["idle"] = str(out / f"{name}_idle.png")

        content_px = sum(1 for y in range(self.size) for x in range(self.size) if idle_canvas.get_pixel(x, y)[3] > 0)
        print(f"  Reference: {content_px}px content")

        if content_px < 50:
            print(f"  WARNING: Low content. Background removal may have eaten the character.")

        # === Step 2: Pose variants via img2img ===
        pose_map = {
            "idle":   [("idle", 0.3)],
            "walk":   [("idle", 0.0), ("walk_1", 0.5), ("idle", 0.0), ("walk_2", 0.5)],
            "attack": [("idle", 0.0), ("attack_1", 0.55), ("attack_2", 0.6), ("idle", 0.0)],
            "hurt":   [("idle", 0.0), ("hurt", 0.5), ("hurt", 0.45), ("idle", 0.0)],
        }

        pose_cache = {"idle": idle_canvas}
        all_anim_frames = {}

        for anim in animations:
            poses = pose_map.get(anim, [("idle", 0.0)])
            frames = []

            print(f"[{name}] Step 2: Generating {anim} ({len(poses)} frames, img2img)...")
            for i, (pose, denoise) in enumerate(poses):
                if denoise == 0.0 and pose in pose_cache:
                    frames.append(pose_cache[pose])
                    print(f"  {anim}[{i}] {pose}: reuse cached")
                    continue

                if pose in pose_cache and denoise < 0.35:
                    frames.append(pose_cache[pose])
                    print(f"  {anim}[{i}] {pose}: reuse (low denoise)")
                    continue

                pose_seed = seed + hash(f"{pose}_{i}") % 10000
                print(f"  {anim}[{i}] {pose} (denoise={denoise})...", end=" ", flush=True)
                try:
                    raw = self.generate_pose(description, ref_raw, pose, pose_seed, denoise)
                    canvas = process_raw(raw, self.size)
                    px = sum(1 for y in range(self.size) for x in range(self.size) if canvas.get_pixel(x, y)[3] > 0)
                    print(f"{px}px")

                    if px < 50:
                        print(f"    Low content, using idle fallback")
                        canvas = idle_canvas

                    pose_cache[pose] = canvas
                    frames.append(canvas)
                except Exception as e:
                    print(f"failed: {e}, using idle")
                    frames.append(idle_canvas)

                # Save individual frame
                canvas.save(str(out / "frames" / f"{name}_{anim}_{i:02d}.png"))

            all_anim_frames[anim] = frames

            # === Step 3: Assemble animation ===
            animation = Animation(frames[0], fps=6)
            animation.frames = frames

            sheet_path = str(out / f"{name}_{anim}_sheet.png")
            animation.export_spritesheet(sheet_path, scale=4)
            result["sheets"][anim] = sheet_path

            gif_path = str(out / f"{name}_{anim}.gif")
            animation.export_gif(gif_path, scale=4)
            result["gifs"][anim] = gif_path

            print(f"  {anim}: sheet + gif exported")

        # === Summary ===
        total = sum(len(f) for f in all_anim_frames.values())
        print(f"\n{'='*40}")
        print(f"  {name}: {total} frames, {len(animations)} animations")
        print(f"  Output: {out}/")
        print(f"{'='*40}")

        return result


# ================================================================
# Convenience
# ================================================================

def create_game_assets(
    characters: Dict[str, str],
    output_dir: str = "./pixel_assets",
    style: str = "default",
    size: int = 48,
    animations: List[str] = None,
) -> dict:
    """One function to generate a full game asset pack.

    Example:
        >>> from gclub_pixel.pipeline import create_game_assets
        >>> assets = create_game_assets({
        ...     "knight": "medieval knight with silver armor and red cape",
        ...     "mage": "wizard in purple robes with magic staff",
        ... })
    """
    pipe = PixelPipeline(size=size, style=style)
    results = {}
    for name, desc in characters.items():
        print(f"\n{'='*50}")
        print(f"  Generating: {name}")
        print(f"{'='*50}")
        results[name] = pipe.create_character(desc, name=name, output_dir=output_dir, animations=animations)
    return results
