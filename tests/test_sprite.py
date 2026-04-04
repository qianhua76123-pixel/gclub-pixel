from gclub_pixel.sprite import Sprite
from gclub_pixel.canvas import PixelCanvas


def test_character_chibi():
    c = Sprite.character(size=32, style="chibi")
    assert isinstance(c, PixelCanvas)
    assert c.width == 32
    # Should have non-transparent pixels
    has_content = any(c.get_pixel(x, y)[3] > 0 for y in range(32) for x in range(32))
    assert has_content


def test_character_tall():
    c = Sprite.character(size=32, style="tall")
    assert c.width == 32


def test_weapon_sword():
    c = Sprite.weapon("sword", size=16)
    assert isinstance(c, PixelCanvas)
    assert c.width == 16


def test_weapon_types():
    for wtype in ["sword", "axe", "staff", "shield"]:
        c = Sprite.weapon(wtype, size=16)
        has_content = any(c.get_pixel(x, y)[3] > 0 for y in range(16) for x in range(16))
        assert has_content, f"{wtype} has no content"


def test_item_potion():
    c = Sprite.item("potion", color="red")
    assert c.width == 16


def test_item_types():
    for itype in ["potion", "coin", "gem", "heart", "key"]:
        c = Sprite.item(itype, size=16)
        has_content = any(c.get_pixel(x, y)[3] > 0 for y in range(16) for x in range(16))
        assert has_content, f"{itype} has no content"
