"""Per-row reveal in randomized order — each row appears at its own t-threshold."""
from __future__ import annotations
import random
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached


def _build_row_thresholds(height: int) -> list[float]:
    rng = random.Random(53)
    thresholds = [(i + 1) / height for i in range(height)]
    rng.shuffle(thresholds)
    return thresholds


_ROW_THRESHOLDS = disk_cached('line_shuffle_row_thresholds_v1', lambda: _build_row_thresholds(122))


class LineShuffle(BaseAnimation):
    name = "line_shuffle"
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
        for y, threshold in enumerate(_ROW_THRESHOLDS):
            if t >= threshold:
                md.line((0, y, w - 1, y), fill=1)
        out.paste(ctx.to_image, mask=mask)
        return out
