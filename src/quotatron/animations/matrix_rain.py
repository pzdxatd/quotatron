"""Matrix-rain style — staggered per-column reveal in pseudo-random column order."""
from __future__ import annotations
import random
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached

CW = 250


def _build_column_phases() -> list[float]:
    # Each column gets a deterministic phase in [0, 0.4]; columns reveal at
    # different start times so the rain looks staggered.
    rng = random.Random(211)
    phases = [rng.random() * 0.4 for _ in range(CW)]
    return phases


_PHASES = disk_cached('matrix_rain_phases_v1', lambda: _build_column_phases())


class MatrixRain(BaseAnimation):
    name = "matrix_rain"
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
        # local_t is rescaled: at t=phase the column starts; at t=1 it's fully revealed.
        for x in range(w):
            phase = _PHASES[x]
            if t <= phase:
                continue
            local_t = (t - phase) / (1 - phase) if phase < 1 else 1.0
            fill_h = int(local_t * h)
            if fill_h > 0:
                md.line((x, 0, x, fill_h - 1), fill=1)
        out.paste(ctx.to_image, mask=mask)
        return out
