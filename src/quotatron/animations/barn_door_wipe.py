"""Barn-door wipe — two rectangles meeting from left and right edges."""
from __future__ import annotations
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation


class BarnDoorWipe(BaseAnimation):
    name = "barn_door_wipe"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        half = t * w / 2
        out = ctx.from_image.copy()
        mask = Image.new("1", (w, h), 0)
        md = ImageDraw.Draw(mask)
        md.rectangle((0, 0, half, h), fill=1)
        md.rectangle((w - half, 0, w, h), fill=1)
        out.paste(ctx.to_image, mask=mask)
        return out
