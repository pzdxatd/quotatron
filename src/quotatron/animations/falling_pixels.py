"""Falling pixel rain — scattered pixel-by-pixel reveal with per-row offset."""
from __future__ import annotations
import random
import numpy as np
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached

CW, CH = 250, 122


def _build_rank_map() -> list[list[float]]:
    rng = random.Random(193)
    coords = [(x, y) for y in range(CH) for x in range(CW)]
    # Sort by y first (top falls first), then add jitter per coord for variety.
    coords.sort(key=lambda c: (c[1], rng.random()))
    total = float(len(coords))
    rank = [[0.0] * CW for _ in range(CH)]
    for i, (x, y) in enumerate(coords):
        rank[y][x] = i / total
    return rank


_RANK_MAP = disk_cached('falling_pixels_rank_map_v1', lambda: _build_rank_map())
_RANK_MAP_NP = np.array(_RANK_MAP, dtype=np.float32)


class FallingPixels(BaseAnimation):
    name = "falling_pixels"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        mask = Image.fromarray((_RANK_MAP_NP <= t).astype(np.uint8) * 255, mode='L')
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
