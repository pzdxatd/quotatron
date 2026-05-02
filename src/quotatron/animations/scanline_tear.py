"""30 horizontal scanlines revealing in randomized order."""
from __future__ import annotations
import random
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached

_N_SCANLINES = 30


def _build_scanline_thresholds() -> list[float]:
    rng = random.Random(89)
    thresholds = [(i + 1) / _N_SCANLINES for i in range(_N_SCANLINES)]
    rng.shuffle(thresholds)
    return thresholds


_SCANLINE_THRESHOLDS = disk_cached('scanline_tear_scanline_thresholds_v1', lambda: _build_scanline_thresholds())


class ScanlineTear(BaseAnimation):
    name = "scanline_tear"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        scanline_h = h / _N_SCANLINES
        out = ctx.from_image.copy()
        mask = Image.new("1", (w, h), 0)
        md = ImageDraw.Draw(mask)
        for i, threshold in enumerate(_SCANLINE_THRESHOLDS):
            if t >= threshold:
                y0 = i * scanline_h
                y1 = (i + 1) * scanline_h
                md.rectangle((0, y0, w, y1), fill=1)
        out.paste(ctx.to_image, mask=mask)
        return out
