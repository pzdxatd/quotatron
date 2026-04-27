"""Expanding-rectangles wipe — single rectangle growing from center."""
from __future__ import annotations
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation


class ExpandingRectangles(BaseAnimation):
    name = "expanding_rectangles"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        # Half-size of the filled rectangle: scales with t toward max(w,h)/2 + margin
        # so by t=1 the rect covers the full canvas.
        max_half = max(w, h)
        half_w = t * max_half / 2 * (w / max(w, h))
        half_h = t * max_half / 2 * (h / max(w, h))
        cx, cy = w / 2, h / 2
        out = ctx.from_image.copy()
        mask = Image.new("1", (w, h), 0)
        ImageDraw.Draw(mask).rectangle(
            (cx - half_w, cy - half_h, cx + half_w, cy + half_h), fill=1
        )
        out.paste(ctx.to_image, mask=mask)
        return out
