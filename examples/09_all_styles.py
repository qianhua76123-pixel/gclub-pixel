"""所有风格对比 - 同一骑士在5种游戏风格下的样子"""

from gclub_pixel import create_styled_character, PixelCanvas, Animation

# ===== 5种风格 x 同一角色配色 =====
styles = ["stardew", "celeste", "undertale", "terraria", "deadcells"]
labels = ["星露谷", "蔚蓝", "传说之下", "泰拉瑞亚", "死亡细胞"]

chars = []
for style in styles:
    ch = create_styled_character(
        style=style,
        role="warrior",
        skin_color=(220, 185, 145),
        hair_color=(140, 90, 40),
        armor_color=(160, 165, 180),
        accent_color=(180, 50, 50),
        eye_color=(50, 70, 120),
        hair_style="short",
    )
    chars.append(ch)
    ch.save(f"output/style_{style}.png", scale=6)
    print(f"  {style}: {ch.width}x{ch.height}")

# ===== 不同职业 (Dead Cells风格) =====
roles = {
    "knight": {"armor_color": (160, 165, 180), "accent_color": (180, 50, 50), "hair_color": (130, 90, 45), "hair_style": "short"},
    "mage": {"armor_color": (95, 55, 130), "accent_color": (80, 160, 220), "hair_color": (210, 210, 220), "hair_style": "long"},
    "archer": {"armor_color": (65, 110, 55), "accent_color": (180, 140, 50), "hair_color": (175, 130, 55), "hair_style": "ponytail"},
    "rogue": {"armor_color": (55, 55, 65), "accent_color": (200, 60, 60), "hair_color": (40, 38, 35), "hair_style": "spiky"},
    "healer": {"armor_color": (210, 205, 195), "accent_color": (200, 175, 55), "hair_color": (120, 80, 40), "hair_style": "messy"},
}

dc_chars = []
for role_name, params in roles.items():
    ch = create_styled_character("deadcells", role=role_name, skin_color=(215, 180, 140), eye_color=(50, 70, 120), **params)
    dc_chars.append(ch)
    ch.save(f"output/dc_{role_name}.png", scale=4)

# Dead Cells队伍合集
lineup = PixelCanvas(48 * 5 + 4 * 6, 64)
for i, ch in enumerate(dc_chars):
    lineup.paste(ch, i * 54, 0)
lineup.save("output/dc_party.png", scale=3)

# ===== 每个角色的idle动画 =====
for role_name, ch in zip(roles.keys(), dc_chars):
    anim = Animation(ch, fps=6)
    anim.idle(amplitude=1, frames=4)
    anim.export_gif(f"output/dc_{role_name}_idle.gif", scale=4)

print(f"\n=== 多风格角色生成完毕 ===")
print(f"  5种风格: {', '.join(styles)}")
print(f"  5种职业(Dead Cells): {', '.join(roles.keys())}")
print(f"  总计: {len(chars) + len(dc_chars)} 个角色 + {len(dc_chars)} 个idle动画")
