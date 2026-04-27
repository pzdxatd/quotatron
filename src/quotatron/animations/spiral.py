"""Archimedean spiral path — pixels reveal in outward-spiral order."""
from __future__ import annotations
import math
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation

CW, CH = 250, 122


def _build_rank_map() -> list[list[float]]:
    cx, cy = CW / 2, CH / 2
    # Walk an Archimedean spiral: r = a * theta, sample many points.
    # Choose a so the spiral covers the canvas in ~50 turns.
    a = 1.0  # radius grows by 1 per radian
    seen: dict[tuple[int, int], int] = {}
    rank_counter = 0
    theta = 0.0
    d_theta = 0.05  # angular step
    max_r = math.hypot(cx, cy) + 5
    while True:
        r = a * theta
        if r > max_r:
            break
        x = int(round(cx + r * math.cos(theta)))
        y = int(round(cy + r * math.sin(theta)))
        if 0 <= x < CW and 0 <= y < CH and (x, y) not in seen:
            seen[(x, y)] = rank_counter
            rank_counter += 1
        theta += d_theta
    # Fill any unvisited pixels (corners outside the spiral) at the end.
    rank: list[list[int | None]] = [[None] * CW for _ in range(CH)]
    for (x, y), r in seen.items():
        rank[y][x] = r
    next_rank = rank_counter
    for y in range(CH):
        for x in range(CW):
            if rank[y][x] is None:
                rank[y][x] = next_rank
                next_rank += 1
    total = float(CW * CH)
    return [[rank[y][x] / total for x in range(CW)] for y in range(CH)]


_RANK_MAP = _build_rank_map()


class Spiral(BaseAnimation):
    name = "spiral"
    duration_default = 10.0
    target_fps = 5
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
            row = _RANK_MAP[y]
            for x in range(w):
                if t >= row[x]:
                    mp[x, y] = 1
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
