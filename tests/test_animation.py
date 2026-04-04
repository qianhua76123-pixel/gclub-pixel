import tempfile
from pathlib import Path

from gclub_pixel.sprite import Sprite
from gclub_pixel.animation import Animation


def test_idle_animation():
    hero = Sprite.character(size=16)
    anim = Animation(hero, fps=8)
    anim.idle(amplitude=1, frames=4)
    assert len(anim.frames) == 4


def test_bounce_animation():
    hero = Sprite.character(size=16)
    anim = Animation(hero, fps=8)
    anim.bounce(height=2, frames=6)
    assert len(anim.frames) == 6


def test_flash_animation():
    hero = Sprite.character(size=16)
    anim = Animation(hero, fps=8)
    anim.flash("white", frames=4)
    assert len(anim.frames) == 4


def test_export_spritesheet():
    hero = Sprite.character(size=16)
    anim = Animation(hero, fps=8)
    anim.idle(frames=4)
    with tempfile.TemporaryDirectory() as d:
        anim.export_spritesheet(str(Path(d) / "test.png"))
        assert (Path(d) / "test.png").exists()
        from PIL import Image
        img = Image.open(str(Path(d) / "test.png"))
        assert img.size == (16 * 4, 16)  # 4 frames in a row


def test_export_gif():
    hero = Sprite.character(size=16)
    anim = Animation(hero, fps=8)
    anim.idle(frames=4)
    with tempfile.TemporaryDirectory() as d:
        anim.export_gif(str(Path(d) / "test.gif"))
        assert (Path(d) / "test.gif").exists()


def test_export_frames():
    hero = Sprite.character(size=16)
    anim = Animation(hero, fps=8)
    anim.idle(frames=4)
    with tempfile.TemporaryDirectory() as d:
        anim.export_frames(d, prefix="frame")
        assert (Path(d) / "frame_000.png").exists()
        assert (Path(d) / "frame_003.png").exists()
