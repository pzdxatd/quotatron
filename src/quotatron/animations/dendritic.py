"""Dendritic growth via diffusion-limited aggregation."""
from __future__ import annotations
import random
import numpy as np
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached

CW, CH = 250, 122


def _build_rank_map() -> list[list[float]]:
    rng = random.Random(181)
    # Start with a single seed at canvas center.
    stuck: dict[tuple[int, int], int] = {(CW // 2, CH // 2): 0}
    rank_counter = 1
    target = int(CW * CH * 0.6)  # grow to ~60% of canvas, then fill rest by rank

    max_walks = 5000
    while rank_counter < target and max_walks > 0:
        max_walks -= 1
        # Spawn a particle at a random edge.
        edge = rng.randint(0, 3)
        if edge == 0:
            x, y = rng.randint(0, CW - 1), 0
        elif edge == 1:
            x, y = rng.randint(0, CW - 1), CH - 1
        elif edge == 2:
            x, y = 0, rng.randint(0, CH - 1)
        else:
            x, y = CW - 1, rng.randint(0, CH - 1)
        # Random walk until it sticks adjacent to the structure or escapes.
        for _ in range(2000):
            # Check if any 4-neighbor is already stuck.
            stuck_nearby = any(
                (x + dx, y + dy) in stuck for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            if stuck_nearby:
                stuck[(x, y)] = rank_counter
                rank_counter += 1
                break
            x += rng.choice([-1, 0, 1])
            y += rng.choice([-1, 0, 1])
            if not (0 <= x < CW and 0 <= y < CH):
                break  # escaped — discard

    # Fill unvisited cells with later ranks (reveal last).
    rank: list[list[int | None]] = [[None] * CW for _ in range(CH)]
    for (x, y), r in stuck.items():
        rank[y][x] = r
    next_rank = rank_counter
    for y in range(CH):
        for x in range(CW):
            if rank[y][x] is None:
                rank[y][x] = next_rank
                next_rank += 1
    total = float(CW * CH)
    return [[rank[y][x] / total for x in range(CW)] for y in range(CH)]


_RANK_MAP = disk_cached('dendritic_rank_map_v1', lambda: _build_rank_map())
_RANK_MAP_NP = np.array(_RANK_MAP, dtype=np.float32)


class Dendritic(BaseAnimation):
    name = "dendritic"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        mask = Image.fromarray((_RANK_MAP_NP <= t).astype(np.uint8) * 255, mode='L')
        out = ctx.from_image.copy()
        out.paste(ctx.to_image, mask=mask)
        return out
