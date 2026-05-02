"""Snake-pattern (boustrophedon) reveal."""
from __future__ import annotations
import numpy as np
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached

CW, CH = 250, 122


def _build_rank_map() -> np.ndarray:
    rank = np.zeros((CH, CW), dtype=np.float32)
    total = float(CW * CH)
    count = 0
    for y in range(CH):
        xs = range(CW) if y % 2 == 0 else range(CW - 1, -1, -1)
        for x in xs:
            rank[y, x] = count / total
            count += 1
    return rank


_RANK_MAP_NP = disk_cached('snake_fill_rank_map_np_v1', lambda: _build_rank_map())


class SnakeFill(BaseAnimation):
    name = "snake_fill"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        mask = Image.fromarray((_RANK_MAP_NP < t).astype(np.uint8) * 255, mode='L')
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
