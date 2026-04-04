"""Example 01: Basic shapes and canvas operations.

Demonstrates: PixelCanvas, fill_rect, draw_circle, draw_line, outline, save.
"""
from gclub_pixel import PixelCanvas

# Create a 32x32 canvas with PICO-8 palette
c = PixelCanvas(32, 32, palette="pico8")

# Draw shapes
c.fill_rect(4, 4, 10, 10, "red")         # red square
c.fill_circle(24, 10, 5, "blue")         # blue circle
c.draw_line(2, 20, 30, 28, "yellow")     # yellow line
c.draw_rect(2, 2, 28, 28, "dark_gray")   # border

# Save with 8x upscale for visibility
c.save("output/01_shapes.png", scale=8)
print("Saved output/01_shapes.png")
