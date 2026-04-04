"""Example 02: Character sprite generation.

Demonstrates: Sprite.character with different styles and colors.
"""
from gclub_pixel import Sprite, PixelCanvas

# Generate different characters
warrior = Sprite.character(size=32, body_color="red", hair_color="brown", style="chibi")
mage = Sprite.character(size=32, body_color="dark_purple", hair_color="white", style="chibi")
rogue = Sprite.character(size=32, body_color="dark_green", hair_color="yellow", style="tall")

# Compose them side by side
lineup = PixelCanvas(96 + 8, 32, palette="pico8")
lineup.paste(warrior, 0, 0)
lineup.paste(mage, 36, 0)
lineup.paste(rogue, 72, 0)
lineup.save("output/02_characters.png", scale=4)
print("Saved output/02_characters.png")

# Also save individually
warrior.save("output/02_warrior.png", scale=8)
mage.save("output/02_mage.png", scale=8)
