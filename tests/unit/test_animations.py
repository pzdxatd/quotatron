from PIL import Image
from quotatron.animations._base import (
    AnimationContext, BaseAnimation, frame_count_for_duration,
)
from quotatron.models import Polarity


def test_frame_count_respects_target_fps_and_panel_minimum() -> None:
    # 10s at 5 fps = 50 frames, but panel min is 0.3s/frame → max ~33 frames.
    n = frame_count_for_duration(duration_s=10.0, target_fps=5)
    assert 20 <= n <= 33


class _Identity(BaseAnimation):
    name = "identity"
    duration_default = 1.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        return ctx.to_image if t >= 0.5 else ctx.from_image


def test_base_animation_yields_frames_between_from_and_to() -> None:
    from_img = Image.new("1", (250, 122), 1)
    to_img = Image.new("1", (250, 122), 0)
    ctx = AnimationContext(
        from_image=from_img, to_image=to_img,
        polarity=Polarity.NORMAL, width=250, height=122,
    )
    anim = _Identity()
    frames = list(anim.frames(ctx, duration_s=1.0))
    assert len(frames) >= 5
    assert frames[0].getpixel((0, 0)) == 1
    assert frames[-1].getpixel((0, 0)) == 0
