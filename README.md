# gclub-pixel

LLM-friendly pixel art generation toolkit. Write Python code, get game-ready sprites and animations.

## Install

```bash
pip install gclub-pixel
```

## Quick Start

```python
from gclub_pixel import PixelCanvas, Palette

# Create a 32x32 canvas with PICO-8 palette
c = PixelCanvas(32, 32, palette="pico8")

# Draw a simple character
c.fill_rect(12, 4, 8, 8, "peach")       # head
c.fill_rect(10, 12, 12, 10, "blue")     # body
c.fill_rect(10, 22, 5, 8, "indigo")     # left leg
c.fill_rect(17, 22, 5, 8, "indigo")     # right leg
c.fill_rect(8, 13, 2, 7, "peach")       # left arm
c.fill_rect(22, 13, 2, 7, "peach")      # right arm

# Add pixel eyes
c.set_pixel(14, 7, "dark_blue")
c.set_pixel(18, 7, "dark_blue")

# Auto outline
c.outline("black")

# Save
c.save("character.png", scale=4)
```

## Designed for LLMs

This library is specifically designed so that AI models (Claude, GPT, etc.) can write code that generates pixel art. Every API is:

- **Intuitive**: method names describe what they do
- **Chainable**: `canvas.fill_rect(...).outline(...).save(...)`
- **Deterministic**: same code = same output, every time
- **Well-documented**: rich docstrings with examples

## License

MIT
