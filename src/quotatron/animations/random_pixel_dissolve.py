"""Pseudo-random pixel-by-pixel dissolve. Deterministic via fixed seed."""
from __future__ import annotations
import random
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation


class RandomPixelDissolve(BaseAnimation):
    name = "random_pixel_dissolve"
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
        # Deterministic shuffle of pixel coords seeded by a fixed seed.
        rng = random.Random(42)
        coords = [(x, y) for y in range(h) for x in range(w)]
        rng.shuffle(coords)
        # Build a mask with the first n shuffled coords set.
        mask = Image.new("1", (w, h), 0)
        mp = mask.load()
        for x, y in coords[:n]:
            mp[x, y] = 1
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
