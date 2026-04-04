"""中世纪角色套装 v2 - 使用升级后的着色引擎"""

from gclub_pixel import PixelCanvas, Sprite, Animation

# ===== 5个中世纪角色 (全部使用新的着色系统) =====

knight = Sprite.character(
    size=32,
    skin_color=(220, 185, 145),
    hair_color=(140, 100, 50),
    body_color=(165, 170, 185),   # 银色铠甲
    pants_color=(80, 75, 70),     # 深灰护腿
    eye_color=(35, 40, 75),
    boot_color=(65, 50, 35),
)

archer = Sprite.character(
    size=32,
    skin_color=(215, 180, 140),
    hair_color=(170, 120, 50),    # 金发
    body_color=(60, 110, 55),     # 森林绿
    pants_color=(90, 75, 50),     # 棕色
    eye_color=(40, 80, 40),
    boot_color=(80, 60, 35),
)

mage = Sprite.character(
    size=32,
    skin_color=(225, 195, 160),
    hair_color=(200, 200, 210),   # 银白发
    body_color=(95, 50, 120),     # 紫袍
    pants_color=(75, 40, 95),
    eye_color=(60, 120, 200),     # 蓝眼
    boot_color=(60, 40, 55),
)

rogue = Sprite.character(
    size=32,
    skin_color=(210, 175, 135),
    hair_color=(50, 45, 40),      # 深色短发
    body_color=(55, 55, 65),      # 暗灰皮甲
    pants_color=(45, 45, 55),
    eye_color=(50, 50, 50),
    boot_color=(40, 35, 30),
)

cleric = Sprite.character(
    size=32,
    skin_color=(225, 190, 150),
    hair_color=(120, 80, 40),
    body_color=(210, 205, 195),   # 白袍
    pants_color=(180, 175, 165),
    eye_color=(80, 60, 40),
    boot_color=(100, 80, 55),
)

# ===== 保存角色 =====
names = ["knight", "archer", "mage", "rogue", "cleric"]
chars = [knight, archer, mage, rogue, cleric]

for name, ch in zip(names, chars):
    ch.save(f"output/v2_{name}.png", scale=8)

# 横排合集
lineup = PixelCanvas(32 * 5 + 4 * 4, 32)
for i, ch in enumerate(chars):
    lineup.paste(ch, i * 36, 0)
lineup.save("output/v2_characters.png", scale=4)

# ===== 武器 (着色版) =====
sword = Sprite.weapon("sword", size=16, blade_color=(185, 195, 210), handle_color=(110, 75, 40), accent_color=(200, 175, 60))
axe = Sprite.weapon("axe", size=16, blade_color=(175, 180, 190), handle_color=(100, 70, 40))
staff = Sprite.weapon("staff", size=16, blade_color=(80, 140, 220), handle_color=(90, 65, 35))
shield = Sprite.weapon("shield", size=16, blade_color=(140, 50, 50), handle_color=(200, 175, 55))

weapons = [sword, axe, staff, shield]
w_sheet = PixelCanvas(16 * 4 + 3 * 4, 16)
for i, w in enumerate(weapons):
    w_sheet.paste(w, i * 20, 0)
w_sheet.save("output/v2_weapons.png", scale=5)

# ===== 物品 (着色版) =====
hp = Sprite.item("potion", color=(210, 45, 45), size=16)
mp = Sprite.item("potion", color=(50, 100, 210), size=16)
coin = Sprite.item("coin", color=(220, 185, 50), size=16)
gem = Sprite.item("gem", color=(50, 120, 220), size=16)
heart = Sprite.item("heart", color=(210, 50, 60), size=16)
key = Sprite.item("key", color=(210, 180, 50), size=16)

items = [hp, mp, coin, gem, heart, key]
i_sheet = PixelCanvas(16 * 6 + 5 * 4, 16)
for i, it in enumerate(items):
    i_sheet.paste(it, i * 20, 0)
i_sheet.save("output/v2_items.png", scale=5)

# ===== 动画 =====
for name, ch in zip(names, chars):
    anim = Animation(ch, fps=6)
    anim.idle(amplitude=1, frames=4)
    anim.export_gif(f"output/v2_{name}_idle.gif", scale=6)

print("=== 中世纪 v2 (着色版) 生成完毕 ===")
print(f"  角色: {', '.join(names)}")
print(f"  全部使用 3-5 色阶着色 + 彩色描边")
