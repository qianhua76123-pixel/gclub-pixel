"""Gemini AI 像素角色生成 - 一行代码出高质量像素画

需要先设置: export GEMINI_API_KEY="your-api-key"
或者: pip install google-genai
"""

from gclub_pixel import gemini_generate, GeminiPixel, PixelCanvas, Animation

# ===== 方式1: 一行代码生成 =====
# knight = gemini_generate("knight", style="deadcells", size=48)
# knight.save("output/ai_knight.png", scale=4)

# ===== 方式2: 批量生成不同角色 =====
gp = GeminiPixel()  # 读取 GEMINI_API_KEY 环境变量

# 中世纪队伍
roles = ["knight", "mage", "archer", "rogue", "healer"]
party = gp.generate_batch(roles, style="deadcells", size=48)

for name, sprite in zip(roles, party):
    sprite.save(f"output/ai_{name}.png", scale=4)
    print(f"  {name}: done")

# 横排合集
lineup = PixelCanvas(48 * 5 + 4 * 8, 48)
for i, sp in enumerate(party):
    lineup.paste(sp, i * 56, 0)
lineup.save("output/ai_party.png", scale=3)

# ===== 方式3: 同一角色多姿势 =====
knight_poses = gp.generate_sheet(
    "knight with silver armor and red cape",
    poses=["idle", "walk", "attack", "hurt"],
    style="deadcells",
    size=48,
)
for i, pose_name in enumerate(["idle", "walk", "attack", "hurt"]):
    knight_poses[i].save(f"output/ai_knight_{pose_name}.png", scale=4)

# ===== 方式4: 自定义描述 =====
custom = gp.generate(
    "female elf archer with emerald green cloak, silver hair, holding ornate bow",
    style="stardew",
    size=32,
    palette_name="endesga32",  # 量化到 Endesga32 调色板
)
custom.save("output/ai_elf_archer.png", scale=8)

# ===== 方式5: 怪物 =====
monsters = ["slime", "skeleton", "goblin", "dragon"]
for m in monsters:
    sprite = gp.generate(m, style="terraria", size=32)
    sprite.save(f"output/ai_{m}.png", scale=6)

# ===== 给AI生成的角色加动画 =====
knight_sprite = party[0]  # 骑士
anim = Animation(knight_sprite, fps=6)
anim.idle(amplitude=1, frames=4)
anim.export_gif("output/ai_knight_idle.gif", scale=4)

print("\\n=== Gemini像素角色生成完毕 ===")
print(f"  风格: deadcells / stardew / terraria")
print(f"  角色: {', '.join(roles)} + elf_archer")
print(f"  怪物: {', '.join(monsters)}")
print(f"  动画: knight idle GIF")
