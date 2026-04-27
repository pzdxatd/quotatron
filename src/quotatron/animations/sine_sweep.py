"""Sine-wobble vertical sweep from left to right."""
from __future__ import annotations
import math
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation


class SineSweep(BaseAnimation):
    name = "sine_sweep"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        out = ctx.from_image.copy()
        mask = Image.new("1", (w, h), 0)
        md = ImageDraw.Draw(mask)
        # For each row, compute the threshold x position. Reveal cells x < threshold.
        # Wobble is purely cosmetic — each row's threshold gets a sin offset of +/-10px.
        for y in range(h):
            offset = math.sin(y * 0.15) * 10
            x_threshold = t * w + offset
            if x_threshold > 0:
                md.line((0, y, min(w - 1, int(x_threshold)), y), fill=1)
        out.paste(ctx.to_image, mask=mask)
        return out
