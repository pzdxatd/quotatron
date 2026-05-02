"""Ink-bleed from single seed with deterministic per-pixel jitter."""
from __future__ import annotations
import math
import random
import numpy as np
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached


_SEED_X, _SEED_Y = 80, 60


def _build_bleed_map(width: int, height: int) -> list[list[float]]:
    rng = random.Random(11)
    grid: list[list[float]] = []
    for y in range(height):
        row: list[float] = []
        for x in range(width):
            d = math.hypot(x - _SEED_X, y - _SEED_Y)
            jitter = rng.uniform(-15, 15)
            row.append(d + jitter)
        grid.append(row)
    return grid


_BLEED_MAP = disk_cached('ink_bleed_bleed_map_v1', lambda: _build_bleed_map(250, 122))
_MAX_BLEED = max(max(r) for r in _BLEED_MAP)
_BLEED_MAP_NP = np.array(_BLEED_MAP, dtype=np.float32)


class InkBleed(BaseAnimation):
    name = "ink_bleed"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        mask = Image.fromarray((_BLEED_MAP_NP <= t * _MAX_BLEED).astype(np.uint8) * 255, mode='L')
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
