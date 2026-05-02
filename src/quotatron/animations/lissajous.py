"""Lissajous curves — 5 curves with prime ratios trace pixels in visit order."""
from __future__ import annotations
import math
import numpy as np
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached

CW, CH = 250, 122
_RATIOS = [(2, 3), (3, 5), (5, 7), (7, 11), (11, 13)]


def _build_rank_map() -> list[list[float]]:
    rank: list[list[float | None]] = [[None] * CW for _ in range(CH)]
    rank_counter = 0
    cx, cy = CW / 2, CH / 2
    ax, ay = (CW / 2) - 1, (CH / 2) - 1
    # Sample many points per curve so we cover the canvas.
    samples_per_curve = 30000
    for a, b in _RATIOS:
        for i in range(samples_per_curve):
            theta = (i / samples_per_curve) * 2 * math.pi
            x = int(round(cx + ax * math.sin(a * theta)))
            y = int(round(cy + ay * math.sin(b * theta + math.pi / 4)))
            if 0 <= x < CW and 0 <= y < CH and rank[y][x] is None:
                rank[y][x] = rank_counter
                rank_counter += 1
    # Fill any unvisited pixels.
    for y in range(CH):
        for x in range(CW):
            if rank[y][x] is None:
                rank[y][x] = rank_counter
                rank_counter += 1
    total = float(CW * CH)
    return [[rank[y][x] / total for x in range(CW)] for y in range(CH)]


_RANK_MAP = disk_cached('lissajous_rank_map_v1', lambda: _build_rank_map())
_RANK_MAP_NP = np.array(_RANK_MAP, dtype=np.float32)


class Lissajous(BaseAnimation):
    name = "lissajous"
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
