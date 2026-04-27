"""Ordered-dither dissolve via 8x8 Bayer threshold matrix."""
from __future__ import annotations
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation

# Standard 8x8 Bayer matrix, values 0..63.
BAYER_8 = [
    [ 0, 32,  8, 40,  2, 34, 10, 42],
    [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44,  4, 36, 14, 46,  6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22],
    [ 3, 35, 11, 43,  1, 33,  9, 41],
    [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47,  7, 39, 13, 45,  5, 37],
    [63, 31, 55, 23, 61, 29, 53, 21],
]


class OrderedDitherDissolve(BaseAnimation):
    name = "ordered_dither_dissolve"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        threshold = t * 64
        mask = Image.new("1", (w, h), 0)
        mp = mask.load()
        for y in range(h):
            row = BAYER_8[y % 8]
            for x in range(w):
                if row[x % 8] < threshold:
                    mp[x, y] = 1
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
