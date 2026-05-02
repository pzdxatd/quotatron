"""Distance-based diffusion dissolve from 6 fixed seed points."""
from __future__ import annotations
import numpy as np
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached

CW, CH = 250, 122
_SEEDS = [(20, 30), (200, 20), (125, 60), (40, 100), (210, 95), (160, 55)]
_MAX_DIST = 80


def _build_dist_map() -> np.ndarray:
    ys = np.arange(CH, dtype=np.float32).reshape(CH, 1)
    xs = np.arange(CW, dtype=np.float32).reshape(1, CW)
    dist = np.full((CH, CW), np.inf, dtype=np.float32)
    for sx, sy in _SEEDS:
        d = np.abs(xs - sx) + np.abs(ys - sy)
        np.minimum(dist, d, out=dist)
    return dist


_DIST_MAP_NP = disk_cached('diffusion_dissolve_dist_map_np_v1', lambda: _build_dist_map())


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
        mask = Image.fromarray((_DIST_MAP_NP <= t * _MAX_DIST).astype(np.uint8) * 255, mode='L')
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
