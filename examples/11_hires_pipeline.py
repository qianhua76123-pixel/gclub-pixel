"""高分辨率管线 - 画平滑曲线，缩小成像素画"""

from gclub_pixel import quick_character, PixelCanvas, Animation

# ===== 5个中世纪角色 (高分辨率管线) =====

knight = quick_character(32,
    skin=(220, 185, 145), hair=(130, 90, 45), hair_style="short",
    armor=(165, 170, 185), pants=(80, 75, 70),
    eye=(45, 55, 100), boot=(65, 50, 35), accent=(180, 50, 50))

mage = quick_character(32,
    skin=(225, 195, 160), hair=(210, 210, 220), hair_style="long",
    armor=(95, 55, 130), pants=(75, 45, 100),
    eye=(70, 130, 210), boot=(55, 40, 55), accent=(80, 160, 220))

archer = quick_character(32,
    skin=(215, 180, 140), hair=(175, 130, 55), hair_style="ponytail",
    armor=(60, 110, 55), pants=(85, 75, 50),
    eye=(50, 90, 50), boot=(80, 60, 35), accent=(180, 140, 50))

rogue = quick_character(32,
    skin=(210, 175, 135), hair=(45, 40, 38), hair_style="spiky",
    armor=(55, 55, 65), pants=(45, 42, 50),
    eye=(55, 55, 55), boot=(40, 35, 28), accent=(200, 60, 60))

cleric = quick_character(32,
    skin=(225, 190, 150), hair=(120, 80, 40), hair_style="messy",
    armor=(215, 210, 200), pants=(180, 175, 165),
    eye=(80, 60, 40), boot=(100, 80, 55), accent=(200, 175, 55))

# 保存
chars = {"knight": knight, "mage": mage, "archer": archer, "rogue": rogue, "cleric": cleric}
for name, ch in chars.items():
    ch.save(f"output/hr_{name}.png", scale=8)

# 横排
lineup = PixelCanvas(32 * 5 + 4 * 4, 32)
for i, ch in enumerate(chars.values()):
    lineup.paste(ch, i * 36, 0)
lineup.save("output/hr_party.png", scale=4)

# 同样出48和64像素版本
knight_48 = quick_character(48, skin=(220,185,145), hair=(130,90,45), armor=(165,170,185), accent=(180,50,50))
knight_64 = quick_character(64, skin=(220,185,145), hair=(130,90,45), armor=(165,170,185), accent=(180,50,50))
knight_48.save("output/hr_knight_48.png", scale=5)
knight_64.save("output/hr_knight_64.png", scale=4)

# 动画
for name, ch in chars.items():
    anim = Animation(ch, fps=6)
    anim.idle(amplitude=1, frames=4)
    anim.export_gif(f"output/hr_{name}_idle.gif", scale=6)

print("=== 高分辨率管线角色生成完毕 ===")
for name in chars:
    print(f"  {name}: output/hr_{name}.png (32px) ")
print(f"  knight: 48px和64px版本也已生成")
