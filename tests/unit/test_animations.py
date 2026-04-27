import pytest
from PIL import Image

from quotatron.animations._base import (
    AnimationContext,
    BaseAnimation,
    frame_count_for_duration,
)
from quotatron.models import Polarity


def test_frame_count_respects_target_fps_and_panel_minimum() -> None:
    # 10s at 5 fps = 50 frames, but panel min is 0.3s/frame → max ~33 frames.
    n = frame_count_for_duration(duration_s=10.0, target_fps=5)
    assert 20 <= n <= 33


def test_frame_count_rejects_non_positive_inputs() -> None:
    with pytest.raises(ValueError):
        frame_count_for_duration(0.0, 5)
    with pytest.raises(ValueError):
        frame_count_for_duration(-1.0, 5)
    with pytest.raises(ValueError):
        frame_count_for_duration(1.0, 0)


class _Identity(BaseAnimation):
    name = "identity"
    duration_default = 1.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        return ctx.to_image if t >= 0.5 else ctx.from_image


def _ctx(width: int = 250, height: int = 122) -> AnimationContext:
    return AnimationContext(
        from_image=Image.new("1", (width, height), 1),
        to_image=Image.new("1", (width, height), 0),
        polarity=Polarity.NORMAL,
        width=width,
        height=height,
    )


def test_base_animation_yields_frames_between_from_and_to() -> None:
    ctx = _ctx()
    anim = _Identity()
    frames = list(anim.frames(ctx, duration_s=1.0))
    assert len(frames) >= 5
    assert frames[0].getpixel((0, 0)) == 1
    assert frames[-1].getpixel((0, 0)) == 0


def test_frames_count_matches_frame_count_for_duration() -> None:
    """Generator must yield exactly frame_count_for_duration(d, fps) frames."""
    anim = _Identity()
    expected = frame_count_for_duration(1.0, _Identity.target_fps)
    assert len(list(anim.frames(_ctx(), duration_s=1.0))) == expected


def test_cannot_instantiate_baseanimation_directly() -> None:
    with pytest.raises(TypeError):
        BaseAnimation()  # type: ignore[abstract]


def test_subclass_without_name_override_raises_at_import() -> None:
    with pytest.raises(TypeError, match="must override BaseAnimation.name"):
        class _NoName(BaseAnimation):
            def render(self, t: float, ctx: AnimationContext) -> Image.Image:
                return ctx.from_image


def test_render_returning_wrong_mode_raises() -> None:
    class _BadMode(BaseAnimation):
        name = "bad_mode"

        def render(self, t: float, ctx: AnimationContext) -> Image.Image:
            return Image.new("RGB", (ctx.width, ctx.height), (255, 255, 255))

    with pytest.raises(ValueError, match="mode='RGB'"):
        list(_BadMode().frames(_ctx(), duration_s=1.0))


def test_render_returning_wrong_size_raises() -> None:
    class _BadSize(BaseAnimation):
        name = "bad_size"

        def render(self, t: float, ctx: AnimationContext) -> Image.Image:
            return Image.new("1", (100, 100), 1)

    with pytest.raises(ValueError, match="size="):
        list(_BadSize().frames(_ctx(), duration_s=1.0))


def test_animation_context_is_frozen() -> None:
    ctx = _ctx()
    with pytest.raises((TypeError, AttributeError)):
        ctx.width = 999  # type: ignore[misc]


def test_registry_excludes_underscore_prefixed_modules() -> None:
    """The auto-discovery contract: _base, _builtin_simple_fade, and the
    package __init__ must never appear in the public registry. This holds
    today (registry empty) and must continue to hold once Milestone 5
    adds 30 plugin files."""
    from quotatron.animations import registry
    reg = registry(refresh=True)
    assert "simple_fade" not in reg, "_builtin modules must not auto-register"
    for cls in reg.values():
        assert not cls.__module__.rsplit(".", 1)[-1].startswith("_"), (
            f"underscore module {cls.__module__} leaked into registry"
        )


def test_fallback_returns_simple_fade() -> None:
    from quotatron.animations import fallback
    from quotatron.animations._builtin_simple_fade import SimpleFade
    assert fallback() is SimpleFade


def test_discovery_skips_broken_plugins(tmp_path, monkeypatch) -> None:
    """A single broken plugin must not crash the animations subsystem."""
    import sys
    import importlib
    import quotatron.animations as anim_pkg

    # Create a fake animations directory with one broken module + one good one.
    fake_dir = tmp_path / "fake_animations"
    fake_dir.mkdir()
    (fake_dir / "__init__.py").write_text("")
    (fake_dir / "broken.py").write_text("raise RuntimeError('intentional test failure')\n")
    (fake_dir / "good.py").write_text(
        "from quotatron.animations._base import BaseAnimation, AnimationContext\n"
        "from PIL import Image\n"
        "class GoodAnim(BaseAnimation):\n"
        "    name = 'good'\n"
        "    def render(self, t, ctx):\n"
        "        return Image.new('1', (ctx.width, ctx.height), 1)\n"
    )

    monkeypatch.syspath_prepend(str(tmp_path))
    sys.modules.pop("fake_animations", None)
    sys.modules.pop("fake_animations.good", None)
    sys.modules.pop("fake_animations.broken", None)

    fake_pkg = importlib.import_module("fake_animations")
    monkeypatch.setattr(anim_pkg, "__file__", fake_pkg.__file__)
    monkeypatch.setattr(anim_pkg, "__name__", "fake_animations")
    monkeypatch.setattr(anim_pkg, "_REGISTRY", {})
    anim_pkg._discover()
    # Broken module skipped, good module registered.
    assert "good" in anim_pkg._REGISTRY
    assert "broken" not in anim_pkg._REGISTRY
