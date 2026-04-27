"""Animation plugin contract."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Literal
from PIL import Image
from quotatron.models import Polarity

PANEL_MIN_FRAME_SECONDS = 0.3   # Waveshare 2.13" partial-refresh floor


def frame_count_for_duration(duration_s: float, target_fps: int) -> int:
    """Compute frame count respecting both target FPS and panel minimum frame time.

    The panel_max derived from PANEL_MIN_FRAME_SECONDS is the hardware ceiling
    for long animations; for short animations we treat target_fps as a soft floor
    so a 1s/5fps animation still yields ~5 frames rather than collapsing to 3.
    """
    requested = int(round(duration_s * target_fps))
    panel_max = int(duration_s / PANEL_MIN_FRAME_SECONDS)
    return max(2, min(requested, max(panel_max, target_fps)))


@dataclass
class AnimationContext:
    from_image: Image.Image
    to_image: Image.Image
    polarity: Polarity
    width: int
    height: int

    @property
    def fg(self) -> int:
        return self.polarity.fg

    @property
    def bg(self) -> int:
        return self.polarity.bg


class BaseAnimation(ABC):
    name: str = "unnamed"
    duration_default: float = 10.0
    target_fps: int = 5
    palette: Literal["auto", "force_white_on_black", "force_black_on_white"] = "auto"

    @abstractmethod
    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        """Render one frame at progress t in [0,1]. Must return a 1-bit image."""

    def frames(
        self, ctx: AnimationContext, duration_s: float | None = None
    ) -> Iterator[Image.Image]:
        d = duration_s if duration_s is not None else self.duration_default
        n = frame_count_for_duration(d, self.target_fps)
        for i in range(n):
            t = i / max(1, n - 1)
            img = self.render(t, ctx)
            if img.mode != "1":
                img = img.convert("1")
            yield img
