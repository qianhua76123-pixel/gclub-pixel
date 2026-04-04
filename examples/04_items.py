"""Example 04: Game item sprites.

Demonstrates: Sprite.item and Sprite.weapon for icons.
"""
from gclub_pixel import Sprite, PixelCanvas

# Generate items
potion = Sprite.item("potion", color="red", size=16)
coin = Sprite.item("coin", color="yellow", size=16)
gem = Sprite.item("gem", color="blue", size=16)
heart = Sprite.item("heart", color="red", size=16)
key = Sprite.item("key", color="yellow", size=16)

# Generate weapons
sword = Sprite.weapon("sword", size=16)
axe = Sprite.weapon("axe", size=16)
staff = Sprite.weapon("staff", blade_color="blue", size=16)

# Compose into an icon sheet
sheet = PixelCanvas(16 * 8 + 7 * 2, 16)
items = [potion, coin, gem, heart, key, sword, axe, staff]
for i, item in enumerate(items):
    sheet.paste(item, i * 18, 0)

sheet.save("output/04_items.png", scale=4)
print("Saved output/04_items.png")
