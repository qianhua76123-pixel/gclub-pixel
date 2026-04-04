"""中世纪像素角色套装 - 骑士、弓箭手、法师、盗贼、牧师 + 武器装备 + 物品"""

from gclub_pixel import PixelCanvas, Sprite, Animation, Palette

# ===== 角色 =====

# 骑士 - 银甲红披风
knight = PixelCanvas(32, 32, palette="pico8")
u = 2
mid = 16
# 头盔
knight.fill_rect(mid-4*u, 0, 8*u, 2*u, "light_gray")
knight.fill_rect(mid-5*u, 1*u, 10*u, 2*u, "light_gray")
# 面甲开口
knight.fill_rect(mid-3*u, 3*u, 6*u, 4*u, "peach")
# 眼睛
knight.set_pixel(mid-2*u, 4*u, "dark_blue")
knight.set_pixel(mid+1*u, 4*u, "dark_blue")
# 铠甲身体
knight.fill_rect(mid-5*u, 7*u, 10*u, 6*u, "light_gray")
# 腰带
knight.fill_rect(mid-5*u, 10*u, 10*u, 1*u, "brown")
knight.fill_rect(mid-1*u, 10*u, 2*u, 1*u, "yellow")  # 腰带扣
# 披风(两侧)
knight.fill_rect(mid-6*u, 7*u, 1*u, 7*u, "red")
knight.fill_rect(mid+5*u, 7*u, 1*u, 7*u, "red")
# 手臂
knight.fill_rect(mid-6*u, 8*u, 1*u, 4*u, "light_gray")
knight.fill_rect(mid+5*u, 8*u, 1*u, 4*u, "light_gray")
# 手
knight.fill_rect(mid-6*u, 12*u, 1*u, 1*u, "peach")
knight.fill_rect(mid+5*u, 12*u, 1*u, 1*u, "peach")
# 腿
knight.fill_rect(mid-4*u, 13*u, 3*u, 3*u, "dark_gray")
knight.fill_rect(mid+1*u, 13*u, 3*u, 3*u, "dark_gray")
knight.outline("black")

# 弓箭手 - 绿衣棕帽
archer = PixelCanvas(32, 32, palette="pico8")
# 帽子
archer.fill_rect(mid-4*u, 0, 8*u, 2*u, "dark_green")
archer.fill_rect(mid-3*u, 0, 2*u, 1*u, "red")  # 羽毛
# 头发
archer.fill_rect(mid-4*u, 2*u, 8*u, 2*u, "brown")
# 脸
archer.fill_rect(mid-3*u, 3*u, 6*u, 4*u, "peach")
archer.set_pixel(mid-2*u, 5*u, "dark_green")
archer.set_pixel(mid+1*u, 5*u, "dark_green")
# 身体
archer.fill_rect(mid-4*u, 7*u, 8*u, 6*u, "dark_green")
# 腰带+箭袋
archer.fill_rect(mid-4*u, 10*u, 8*u, 1*u, "brown")
archer.fill_rect(mid+3*u, 7*u, 2*u, 5*u, "brown")  # 箭袋
# 手臂
archer.fill_rect(mid-5*u, 8*u, 1*u, 4*u, "peach")
archer.fill_rect(mid+4*u, 8*u, 1*u, 4*u, "peach")
# 腿
archer.fill_rect(mid-3*u, 13*u, 2*u, 3*u, "brown")
archer.fill_rect(mid+1*u, 13*u, 2*u, 3*u, "brown")
archer.outline("black")

# 法师 - 紫袍蓝帽
mage = PixelCanvas(32, 32, palette="pico8")
# 尖帽子
mage.fill_rect(mid-1*u, 0, 2*u, 1*u, "dark_purple")
mage.fill_rect(mid-2*u, 1*u, 4*u, 1*u, "dark_purple")
mage.fill_rect(mid-3*u, 2*u, 6*u, 1*u, "dark_purple")
mage.fill_rect(mid-4*u, 3*u, 8*u, 1*u, "dark_purple")
# 星星装饰
mage.set_pixel(mid, 2*u, "yellow")
# 脸
mage.fill_rect(mid-3*u, 4*u, 6*u, 4*u, "peach")
# 眼睛
mage.set_pixel(mid-2*u, 5*u, "blue")
mage.set_pixel(mid+1*u, 5*u, "blue")
# 胡子
mage.fill_rect(mid-2*u, 7*u, 4*u, 1*u, "white")
# 长袍
mage.fill_rect(mid-5*u, 8*u, 10*u, 6*u, "dark_purple")
# 腰带
mage.fill_rect(mid-5*u, 10*u, 10*u, 1*u, "yellow")
# 袖子
mage.fill_rect(mid-6*u, 8*u, 1*u, 4*u, "dark_purple")
mage.fill_rect(mid+5*u, 8*u, 1*u, 4*u, "dark_purple")
# 手
mage.fill_rect(mid-6*u, 12*u, 1*u, 1*u, "peach")
mage.fill_rect(mid+5*u, 12*u, 1*u, 1*u, "peach")
# 长袍下摆
mage.fill_rect(mid-5*u, 14*u, 10*u, 2*u, "dark_purple")
mage.outline("black")

# 盗贼 - 黑衣红围巾
rogue = PixelCanvas(32, 32, palette="pico8")
# 兜帽
rogue.fill_rect(mid-4*u, 0, 8*u, 3*u, "dark_gray")
rogue.fill_rect(mid-5*u, 2*u, 10*u, 2*u, "dark_gray")
# 脸(半遮)
rogue.fill_rect(mid-3*u, 3*u, 6*u, 4*u, "peach")
# 面罩
rogue.fill_rect(mid-3*u, 6*u, 6*u, 1*u, "red")
# 眼睛
rogue.set_pixel(mid-2*u, 4*u, "dark_gray")
rogue.set_pixel(mid+1*u, 4*u, "dark_gray")
# 身体
rogue.fill_rect(mid-4*u, 7*u, 8*u, 6*u, "dark_gray")
# 腰带+匕首
rogue.fill_rect(mid-4*u, 10*u, 8*u, 1*u, "brown")
rogue.fill_rect(mid+2*u, 10*u, 1*u, 3*u, "light_gray")  # 匕首
# 围巾尾巴
rogue.fill_rect(mid+4*u, 5*u, 1*u, 4*u, "red")
# 手臂
rogue.fill_rect(mid-5*u, 8*u, 1*u, 4*u, "dark_gray")
rogue.fill_rect(mid+4*u, 8*u, 1*u, 4*u, "dark_gray")
# 腿
rogue.fill_rect(mid-3*u, 13*u, 2*u, 3*u, "dark_gray")
rogue.fill_rect(mid+1*u, 13*u, 2*u, 3*u, "dark_gray")
rogue.outline("black")

# 牧师 - 白袍金十字
cleric = PixelCanvas(32, 32, palette="pico8")
# 头巾
cleric.fill_rect(mid-4*u, 0, 8*u, 3*u, "white")
# 脸
cleric.fill_rect(mid-3*u, 3*u, 6*u, 4*u, "peach")
cleric.set_pixel(mid-2*u, 4*u, "brown")
cleric.set_pixel(mid+1*u, 4*u, "brown")
# 白袍
cleric.fill_rect(mid-5*u, 7*u, 10*u, 6*u, "white")
# 金色十字架
cleric.fill_rect(mid-1*u, 8*u, 2*u, 4*u, "yellow")
cleric.fill_rect(mid-2*u, 9*u, 4*u, 1*u, "yellow")
# 腰带
cleric.fill_rect(mid-5*u, 11*u, 10*u, 1*u, "orange")
# 袖子
cleric.fill_rect(mid-6*u, 8*u, 1*u, 4*u, "white")
cleric.fill_rect(mid+5*u, 8*u, 1*u, 4*u, "white")
cleric.fill_rect(mid-6*u, 12*u, 1*u, 1*u, "peach")
cleric.fill_rect(mid+5*u, 12*u, 1*u, 1*u, "peach")
# 长袍下摆
cleric.fill_rect(mid-5*u, 13*u, 10*u, 3*u, "white")
cleric.outline("black")

# ===== 武器 =====
long_sword = Sprite.weapon("sword", size=16, blade_color="light_gray", handle_color="brown")
battle_axe = Sprite.weapon("axe", size=16, blade_color="light_gray", handle_color="brown")
magic_staff = Sprite.weapon("staff", size=16, blade_color="blue", handle_color="brown")
iron_shield = Sprite.weapon("shield", size=16, blade_color="dark_gray", handle_color="yellow")

# ===== 物品 =====
hp_potion = Sprite.item("potion", color="red", size=16)
mp_potion = Sprite.item("potion", color="blue", size=16)
gold_coin = Sprite.item("coin", color="yellow", size=16)
ruby_gem = Sprite.item("gem", color="red", size=16)
life_heart = Sprite.item("heart", color="red", size=16)
dungeon_key = Sprite.item("key", color="yellow", size=16)

# ===== 组合输出 =====

# 角色合集 (5个角色横排)
chars = [knight, archer, mage, rogue, cleric]
char_sheet = PixelCanvas(32 * 5 + 4 * 8, 32)
for i, ch in enumerate(chars):
    char_sheet.paste(ch, i * (32 + 8), 0)
char_sheet.save("output/medieval_characters.png", scale=3)

# 单独保存每个角色 (大图预览)
names = ["knight", "archer", "mage", "rogue", "cleric"]
for name, ch in zip(names, chars):
    ch.save(f"output/medieval_{name}.png", scale=8)

# 武器合集
weapons = [long_sword, battle_axe, magic_staff, iron_shield]
weapon_sheet = PixelCanvas(16 * 4 + 3 * 4, 16)
for i, w in enumerate(weapons):
    weapon_sheet.paste(w, i * 20, 0)
weapon_sheet.save("output/medieval_weapons.png", scale=4)

# 物品合集
items = [hp_potion, mp_potion, gold_coin, ruby_gem, life_heart, dungeon_key]
item_sheet = PixelCanvas(16 * 6 + 5 * 4, 16)
for i, it in enumerate(items):
    item_sheet.paste(it, i * 20, 0)
item_sheet.save("output/medieval_items.png", scale=4)

# ===== 动画 =====

# 每个角色生成 idle 动画 GIF
for name, ch in zip(names, chars):
    anim = Animation(ch, fps=6)
    anim.idle(amplitude=1, frames=4)
    anim.export_gif(f"output/medieval_{name}_idle.gif", scale=6)
    anim.export_spritesheet(f"output/medieval_{name}_idle_sheet.png", scale=3)

print("=== 中世纪像素角色套装生成完毕 ===")
print(f"  角色: {', '.join(names)}")
print(f"  武器: 长剑, 战斧, 法杖, 盾牌")
print(f"  物品: 生命药水, 魔法药水, 金币, 红宝石, 爱心, 钥匙")
print(f"  动画: 5个角色的idle动画 (GIF + SpriteSheet)")
print(f"  输出目录: output/")
