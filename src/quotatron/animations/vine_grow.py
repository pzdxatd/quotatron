"""Vine-growth via deterministic random walk from bottom-center with branching."""
from __future__ import annotations
import random
import numpy as np
from PIL import Image
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.animations._precompute import disk_cached

CW, CH = 250, 122


def _build_rank_map() -> list[list[float]]:
    rng = random.Random(167)
    visited: dict[tuple[int, int], int] = {}
    rank_counter = 0
    # Multiple walkers, each starts from bottom-center and walks upward+sideways.
    # Branch probability: each walker can split (spawn another) with p=0.1 per step.
    walkers: list[tuple[int, int]] = [(CW // 2, CH - 1)]
    max_steps = 60000  # plenty of headroom for full canvas coverage
    steps = 0
    while walkers and rank_counter < CW * CH and steps < max_steps:
        new_walkers: list[tuple[int, int]] = []
        for x, y in walkers:
            if (x, y) not in visited and 0 <= x < CW and 0 <= y < CH:
                visited[(x, y)] = rank_counter
                rank_counter += 1
            # Move: prefer upward, sometimes sideways.
            dx = rng.choice([-1, -1, 0, 0, 1, 1])
            dy = rng.choice([-1, -1, -1, 0, 0, 1])  # bias upward
            nx, ny = x + dx, y + dy
            if 0 <= nx < CW and 0 <= ny < CH:
                new_walkers.append((nx, ny))
            # Branch.
            if rng.random() < 0.1 and len(new_walkers) < 200:
                bx = rng.randint(0, CW - 1)
                by = rng.randint(0, CH - 1)
                new_walkers.append((bx, by))
        walkers = new_walkers
        steps += 1

    # Any pixels never visited get max rank (revealed last).
    rank: list[list[float]] = [[float("inf")] * CW for _ in range(CH)]
    for (x, y), r in visited.items():
        rank[y][x] = r
    # Assign unvisited pixels sequentially after all visited.
    next_rank = rank_counter
    for y in range(CH):
        for x in range(CW):
            if rank[y][x] == float("inf"):
                rank[y][x] = next_rank
                next_rank += 1
    # Normalize to [0, 1].
    total = float(CW * CH)
    return [[rank[y][x] / total for x in range(CW)] for y in range(CH)]


_RANK_MAP_NP = disk_cached(
    "vine_grow_rank_v1",
    lambda: np.array(_build_rank_map(), dtype=np.float32),
)


class VineGrow(BaseAnimation):
    name = "vine_grow"
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
