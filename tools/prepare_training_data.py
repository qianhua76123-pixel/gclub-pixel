"""自动分类 + 切割 + 标注像素画训练数据。

将混合素材库自动处理为 LoRA 训练可用的格式：
1. 按来源目录名和图片特征自动分类（角色/武器/场景/道具/头像）
2. 检测 sprite sheet 并切割成单帧
3. 缩放到 512×512（训练目标尺寸）
4. 自动生成文本标注文件
5. 按风格聚类为多组训练集

用法:
    python tools/prepare_training_data.py /Users/qianhua/pixel-games ~/pixel_lora_data
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import List, Tuple, Dict
from collections import defaultdict

from PIL import Image


# ================================================================
# 配置
# ================================================================

TARGET_SIZE = 512  # SD训练标准尺寸
MIN_CONTENT_SIZE = 16  # 最小有效内容尺寸（太小的跳过）
MAX_FRAMES_PER_SHEET = 20  # sprite sheet最多切这么多帧

# 目录名 → 内容类型映射
DIR_TYPE_MAP = {
    "武器装备": "weapon",
    "道具": "item",
    "技能": "skill_effect",
    "头像": "portrait",
    "像素小人": "character",
    "人设": "character_design",
    "角色动作": "character_action",
    "场景": "scene",
    "megapont": "character",  # 俄国像素画家的角色作品
    "Characters": "character_walk",
    "村庄": "scene",
    "Assets": "scene",
}

# 内容类型 → 训练标注前缀
TYPE_CAPTIONS = {
    "character_walk": "pixel art character sprite, RPG walking animation, {style}, front view, game sprite",
    "character": "pixel art character, game character sprite, {style}, detailed pixel art",
    "character_design": "pixel art character design sheet, reference sheet, {style}, multiple views",
    "character_action": "pixel art character action sprite, animation frame, {style}, game sprite",
    "weapon": "pixel art weapon icon, game item, {style}, equipment sprite",
    "item": "pixel art item icon, game item, {style}, inventory icon",
    "skill_effect": "pixel art skill effect, magic spell animation, {style}, game effect",
    "portrait": "pixel art character portrait, face close-up, {style}, game portrait",
    "scene": "pixel art game scene, background tileset, {style}, environment",
}


# ================================================================
# 工具函数
# ================================================================

def detect_content_type(filepath: str, parent_dirs: List[str]) -> str:
    """从文件路径的父目录名推断内容类型。"""
    path_str = "/".join(parent_dirs).lower()
    for keyword, content_type in DIR_TYPE_MAP.items():
        if keyword.lower() in path_str or keyword in path_str:
            return content_type
    return "unknown"


def is_sprite_sheet(img: Image.Image) -> bool:
    """检测图片是否是 sprite sheet（多帧合一）。"""
    w, h = img.size
    # RPG Maker XP 标准: 128×192 (4×3格，每格32×48)
    if w == 128 and h == 192:
        return True
    # RPG Maker XP 加大版: 160×216
    if w == 160 and h == 216:
        return True
    # 通用检测：宽高比很大，且宽度是某个小数的整数倍
    if w > h * 2 and w > 128:
        return True
    if h > w * 2 and h > 128:
        return True
    # 方形但很大的可能是图标合集
    if w > 256 and h > 256 and w == h:
        return True
    # 检查是否有规律性网格
    if w % 32 == 0 and h % 32 == 0 and (w // 32) * (h // 32) > 4:
        return True
    return False


def split_rpgmaker_sheet(img: Image.Image) -> List[Image.Image]:
    """切割 RPG Maker XP 格式的行走图（4方向×3帧=12格）。"""
    w, h = img.size

    if w == 128 and h == 192:
        fw, fh = 32, 48
    elif w == 160 and h == 216:
        fw, fh = 40, 54
    else:
        # 通用: 猜测4列
        cols = 4
        rows = 3
        fw = w // cols
        fh = h // rows

    frames = []
    cols = w // fw
    rows = h // fh

    for row in range(min(rows, 4)):
        for col in range(min(cols, 4)):
            x1, y1 = col * fw, row * fh
            frame = img.crop((x1, y1, x1 + fw, y1 + fh))
            # 检查帧是否有内容
            if frame.mode == "RGBA":
                content = sum(1 for px in frame.getdata() if px[3] > 10)
            else:
                content = sum(1 for px in frame.getdata() if sum(px[:3]) < 250 * 3)
            if content > fw * fh * 0.05:  # 至少5%有内容
                frames.append(frame)

    return frames[:MAX_FRAMES_PER_SHEET]


def split_generic_sheet(img: Image.Image) -> List[Image.Image]:
    """切割通用 sprite sheet，尝试检测网格大小。"""
    w, h = img.size
    frames = []

    # 尝试常见的帧大小
    for frame_size in [64, 48, 32, 96, 128]:
        if w % frame_size == 0 and h % frame_size == 0:
            cols = w // frame_size
            rows = h // frame_size
            if 2 <= cols * rows <= MAX_FRAMES_PER_SHEET:
                for row in range(rows):
                    for col in range(cols):
                        x1, y1 = col * frame_size, row * frame_size
                        frame = img.crop((x1, y1, x1 + frame_size, y1 + frame_size))
                        frames.append(frame)
                return frames

    # 无法检测网格，按比例切
    if w > h * 1.5:
        # 横向排列
        n = round(w / h)
        fw = w // n
        for i in range(min(n, MAX_FRAMES_PER_SHEET)):
            frames.append(img.crop((i * fw, 0, (i + 1) * fw, h)))
    elif h > w * 1.5:
        n = round(h / w)
        fh = h // n
        for i in range(min(n, MAX_FRAMES_PER_SHEET)):
            frames.append(img.crop((0, i * fh, w, (i + 1) * fh)))

    return frames if frames else [img]


def resize_for_training(img: Image.Image, target: int = TARGET_SIZE) -> Image.Image:
    """缩放到训练尺寸，保持像素画清晰度。"""
    w, h = img.size
    # 先用 NEAREST 放大到接近目标尺寸
    scale = max(1, target // max(w, h))
    if scale > 1:
        img = img.resize((w * scale, h * scale), Image.NEAREST)

    # 再裁切/填充到正方形
    w, h = img.size
    side = max(w, h)
    square = Image.new("RGBA", (side, side), (255, 255, 255, 255))
    offset_x = (side - w) // 2
    offset_y = (side - h) // 2
    if img.mode == "RGBA":
        square.paste(img, (offset_x, offset_y), img)
    else:
        square.paste(img, (offset_x, offset_y))

    # 最终缩放到目标
    if side != target:
        square = square.resize((target, target), Image.NEAREST)

    return square.convert("RGB")


def detect_style(img: Image.Image) -> str:
    """根据图片颜色特征粗略判断风格。"""
    small = img.resize((32, 32), Image.NEAREST).convert("RGB")
    pixels = list(small.getdata())

    avg_r = sum(p[0] for p in pixels) // len(pixels)
    avg_g = sum(p[1] for p in pixels) // len(pixels)
    avg_b = sum(p[2] for p in pixels) // len(pixels)
    brightness = (avg_r + avg_g + avg_b) // 3

    # 颜色数量
    unique_colors = len(set(pixels))

    if brightness < 80:
        return "dark_detailed"
    elif unique_colors < 20:
        return "minimal"
    elif brightness > 180:
        return "cute_bright"
    else:
        return "retro_rpg"


def generate_caption(content_type: str, style: str, filename: str) -> str:
    """生成训练标注文本。"""
    template = TYPE_CAPTIONS.get(content_type, "pixel art, game sprite, {style}")
    caption = template.format(style=style)

    # 从文件名中提取额外信息
    name = Path(filename).stem.lower()
    if "knight" in name or "骑士" in name:
        caption += ", knight character"
    elif "mage" in name or "法师" in name or "魔法" in name:
        caption += ", mage character"
    elif "dragon" in name or "龙" in name:
        caption += ", dragon monster"

    return caption


# ================================================================
# 主流程
# ================================================================

def process_dataset(input_dir: str, output_dir: str):
    """处理整个素材库。"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    stats = defaultdict(int)
    processed = 0
    errors = 0

    # 收集所有图片
    image_files = []
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.webp"):
        image_files.extend(input_path.rglob(ext))

    print(f"发现 {len(image_files)} 张图片")
    print(f"输出目录: {output_path}")
    print()

    for filepath in image_files:
        try:
            # 获取相对路径的父目录
            rel = filepath.relative_to(input_path)
            parent_dirs = [p.name for p in rel.parents if p.name]

            # 检测内容类型
            content_type = detect_content_type(str(filepath), parent_dirs)

            # 打开图片
            img = Image.open(filepath)
            if img.mode == "P":
                img = img.convert("RGBA")

            # 检测是否是 sprite sheet
            if is_sprite_sheet(img):
                if content_type == "character_walk":
                    frames = split_rpgmaker_sheet(img)
                else:
                    frames = split_generic_sheet(img)
            else:
                frames = [img]

            # 处理每一帧
            for i, frame in enumerate(frames):
                # 跳过太小的
                if frame.width < MIN_CONTENT_SIZE or frame.height < MIN_CONTENT_SIZE:
                    continue

                # 检测风格
                style = detect_style(frame)

                # 创建输出子目录: {类型}/{风格}/
                type_dir = output_path / content_type / style
                type_dir.mkdir(parents=True, exist_ok=True)

                # 生成唯一文件名
                frame_hash = hashlib.md5(frame.tobytes()[:1000]).hexdigest()[:8]
                frame_name = f"{filepath.stem}_{i:02d}_{frame_hash}"

                # 缩放到训练尺寸
                training_img = resize_for_training(frame)

                # 保存图片
                img_path = type_dir / f"{frame_name}.png"
                training_img.save(str(img_path), "PNG")

                # 生成标注
                caption = generate_caption(content_type, style, filepath.name)
                txt_path = type_dir / f"{frame_name}.txt"
                txt_path.write_text(caption)

                stats[f"{content_type}/{style}"] += 1
                processed += 1

            if processed % 200 == 0 and processed > 0:
                print(f"  已处理 {processed} 帧...")

        except Exception as e:
            errors += 1
            if errors <= 10:
                print(f"  Error: {filepath.name}: {e}")

    # 汇总报告
    print(f"\n{'='*50}")
    print(f"  处理完成!")
    print(f"  输入图片: {len(image_files)}")
    print(f"  输出帧数: {processed}")
    print(f"  错误数: {errors}")
    print(f"{'='*50}")
    print(f"\n按类型/风格分布:")
    for key in sorted(stats.keys()):
        print(f"  {key}: {stats[key]} 帧")

    # 保存统计
    stats_path = output_path / "stats.json"
    stats_path.write_text(json.dumps(dict(stats), indent=2, ensure_ascii=False))
    print(f"\n统计已保存到: {stats_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python prepare_training_data.py <素材目录> <输出目录>")
        print("示例: python prepare_training_data.py ~/pixel-games ~/pixel_lora_data")
        sys.exit(1)

    process_dataset(sys.argv[1], sys.argv[2])
