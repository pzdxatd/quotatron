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
    if duration_s <= 0 or target_fps <= 0:
        raise ValueError(f"duration_s and target_fps must be positive; got {duration_s=}, {target_fps=}")
    requested = int(round(duration_s * target_fps))
    panel_max = int(duration_s / PANEL_MIN_FRAME_SECONDS)
    return max(2, min(requested, max(panel_max, target_fps)))


@dataclass(frozen=True)
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
    # Only "auto" is consumed today; widen this Literal when force-* variants
    # have a real consumer.
    palette: Literal["auto"] = "auto"

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Catch missing-name bugs at import time, before the registry collides.
        if cls.name == "unnamed":
            raise TypeError(
                f"{cls.__module__}.{cls.__qualname__} must override BaseAnimation.name"
            )

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
            # Fail loud on wrong-shape returns. Silent .convert("1") would let
            # an animation that returns RGB by mistake produce visually-plausible-
            # but-dithered output that survives review.
            if img.mode != "1":
                raise ValueError(
                    f"{type(self).__name__}.render returned mode={img.mode!r}; expected '1'"
                )
            if img.size != (ctx.width, ctx.height):
                raise ValueError(
                    f"{type(self).__name__}.render returned size={img.size}; "
                    f"expected {(ctx.width, ctx.height)}"
                )
            yield img
