"""Flood-fill from upper-left corner using Manhattan distance order."""
from __future__ import annotations
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation


def _build_order(width: int, height: int) -> list[tuple[int, int]]:
    coords = [(x, y) for y in range(height) for x in range(width)]
    coords.sort(key=lambda c: c[0] + c[1])
    return coords


_ORDER = _build_order(250, 122)


class FloodFill(BaseAnimation):
    name = "flood_fill"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        n = int(t * len(_ORDER))
        mask = Image.new("1", (w, h), 0)
        mp = mask.load()
        for x, y in _ORDER[:n]:
            mp[x, y] = 1
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
