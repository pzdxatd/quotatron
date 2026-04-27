"""Ripple — single expanding circular wavefront from center."""
from __future__ import annotations
import math
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation

CW, CH = 250, 122


def _build_dist_map() -> list[list[float]]:
    cx, cy = CW / 2, CH / 2
    return [[math.hypot(x - cx, y - cy) for x in range(CW)] for y in range(CH)]


_DIST_MAP = _build_dist_map()
_MAX_DIST = math.hypot(CW / 2, CH / 2)  # ~139


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
        w, h = ctx.width, ctx.height
        threshold = t * _MAX_DIST
        mask = Image.new("1", (w, h), 0)
        mp = mask.load()
        for y in range(h):
            row = _DIST_MAP[y]
            for x in range(w):
                if row[x] <= threshold:
                    mp[x, y] = 1
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
