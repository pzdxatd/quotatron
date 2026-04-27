"""Typewriter-style block reveal in row-major order."""
from __future__ import annotations
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation

_CELL_W, _CELL_H = 12, 15


class TypewriterOverprint(BaseAnimation):
    name = "typewriter_overprint"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        cols = (w + _CELL_W - 1) // _CELL_W
        rows = (h + _CELL_H - 1) // _CELL_H
        total_cells = cols * rows
        n = int(t * total_cells)
        out = ctx.from_image.copy()
        mask = Image.new("1", (w, h), 0)
        md = ImageDraw.Draw(mask)
        for i in range(n):
            r = i // cols
            c = i % cols
            x0 = c * _CELL_W
            y0 = r * _CELL_H
            x1 = min(w, x0 + _CELL_W)
            y1 = min(h, y0 + _CELL_H)
            md.rectangle((x0, y0, x1, y1), fill=1)
        out.paste(ctx.to_image, mask=mask)
        return out
