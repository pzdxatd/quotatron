"""8x4 grid where each cell reveals at its own deterministic t-threshold."""
from __future__ import annotations
import random
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached


# Pre-compute reveal thresholds for the 8x4 = 32 cells, deterministic.
def _build_thresholds() -> list[float]:
    rng = random.Random(7)
    thresholds = [(i + 1) / 32 for i in range(32)]
    rng.shuffle(thresholds)
    return thresholds

_THRESHOLDS = disk_cached('grid_stamp_thresholds_v1', lambda: _build_thresholds())


class GridStamp(BaseAnimation):
    name = "grid_stamp"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        cols, rows = 8, 4
        cell_w = w / cols
        cell_h = h / rows
        out = ctx.from_image.copy()
        mask = Image.new("1", (w, h), 0)
        md = ImageDraw.Draw(mask)
        for r in range(rows):
            for c in range(cols):
                idx = r * cols + c
                if t >= _THRESHOLDS[idx]:
                    md.rectangle(
                        (c * cell_w, r * cell_h, (c + 1) * cell_w, (r + 1) * cell_h),
                        fill=1,
                    )
        out.paste(ctx.to_image, mask=mask)
        return out
