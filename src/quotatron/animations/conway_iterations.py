"""Conway's Game of Life — pixels that survive longer reveal first."""
from __future__ import annotations
import random
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation

CW, CH = 250, 122
_GENERATIONS = 8


def _step(grid: list[list[int]]) -> list[list[int]]:
    h = len(grid)
    w = len(grid[0])
    nxt = [[0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            n = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w:
                        n += grid[ny][nx]
            alive = grid[y][x]
            if alive and n in (2, 3):
                nxt[y][x] = 1
            elif not alive and n == 3:
                nxt[y][x] = 1
    return nxt


def _build_lifetime_map() -> list[list[int]]:
    rng = random.Random(149)
    # ~30% initial alive density gives reasonable Conway behavior.
    grid = [[1 if rng.random() < 0.3 else 0 for _ in range(CW)] for _ in range(CH)]
    lifetime = [[0] * CW for _ in range(CH)]
    for _ in range(_GENERATIONS):
        for y in range(CH):
            for x in range(CW):
                if grid[y][x]:
                    lifetime[y][x] += 1
        grid = _step(grid)
    return lifetime  # values in [0, _GENERATIONS]


_LIFETIME_MAP = _build_lifetime_map()
_MAX_LIFETIME = max(max(row) for row in _LIFETIME_MAP) or 1


class ConwayIterations(BaseAnimation):
    name = "conway_iterations"
    duration_default = 10.0
    target_fps = 4
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        w, h = ctx.width, ctx.height
        # Pixels with high lifetime reveal earlier. Map lifetime in [0, max] to
        # threshold in [0, 1] inversely so high-life => low-threshold => reveals first.
        mask = Image.new("1", (w, h), 0)
        mp = mask.load()
        for y in range(h):
            row = _LIFETIME_MAP[y]
            for x in range(w):
                threshold = 1.0 - row[x] / _MAX_LIFETIME
                if t >= threshold:
                    mp[x, y] = 1
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
