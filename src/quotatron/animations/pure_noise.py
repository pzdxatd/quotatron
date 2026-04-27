"""Pure-noise per-pixel threshold reveal."""
from __future__ import annotations
import random
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation

CW, CH = 250, 122


def _build_noise_field() -> list[list[float]]:
    rng = random.Random(101)
    return [[rng.random() for _ in range(CW)] for _ in range(CH)]


_NOISE = _build_noise_field()


class PureNoise(BaseAnimation):
    name = "pure_noise"
    duration_default = 10.0
    target_fps = 4
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        mask = Image.new("1", (w, h), 0)
        mp = mask.load()
        for y in range(h):
            row = _NOISE[y]
            for x in range(w):
                if t > row[x]:
                    mp[x, y] = 1
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
