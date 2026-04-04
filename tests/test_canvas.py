import tempfile
from pathlib import Path

from gclub_pixel.canvas import PixelCanvas, TRANSPARENT


def test_create_canvas():
    c = PixelCanvas(16, 16)
    assert c.width == 16
    assert c.height == 16


def test_set_get_pixel():
    c = PixelCanvas(8, 8)
    c.set_pixel(3, 3, (255, 0, 0))
    assert c.get_pixel(3, 3) == (255, 0, 0, 255)


def test_fill_rect():
    c = PixelCanvas(8, 8, palette="pico8")
    c.fill_rect(2, 2, 4, 4, "red")
    assert c.get_pixel(3, 3) == (255, 0, 77, 255)
    assert c.get_pixel(0, 0) == TRANSPARENT


def test_draw_circle():
    c = PixelCanvas(16, 16)
    c.draw_circle(8, 8, 5, (255, 255, 255))
    # Circle should have set some pixels
    non_transparent = sum(
        1 for y in range(16) for x in range(16) if c.get_pixel(x, y)[3] > 0
    )
    assert non_transparent > 10


def test_fill_circle():
    c = PixelCanvas(16, 16)
    c.fill_circle(8, 8, 4, (255, 0, 0))
    assert c.get_pixel(8, 8) == (255, 0, 0, 255)


def test_outline():
    c = PixelCanvas(16, 16)
    c.fill_rect(5, 5, 6, 6, (255, 0, 0))
    c.outline((0, 0, 0))
    # Pixel adjacent to red should now be black outline
    assert c.get_pixel(4, 5)[3] > 0


def test_mirror_x():
    c = PixelCanvas(8, 8)
    c.set_pixel(1, 1, (255, 0, 0))
    c.mirror_x()
    assert c.get_pixel(6, 1) == (255, 0, 0, 255)


def test_copy():
    c = PixelCanvas(8, 8)
    c.set_pixel(0, 0, (255, 0, 0))
    c2 = c.copy()
    c2.set_pixel(0, 0, (0, 255, 0))
    assert c.get_pixel(0, 0) == (255, 0, 0, 255)  # original unchanged


def test_paste():
    bg = PixelCanvas(16, 16)
    fg = PixelCanvas(4, 4)
    fg.fill(((0, 255, 0)))
    bg.paste(fg, 6, 6)
    assert bg.get_pixel(7, 7) == (0, 255, 0, 255)


def test_save():
    c = PixelCanvas(8, 8, palette="pico8")
    c.fill_rect(0, 0, 8, 8, "blue")
    with tempfile.TemporaryDirectory() as d:
        p = str(Path(d) / "test.png")
        c.save(p)
        assert Path(p).exists()
        assert Path(p).stat().st_size > 0


def test_save_scaled():
    c = PixelCanvas(8, 8)
    c.fill(((255, 0, 0)))
    with tempfile.TemporaryDirectory() as d:
        p = str(Path(d) / "test_4x.png")
        c.save(p, scale=4)
        from PIL import Image
        img = Image.open(p)
        assert img.size == (32, 32)


def test_chaining():
    c = PixelCanvas(16, 16, palette="pico8")
    result = c.fill_rect(2, 2, 4, 4, "red").outline("black")
    assert result is c  # chaining returns self
