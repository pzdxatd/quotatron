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


def _build_threshold_map() -> list[list[float]]:
    """Run 8 Conway generations, then assign each pixel a reveal threshold by
    rank: pixels alive in many generations get low thresholds (reveal early).
    The rank-based mapping forces a uniform reveal rate so the animation
    progresses smoothly across the full t-sweep instead of clustering reveals
    in the late frames (Conway naturally has a heavy short-lifetime tail)."""
    rng = random.Random(149)
    grid = [[1 if rng.random() < 0.3 else 0 for _ in range(CW)] for _ in range(CH)]
    lifetime = [[0] * CW for _ in range(CH)]
    for _ in range(_GENERATIONS):
        for y in range(CH):
            for x in range(CW):
                if grid[y][x]:
                    lifetime[y][x] += 1
        grid = _step(grid)

    # Rank-based threshold: sort all pixels by lifetime descending; the i-th
    # ranked pixel gets threshold = i / total. Tied lifetimes break by (y, x)
    # for determinism.
    flat = [(lifetime[y][x], y, x) for y in range(CH) for x in range(CW)]
    flat.sort(key=lambda r: (-r[0], r[1], r[2]))
    threshold = [[0.0] * CW for _ in range(CH)]
    total = float(len(flat))
    for rank, (_life, y, x) in enumerate(flat):
        threshold[y][x] = rank / total
    return threshold


_THRESHOLD_MAP = _build_threshold_map()


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
        mask = Image.new("1", (w, h), 0)
        mp = mask.load()
        for y in range(h):
            row = _THRESHOLD_MAP[y]
            for x in range(w):
                if t >= row[x]:
                    mp[x, y] = 1
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
