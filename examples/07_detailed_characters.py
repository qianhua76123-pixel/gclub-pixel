"""中世纪角色 v3 - 64x64高细节分层渲染"""

from gclub_pixel import CharacterBody, PixelCanvas, Animation

# ===== 64x64 高细节角色 =====

# 骑士 - 银色板甲
knight = CharacterBody(64)
knight.set_skin((220, 185, 145))
knight.set_hair("short", (130, 90, 45))
knight.set_armor("plate", (170, 175, 190))
knight.set_eyes((40, 55, 90))
knight_sprite = knight.render()
knight_sprite.save("output/v3_knight_64.png", scale=4)

# 弓箭手 - 绿色皮甲
archer = CharacterBody(64)
archer.set_skin((215, 180, 140))
archer.set_hair("ponytail", (175, 130, 55))
archer.set_armor("leather", (65, 115, 55))
archer.set_eyes((50, 90, 50))
archer_sprite = archer.render()
archer_sprite.save("output/v3_archer_64.png", scale=4)

# 法师 - 紫色长袍
mage = CharacterBody(64)
mage.set_skin((225, 195, 160))
mage.set_hair("long", (210, 210, 220))
mage.set_armor("robe", (100, 55, 130))
mage.set_eyes((70, 130, 210))
mage_sprite = mage.render()
mage_sprite.save("output/v3_mage_64.png", scale=4)

# 盗贼 - 深灰皮甲
rogue = CharacterBody(64)
rogue.set_skin((210, 175, 135))
rogue.set_hair("spiky", (45, 40, 38))
rogue.set_armor("leather", (60, 58, 68))
rogue.set_eyes((55, 55, 55))
rogue_sprite = rogue.render()
rogue_sprite.save("output/v3_rogue_64.png", scale=4)

# 牧师 - 白袍
cleric = CharacterBody(64)
cleric.set_skin((225, 195, 155))
cleric.set_hair("messy", (125, 80, 40))
cleric.set_armor("robe", (215, 210, 200))
cleric.set_eyes((85, 65, 45))
cleric_sprite = cleric.render()
cleric_sprite.save("output/v3_cleric_64.png", scale=4)

# ===== 横排合集 =====
sprites = [knight_sprite, archer_sprite, mage_sprite, rogue_sprite, cleric_sprite]
names = ["knight", "archer", "mage", "rogue", "cleric"]
lineup = PixelCanvas(64 * 5 + 4 * 8, 64)
for i, sp in enumerate(sprites):
    lineup.paste(sp, i * 72, 0)
lineup.save("output/v3_characters_64.png", scale=3)

# ===== Idle动画 =====
for name, sp in zip(names, sprites):
    anim = Animation(sp, fps=6)
    anim.idle(amplitude=1, frames=4)
    anim.export_gif(f"output/v3_{name}_idle.gif", scale=4)

print("=== v3 高细节角色 (64x64) 生成完毕 ===")
print(f"  角色: {', '.join(names)}")
print(f"  特性: 球形头部光影 / 圆柱体躯干 / 分层渲染 / 彩色描边")
print(f"  细节: 眼睛(巩膜+虹膜+瞳孔+高光) / 眉毛 / 鼻影 / 嘴唇")
print(f"  铠甲: 铆钉 / 接缝 / 肩甲高光 / 腰带扣")
print(f"  发型: short / ponytail / long / spiky / messy")
