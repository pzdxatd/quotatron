"""Per-column rain — each column fills from top with staggered start."""
from __future__ import annotations
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation


class ColumnRain(BaseAnimation):
    name = "column_rain"
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
        # Each column has a phase offset 0..0.3 based on (x % 7).
        # Effective t for column x = max(0, (t - phase) / (1 - phase_max)).
        phase_max = 0.3
        for x in range(w):
            phase = (x % 7) * (phase_max / 6)
            local_t = (t - phase) / (1 - phase_max)
            if local_t <= 0:
                continue
            local_t = min(1.0, local_t)
            fill_h = int(local_t * h)
            if fill_h > 0:
                md.line((x, 0, x, fill_h - 1), fill=1)
        out.paste(ctx.to_image, mask=mask)
        return out
