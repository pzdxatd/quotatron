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
        # With 5 well-distributed centers spanning the canvas, the farthest
        # uncovered point is only ~70px from some center. Lowering max_r so
        # the t-sweep visibly progresses across the full 0..1 range instead
        # of saturating by t≈0.25.
        max_r = 80
        r = t * max_r
        out = ctx.from_image.copy()
        mask = Image.new("1", (w, h), 0)
        md = ImageDraw.Draw(mask)
        for cx, cy in _CENTERS:
            md.ellipse((cx - r, cy - r, cx + r, cy + r), fill=1)
        out.paste(ctx.to_image, mask=mask)
        return out
