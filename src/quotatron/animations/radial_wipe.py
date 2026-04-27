"""Radial wipe expanding from canvas center."""
from __future__ import annotations
from math import hypot
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation


class RadialWipe(BaseAnimation):
    name = "radial_wipe"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        cx, cy = w / 2, h / 2
        r = t * hypot(cx, cy)
        out = ctx.from_image.copy()
        mask = Image.new("1", (w, h), 0)
        ImageDraw.Draw(mask).ellipse((cx - r, cy - r, cx + r, cy + r), fill=1)
        out.paste(ctx.to_image, mask=mask)
        return out
