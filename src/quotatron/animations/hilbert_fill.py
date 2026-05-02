"""Hilbert space-filling curve traversal — pixels reveal in curve order."""
from __future__ import annotations
import numpy as np
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached

CW, CH = 250, 122
_ORDER = 8   # 2^8 = 256, covers 250x122 canvas


def _d2xy(n: int, d: int) -> tuple[int, int]:
    """Convert distance d on Hilbert curve of side 2^n to (x, y)."""
    rx = ry = 0
    x = y = 0
    t = d
    s = 1
    while s < n:
        rx = 1 & (t // 2)
        ry = 1 & (t ^ rx)
        if ry == 0:
            if rx == 1:
                x = s - 1 - x
                y = s - 1 - y
            x, y = y, x
        x += s * rx
        y += s * ry
        t //= 4
        s *= 2
    return x, y


def _build_rank_map() -> list[list[float]]:
    n = 1 << _ORDER
    rank: list[list[float | None]] = [[None] * CW for _ in range(CH)]
    rank_counter = 0
    for d in range(n * n):
        x, y = _d2xy(n, d)
        if 0 <= x < CW and 0 <= y < CH and rank[y][x] is None:
            rank[y][x] = rank_counter
            rank_counter += 1
    # Defensive: any pixels not reached (shouldn't happen with order 8) get late ranks.
    for y in range(CH):
        for x in range(CW):
            if rank[y][x] is None:
                rank[y][x] = rank_counter
                rank_counter += 1
    total = float(CW * CH)
    return [[rank[y][x] / total for x in range(CW)] for y in range(CH)]


_RANK_MAP = disk_cached('hilbert_fill_rank_map_v1', lambda: _build_rank_map())
_RANK_MAP_NP = np.array(_RANK_MAP, dtype=np.float32)


class HilbertFill(BaseAnimation):
    name = "hilbert_fill"
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
