"""16x8 grid of blocks revealing in randomized order."""
from __future__ import annotations
import random
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached

_COLS, _ROWS = 16, 8
_N_BLOCKS = _COLS * _ROWS


def _build_block_thresholds() -> list[float]:
    rng = random.Random(67)
    thresholds = [(i + 1) / _N_BLOCKS for i in range(_N_BLOCKS)]
    rng.shuffle(thresholds)
    return thresholds


_BLOCK_THRESHOLDS = disk_cached('block_jitter_block_thresholds_v1', lambda: _build_block_thresholds())


class BlockJitter(BaseAnimation):
    name = "block_jitter"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        cell_w = w / _COLS
        cell_h = h / _ROWS
        out = ctx.from_image.copy()
        mask = Image.new("1", (w, h), 0)
        md = ImageDraw.Draw(mask)
        for r in range(_ROWS):
            for c in range(_COLS):
                idx = r * _COLS + c
                if t >= _BLOCK_THRESHOLDS[idx]:
                    md.rectangle(
                        (c * cell_w, r * cell_h, (c + 1) * cell_w, (r + 1) * cell_h),
                        fill=1,
                    )
        out.paste(ctx.to_image, mask=mask)
        return out
