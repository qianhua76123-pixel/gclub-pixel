"""Example 03: Sprite animation.

Demonstrates: Animation idle, bounce, flash. Export as GIF and spritesheet.
"""
from gclub_pixel import Sprite, Animation

# Create a character
hero = Sprite.character(size=32, body_color="blue", hair_color="red")

# Idle animation (breathing bob)
idle = Animation(hero, fps=6)
idle.idle(amplitude=1, frames=4)
idle.export_gif("output/03_idle.gif", scale=4)
idle.export_spritesheet("output/03_idle_sheet.png", scale=4)
print("Saved output/03_idle.gif and 03_idle_sheet.png")

# Bounce animation
bounce = Animation(hero, fps=8)
bounce.bounce(height=3, frames=6)
bounce.export_gif("output/03_bounce.gif", scale=4)
print("Saved output/03_bounce.gif")

# Damage flash
flash = Animation(hero, fps=10)
flash.flash("white", frames=6)
flash.export_gif("output/03_flash.gif", scale=4)
print("Saved output/03_flash.gif")
