"""Distance-based diffusion dissolve from 6 fixed seed points."""
from __future__ import annotations
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation


# Six fixed seed points spread across the canvas for variety.
_SEEDS = [(20, 30), (200, 20), (125, 60), (40, 100), (210, 95), (160, 55)]


class DiffusionDissolve(BaseAnimation):
    name = "diffusion_dissolve"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        # Manhattan distance from nearest seed for each pixel. With these 6
        # well-distributed seeds, the actual max-distance in the canvas is
        # only ~75 pixels; cap reveal at 80 so the t-sweep covers the visual
        # range smoothly rather than saturating by t=0.25.
        max_dist = 80
        threshold = int(t * max_dist)
        mask = Image.new("1", (w, h), 0)
        mp = mask.load()
        for y in range(h):
            for x in range(w):
                d = min(abs(x - sx) + abs(y - sy) for sx, sy in _SEEDS)
                if d <= threshold:
                    mp[x, y] = 1
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
