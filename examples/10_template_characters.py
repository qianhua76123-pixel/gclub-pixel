"""模板角色 - 逐像素手绘模板 + 实时换色"""

from gclub_pixel import render_template, PixelCanvas, Animation
from gclub_pixel.templates import CHIBI_32

# ===== 同一模板，不同配色 = 不同角色 =====

knight = render_template(CHIBI_32,
    skin=(220, 185, 145), hair=(130, 90, 45),
    armor=(165, 170, 185), pants=(75, 70, 65),
    eye=(45, 55, 100), boot=(65, 50, 35),
    accent=(180, 50, 50))

mage = render_template(CHIBI_32,
    skin=(225, 195, 160), hair=(210, 210, 220),
    armor=(95, 55, 130), pants=(75, 45, 100),
    eye=(70, 130, 210), boot=(55, 40, 55),
    accent=(80, 160, 220))

archer = render_template(CHIBI_32,
    skin=(215, 180, 140), hair=(175, 130, 55),
    armor=(60, 110, 55), pants=(85, 75, 50),
    eye=(50, 90, 50), boot=(80, 60, 35),
    accent=(180, 140, 50))

rogue = render_template(CHIBI_32,
    skin=(210, 175, 135), hair=(45, 40, 38),
    armor=(55, 55, 65), pants=(45, 42, 50),
    eye=(55, 55, 55), boot=(40, 35, 28),
    accent=(200, 60, 60))

cleric = render_template(CHIBI_32,
    skin=(225, 190, 150), hair=(120, 80, 40),
    armor=(215, 210, 200), pants=(180, 175, 165),
    eye=(80, 60, 40), boot=(100, 80, 55),
    accent=(200, 175, 55))

# 保存单个角色 (8x放大)
chars = {"knight": knight, "mage": mage, "archer": archer, "rogue": rogue, "cleric": cleric}
for name, ch in chars.items():
    ch.save(f"output/tpl_{name}.png", scale=8)

# 横排合集
lineup = PixelCanvas(32 * 5 + 4 * 4, 32)
for i, ch in enumerate(chars.values()):
    lineup.paste(ch, i * 36, 0)
lineup.save("output/tpl_party.png", scale=4)

# idle动画
for name, ch in chars.items():
    anim = Animation(ch, fps=6)
    anim.idle(amplitude=1, frames=4)
    anim.export_gif(f"output/tpl_{name}_idle.gif", scale=6)

print("=== 模板角色生成完毕 ===")
for name in chars:
    print(f"  {name}: output/tpl_{name}.png")
