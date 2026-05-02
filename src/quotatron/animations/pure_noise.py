"""Pure-noise per-pixel threshold reveal."""
from __future__ import annotations
import random
import numpy as np
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached

CW, CH = 250, 122


def _build_noise_field() -> list[list[float]]:
    rng = random.Random(101)
    return [[rng.random() for _ in range(CW)] for _ in range(CH)]


_NOISE = disk_cached('pure_noise_noise_v1', lambda: _build_noise_field())
_NOISE_NP = np.array(_NOISE, dtype=np.float32)


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
        mask = Image.fromarray((_NOISE_NP < t).astype(np.uint8) * 255, mode='L')
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
