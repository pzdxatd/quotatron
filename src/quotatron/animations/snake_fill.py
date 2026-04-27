"""Snake-pattern (boustrophedon) reveal."""
from __future__ import annotations
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation


class SnakeFill(BaseAnimation):
    name = "snake_fill"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        n = int(t * w * h)
        mask = Image.new("1", (w, h), 0)
        mp = mask.load()
        count = 0
        for y in range(h):
            xs = range(w) if y % 2 == 0 else range(w - 1, -1, -1)
            for x in xs:
                if count >= n:
                    break
                mp[x, y] = 1
                count += 1
            if count >= n:
                break
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
