"""Unit tests for the asyncio scheduler main loop."""
from __future__ import annotations

import asyncio
import datetime as dt
from typing import Iterator

import pytest
from PIL import Image

from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.config import (
    AnimationsConfig,
    Config,
    CycleConfig,
)
from quotatron.content import ContentLibrary
from quotatron.display.mock import MockDisplay
from quotatron.models import ContentItem
from quotatron.scheduler import Scheduler


def _make_lib(n: int = 5) -> ContentLibrary:
    return ContentLibrary(items=[
        ContentItem(
            kind="quote", text=f"q{i}", author="a",
            category="philosophy", source="bundled",
        )
        for i in range(n)
    ])


def test_scheduler_runs_one_full_cycle_in_test_mode() -> None:
    cfg = Config(cycle=CycleConfig(quote_seconds=1, animation_seconds=1))
    display = MockDisplay()
    sch = Scheduler(
        config=cfg, library=_make_lib(), display=display,
        test_max_cycles=2, _test_sleep_override=0.0,
    )
    asyncio.run(sch.run())
    fulls = sum(1 for m, _ in display.history if m == "full")
    # Cycle 0: full (no anim — first frame). Cycle 1: anim + full. = 2.
    assert fulls == 2


def test_scheduler_flips_polarity_each_cycle() -> None:
    cfg = Config(cycle=CycleConfig(quote_seconds=1, animation_seconds=1, invert_polarity_every=1))
    display = MockDisplay()
    sch = Scheduler(
        config=cfg, library=_make_lib(1), display=display,
        test_max_cycles=4, _test_sleep_override=0.0,
    )
    asyncio.run(sch.run())
    assert list(sch.polarity_history) == ["normal", "inverted", "normal", "inverted"]


def test_animation_exception_falls_back_to_clean_full_refresh() -> None:
    """A buggy animation must not crash the device — the cycle should still
    end with a clean display_full(dest) so the panel is always in a known
    state for the next cycle."""

    class _Boom(BaseAnimation):
        name = "_boom"

        def render(self, t: float, ctx: AnimationContext) -> Image.Image:
            raise RuntimeError("intentional test failure")

    cfg = Config(cycle=CycleConfig(quote_seconds=1, animation_seconds=1))
    display = MockDisplay()
    sch = Scheduler(
        config=cfg, library=_make_lib(), display=display,
        test_max_cycles=2, _test_sleep_override=0.0,
    )
    # Inject the buggy animation so the second cycle hits the exception path.
    sch._pick_animation = lambda: _Boom()  # type: ignore[method-assign]
    asyncio.run(sch.run())
    # The exception is caught; display_full(dest) must still fire so the panel
    # ends in a known state. exit_partial_mode is NOT called separately —
    # display_full() handles the partial→full re-init internally when _partial=True.
    modes = [m for m, _ in display.history]
    fulls = sum(1 for m in modes if m == "full")
    assert fulls == 2
    # display_full must follow the failed enter_partial
    partial_idx = modes.index("enter_partial")
    assert "full" in modes[partial_idx:]


def test_blocklist_excludes_animations() -> None:
    """Blocklisted animation names must not appear in _pick_animation."""
    # Block every real animation; the picker must fall back to simple_fade.
    from quotatron.animations import registry
    cfg = Config(
        cycle=CycleConfig(),
        animations=AnimationsConfig(blocklist=list(registry().keys()), shuffle="random"),
    )
    display = MockDisplay()
    sch = Scheduler(config=cfg, library=_make_lib(), display=display)
    anim = sch._pick_animation()
    assert anim.name == "simple_fade"


def test_sequential_shuffle_progresses_index_each_cycle() -> None:
    """With shuffle=sequential, _pick_animation walks the registry in order."""
    cfg = Config(
        cycle=CycleConfig(),
        animations=AnimationsConfig(shuffle="sequential"),
    )
    display = MockDisplay()
    sch = Scheduler(config=cfg, library=_make_lib(), display=display)
    # Two consecutive picks at the same _cycle_count return the same animation
    # (deterministic). Bumping the cycle count yields a different animation.
    first = sch._pick_animation()
    sch._cycle_count = 0
    again = sch._pick_animation()
    assert first.name == again.name
    sch._cycle_count = 1
    different = sch._pick_animation()
    assert different.name != first.name


def test_deep_clean_runs_at_03_and_only_once_per_day() -> None:
    """Deep clean must fire exactly once when the local clock crosses 03:00,
    and not again on subsequent cycles within the same calendar day."""
    cfg = Config(cycle=CycleConfig(quote_seconds=1, animation_seconds=1))
    display = MockDisplay()
    # Fixed clock at 03:15 for every iteration.
    fixed = dt.datetime(2026, 1, 1, 3, 15, 0)
    sch = Scheduler(
        config=cfg, library=_make_lib(), display=display,
        test_max_cycles=3, _test_sleep_override=0.0,
        _now=lambda: fixed,
    )
    asyncio.run(sch.run())
    cleans = sum(1 for m, _ in display.history if m == "deep_clean")
    assert cleans == 1


def test_deep_clean_does_not_run_outside_03_hour() -> None:
    cfg = Config(cycle=CycleConfig(quote_seconds=1, animation_seconds=1))
    display = MockDisplay()
    fixed = dt.datetime(2026, 1, 1, 14, 0, 0)  # 14:00, not 03:xx
    sch = Scheduler(
        config=cfg, library=_make_lib(), display=display,
        test_max_cycles=3, _test_sleep_override=0.0,
        _now=lambda: fixed,
    )
    asyncio.run(sch.run())
    cleans = sum(1 for m, _ in display.history if m == "deep_clean")
    assert cleans == 0


def test_polarity_history_capped_at_1000() -> None:
    """Long-running device must not grow polarity_history unboundedly."""
    cfg = Config(cycle=CycleConfig(quote_seconds=1, animation_seconds=1, invert_polarity_every=1))
    display = MockDisplay()
    sch = Scheduler(
        config=cfg, library=_make_lib(1), display=display,
        test_max_cycles=1100, _test_sleep_override=0.0,
    )
    asyncio.run(sch.run())
    assert len(sch.polarity_history) == 1000
    assert sch._cycle_count == 1100


def test_stop_cancels_in_flight_sleep() -> None:
    """SIGTERM must not wait up to quote_seconds for the loop to notice
    self._stop. The cancel path exits within milliseconds."""
    cfg = Config(cycle=CycleConfig(quote_seconds=600, animation_seconds=1))
    display = MockDisplay()
    sch = Scheduler(
        config=cfg, library=_make_lib(), display=display,
    )

    async def run_and_stop() -> None:
        task = asyncio.create_task(sch.run())
        # Yield once so the scheduler reaches its first sleep.
        await asyncio.sleep(0.1)
        sch.stop()
        await task

    # If stop() didn't cancel, this would block for 600 seconds.
    asyncio.run(asyncio.wait_for(run_and_stop(), timeout=5.0))
