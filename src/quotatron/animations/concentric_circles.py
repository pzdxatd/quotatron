"""Five fixed-center circles growing in unison."""
from __future__ import annotations
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation


_CENTERS = [(50, 30), (200, 30), (125, 60), (50, 95), (200, 95)]


class ConcentricCircles(BaseAnimation):
    name = "concentric_circles"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        # Max radius needed for any of these centers to reach the farthest
        # corner: ~hypot(200, 95) ≈ 222. Use 200 so the canvas is fully
        # covered by t=1.
        max_r = 200
        r = t * max_r
        out = ctx.from_image.copy()
        mask = Image.new("1", (w, h), 0)
        md = ImageDraw.Draw(mask)
        for cx, cy in _CENTERS:
            md.ellipse((cx - r, cy - r, cx + r, cy + r), fill=1)
        out.paste(ctx.to_image, mask=mask)
        return out
