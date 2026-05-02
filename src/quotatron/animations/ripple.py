"""Ripple — single expanding circular wavefront from center."""
from __future__ import annotations
import math
import numpy as np
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached

CW, CH = 250, 122


def _build_dist_map() -> list[list[float]]:
    cx, cy = CW / 2, CH / 2
    return [[math.hypot(x - cx, y - cy) for x in range(CW)] for y in range(CH)]


_DIST_MAP = disk_cached('ripple_dist_map_v1', lambda: _build_dist_map())
_MAX_DIST = math.hypot(CW / 2, CH / 2)  # ~139
_DIST_MAP_NP = np.array(_DIST_MAP, dtype=np.float32)


class Ripple(BaseAnimation):
    name = "ripple"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        mask = Image.fromarray((_DIST_MAP_NP <= t * _MAX_DIST).astype(np.uint8) * 255, mode='L')
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
