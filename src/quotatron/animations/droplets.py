"""Eight fixed-center droplets growing with t² acceleration."""
from __future__ import annotations
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation


_DROP_CENTERS = [
    (30, 25), (90, 50), (160, 30), (220, 70),
    (50, 100), (130, 90), (200, 100), (110, 20),
]


class Droplets(BaseAnimation):
    name = "droplets"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        # Each drop's radius accelerates as t² so spread feels organic.
        # Cap radius so that at t=1 the canvas is fully covered.
        # max(hypot from any drop to a corner) ~ 130, t² scaling needs r=130 at t=1
        # so coefficient ≈ 130. Use 160 for safety margin.
        r = t * t * 160
        out = ctx.from_image.copy()
        mask = Image.new("1", (w, h), 0)
        md = ImageDraw.Draw(mask)
        for cx, cy in _DROP_CENTERS:
            md.ellipse((cx - r, cy - r, cx + r, cy + r), fill=1)
        out.paste(ctx.to_image, mask=mask)
        return out
