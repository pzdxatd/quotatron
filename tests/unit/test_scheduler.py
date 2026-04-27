"""Unit tests for the asyncio scheduler main loop."""
from __future__ import annotations

import asyncio

from quotatron.config import Config, CycleConfig
from quotatron.content import ContentLibrary
from quotatron.display.mock import MockDisplay
from quotatron.models import ContentItem
from quotatron.scheduler import Scheduler


def test_scheduler_runs_one_full_cycle_in_test_mode() -> None:
    items = [
        ContentItem(
            kind="quote",
            text=f"q{i}",
            author="a",
            category="philosophy",
            source="bundled",
        )
        for i in range(5)
    ]
    lib = ContentLibrary(items=items)
    cfg = Config(cycle=CycleConfig(quote_seconds=1, animation_seconds=1))
    display = MockDisplay()
    sch = Scheduler(
        config=cfg,
        library=lib,
        display=display,
        test_max_cycles=2,
        _test_sleep_override=0.0,
    )
    asyncio.run(sch.run())
    fulls = sum(1 for m, _ in display.history if m == "full")
    assert fulls >= 2


def test_scheduler_flips_polarity_each_cycle() -> None:
    items = [
        ContentItem(
            kind="quote",
            text="q",
            author="a",
            category="philosophy",
            source="bundled",
        )
    ]
    cfg = Config(
        cycle=CycleConfig(quote_seconds=1, animation_seconds=1, invert_polarity_every=1)
    )
    display = MockDisplay()
    sch = Scheduler(
        config=cfg,
        library=ContentLibrary(items=items),
        display=display,
        test_max_cycles=4,
        _test_sleep_override=0.0,
    )
    asyncio.run(sch.run())
    assert sch.polarity_history == ["normal", "inverted", "normal", "inverted"]
