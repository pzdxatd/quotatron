"""Diagonal wipe from upper-left to lower-right replacing from_image with to_image."""
from __future__ import annotations
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation


class DiagonalWipe(BaseAnimation):
    name = "diagonal_wipe"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        # Diagonal line equation: x + y < threshold ⇒ from to_image.
        # Total diagonal length: w + h. Threshold sweeps 0 → w+h as t: 0→1.
        w, h = ctx.width, ctx.height
        threshold = (w + h) * t
        out = ctx.from_image.copy()
        mask = Image.new("1", (w, h), 0)
        md = ImageDraw.Draw(mask)
        # Triangle bounded by x + y < threshold
        md.polygon(
            [(0, 0), (min(w, threshold), 0), (0, min(h, threshold))],
            fill=1,
        )
        # If threshold > w, also fill rectangle and second triangle (parallelogram).
        if threshold > w:
            md.polygon(
                [(0, 0), (w, 0), (w, min(h, threshold - w)), (0, 0)],
                fill=1,
            )
            md.polygon(
                [(0, 0), (w, min(h, threshold - w)),
                 (min(w, threshold), 0)],
                fill=1,
            )
        out.paste(ctx.to_image, mask=mask)
        return out
