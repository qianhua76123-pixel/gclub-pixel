from gclub_pixel.palette import Palette, get_palette, resolve_color


def test_pico8_colors():
    p = Palette.PICO8
    assert p.get("red") == (255, 0, 77)
    assert p.get("black") == (0, 0, 0)
    assert p.get(0) == (0, 0, 0)


def test_closest_color():
    p = Palette.PICO8
    c = p.closest(250, 10, 70)
    assert c == (255, 0, 77)  # closest to red


def test_palette_names():
    p = Palette.PICO8
    assert "red" in p.names
    assert len(p) == 16


def test_get_palette():
    p = get_palette("pico8")
    assert len(p) == 16


def test_resolve_color_string():
    p = Palette.PICO8
    assert resolve_color("red", p) == (255, 0, 77, 255)


def test_resolve_color_tuple():
    assert resolve_color((100, 200, 50)) == (100, 200, 50, 255)
    assert resolve_color((100, 200, 50, 128)) == (100, 200, 50, 128)


def test_all_builtin_palettes():
    for name in ["pico8", "db16", "db32", "endesga32", "gameboy", "nes", "sweetie16"]:
        p = get_palette(name)
        assert len(p) > 0
