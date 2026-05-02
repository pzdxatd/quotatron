"""Smooth value-noise threshold reveal (low-res grid bilinearly upsampled)."""
from __future__ import annotations
import random
import numpy as np
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached

CW, CH = 250, 122
_GW, _GH = 32, 16  # low-res grid resolution


def _build_smooth_noise() -> list[list[float]]:
    rng = random.Random(127)
    grid = [[rng.random() for _ in range(_GW)] for _ in range(_GH)]
    # Bilinearly upsample to (CH, CW).
    out: list[list[float]] = []
    for y in range(CH):
        gy = y * (_GH - 1) / (CH - 1)
        gy0 = int(gy)
        gy1 = min(gy0 + 1, _GH - 1)
        fy = gy - gy0
        row: list[float] = []
        for x in range(CW):
            gx = x * (_GW - 1) / (CW - 1)
            gx0 = int(gx)
            gx1 = min(gx0 + 1, _GW - 1)
            fx = gx - gx0
            v = (
                grid[gy0][gx0] * (1 - fx) * (1 - fy)
                + grid[gy0][gx1] * fx * (1 - fy)
                + grid[gy1][gx0] * (1 - fx) * fy
                + grid[gy1][gx1] * fx * fy
            )
            row.append(v)
        out.append(row)
    return out


_SMOOTH_NOISE = disk_cached('perlin_fade_smooth_noise_v1', lambda: _build_smooth_noise())
_SMOOTH_NOISE_NP = np.array(_SMOOTH_NOISE, dtype=np.float32)


class PerlinFade(BaseAnimation):
    name = "perlin_fade"
    duration_default = 10.0
    target_fps = 4
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        mask = Image.fromarray((_SMOOTH_NOISE_NP < t).astype(np.uint8) * 255, mode='L')
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
