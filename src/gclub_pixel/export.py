"""Multi-format export utilities.

Export pixel art to various game engine formats:
- PNG (default)
- SpriteSheet with JSON metadata
- Godot SpriteFrames .tres
- Phaser JSON Atlas
- GIF animation

Example:
    >>> export_spritesheet_with_meta(frames, "hero_walk", "./assets/")
    >>> export_godot_spriteframes(anim, "hero", "./godot_project/")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from PIL import Image

from gclub_pixel.canvas import PixelCanvas
from gclub_pixel.animation import Animation


def export_spritesheet_with_meta(
    frames: List[PixelCanvas],
    name: str,
    output_dir: str,
    columns: Optional[int] = None,
    padding: int = 0,
    scale: int = 1,
) -> dict:
    """Export frames as a spritesheet PNG + JSON metadata file.

    Creates two files:
        {name}.png  - the spritesheet image
        {name}.json - metadata (frame size, count, columns)

    Args:
        frames: List of PixelCanvas frames.
        name: Base filename (without extension).
        output_dir: Output directory.
        columns: Frames per row (default: all in one row).
        padding: Pixels between frames.
        scale: Upscale factor.

    Returns:
        Metadata dict.

    Example:
        >>> meta = export_spritesheet_with_meta(anim.frames, "walk", "./assets/")
    """
    if not frames:
        return {}

    d = Path(output_dir)
    d.mkdir(parents=True, exist_ok=True)

    n = len(frames)
    fw, fh = frames[0].width, frames[0].height
    cols = columns or n
    rows = (n + cols - 1) // cols

    sw = cols * fw + (cols - 1) * padding
    sh = rows * fh + (rows - 1) * padding
    sheet = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))

    for i, frame in enumerate(frames):
        col = i % cols
        row = i // cols
        x = col * (fw + padding)
        y = row * (fh + padding)
        sheet.paste(frame.to_image(), (x, y))

    if scale > 1:
        sheet = sheet.resize((sw * scale, sh * scale), Image.NEAREST)
        fw *= scale
        fh *= scale

    sheet.save(str(d / f"{name}.png"), "PNG")

    meta = {
        "name": name,
        "image": f"{name}.png",
        "frame_width": fw,
        "frame_height": fh,
        "frame_count": n,
        "columns": cols,
        "rows": rows,
        "padding": padding * scale,
    }

    (d / f"{name}.json").write_text(json.dumps(meta, indent=2))
    return meta


def export_phaser_atlas(
    frames: List[PixelCanvas],
    name: str,
    output_dir: str,
    scale: int = 1,
) -> dict:
    """Export as Phaser-compatible JSON atlas.

    Creates a texture atlas format that Phaser.js can load directly
    with `this.load.atlas(key, png, json)`.

    Example:
        >>> export_phaser_atlas(anim.frames, "hero_walk", "./public/assets/")
    """
    if not frames:
        return {}

    d = Path(output_dir)
    d.mkdir(parents=True, exist_ok=True)

    n = len(frames)
    fw, fh = frames[0].width * scale, frames[0].height * scale

    # Create horizontal strip
    sheet = Image.new("RGBA", (fw * n, fh), (0, 0, 0, 0))
    for i, frame in enumerate(frames):
        img = frame.to_image()
        if scale > 1:
            img = img.resize((fw, fh), Image.NEAREST)
        sheet.paste(img, (i * fw, 0))

    sheet.save(str(d / f"{name}.png"), "PNG")

    atlas = {
        "frames": {
            f"{name}_{i:03d}": {
                "frame": {"x": i * fw, "y": 0, "w": fw, "h": fh},
                "sourceSize": {"w": fw, "h": fh},
                "spriteSourceSize": {"x": 0, "y": 0, "w": fw, "h": fh},
            }
            for i in range(n)
        },
        "meta": {
            "image": f"{name}.png",
            "size": {"w": fw * n, "h": fh},
            "format": "RGBA8888",
        },
    }

    (d / f"{name}.json").write_text(json.dumps(atlas, indent=2))
    return atlas


def export_godot_spriteframes(
    animations: dict,
    output_dir: str,
    name: str = "sprites",
) -> str:
    """Export animations as a Godot SpriteFrames .tres resource.

    Args:
        animations: Dict of {anim_name: Animation} objects.
        output_dir: Godot project assets directory.
        name: Resource filename.

    Returns:
        Path to the .tres file.

    Example:
        >>> anims = {"idle": idle_anim, "walk": walk_anim}
        >>> export_godot_spriteframes(anims, "./godot/assets/")
    """
    d = Path(output_dir)
    d.mkdir(parents=True, exist_ok=True)

    # Export each animation's frames as individual PNGs
    lines = ['[gd_resource type="SpriteFrames" format=3]', ""]

    resource_idx = 1
    anim_data = []

    for anim_name, anim in animations.items():
        frame_paths = []
        for i, frame in enumerate(anim.frames):
            fname = f"{name}_{anim_name}_{i:03d}.png"
            frame.save(str(d / fname))
            frame_paths.append(fname)

        frames_str = ", ".join(
            f'{{"duration": 1.0, "texture": ExtResource("res://{d.name}/{fp}")}}'
            for fp in frame_paths
        )

        anim_data.append(
            f'{{"name": &"{anim_name}", "speed": {anim.fps}.0, "loop": true, "frames": [{frames_str}]}}'
        )

    lines.append("[resource]")
    lines.append(f'animations = [{", ".join(anim_data)}]')

    tres_path = d / f"{name}.tres"
    tres_path.write_text("\n".join(lines))
    return str(tres_path)
