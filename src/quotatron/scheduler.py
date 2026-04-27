"""Asyncio main loop orchestrating content selection, rendering, and display.

The :class:`Scheduler` is the central runtime: it picks a :class:`ContentItem`,
composes a frame, optionally runs an animation transition, sleeps for the
configured cycle duration, and repeats. Polarity bounces every
``invert_polarity_every`` cycles. A daily deep-clean fires at 03:00 local time.

The ``_test_sleep_override`` parameter is a test affordance — set it to
``0.0`` to bypass the configured ``quote_seconds`` sleep so unit tests run
quickly without waiting on real wall-clock time. Production passes
``None`` (the default) and pays the full configured sleep.
"""
from __future__ import annotations

import asyncio
import logging
import random
import signal
from datetime import date, datetime
from typing import Optional

from PIL.Image import Image as PILImage

from quotatron.animations import fallback as fallback_animation
from quotatron.animations import registry as animation_registry
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.config import Config
from quotatron.content import ContentLibrary
from quotatron.display._interface import Display
from quotatron.models import Polarity
from quotatron.render import compose

log = logging.getLogger(__name__)


class Scheduler:
    """Asyncio main loop wiring content -> render -> animation -> display."""

    def __init__(
        self,
        config: Config,
        library: ContentLibrary,
        display: Display,
        test_max_cycles: Optional[int] = None,
        _test_sleep_override: Optional[float] = None,
    ) -> None:
        self.config = config
        self.library = library
        self.display = display
        self._stop = False
        self._test_max_cycles = test_max_cycles
        self._test_sleep_override = _test_sleep_override
        self.polarity_history: list[str] = []
        self._last_deep_clean_date: date | None = None
        self._deep_clean_hour = 3

    async def run(self) -> None:
        polarity = Polarity.NORMAL
        cycle = 0
        prev_image: PILImage | None = None
        while not self._stop:
            item = self.library.next_item(
                quote_to_joke_ratio=self.config.content.quote_to_joke_ratio,
                quote_weights=self.config.content.weights.quotes,
                joke_weights=self.config.content.weights.jokes,
                no_repeat_window=self.config.content.no_repeat_window,
                seed=None,
            )
            dest = compose(item, polarity=polarity, rotation=self.config.display.rotation)
            log.info(
                "cycle=%d item=%s/%s author=%r polarity=%s",
                cycle,
                item.kind,
                item.category,
                item.author,
                polarity.value,
            )

            if prev_image is not None and self.config.animations.enabled:
                anim = self._pick_animation()
                ctx = AnimationContext(
                    from_image=prev_image,
                    to_image=dest,
                    polarity=polarity,
                    width=self.display.width,
                    height=self.display.height,
                )
                self.display.enter_partial_mode()
                try:
                    for frame in anim.frames(ctx, self.config.cycle.animation_seconds):
                        self.display.display_partial(frame)
                        # Yield so signal handlers and the API refresh task run.
                        await asyncio.sleep(0)
                except Exception:
                    log.exception("animation %s raised — using fallback", anim.name)
                self.display.exit_partial_mode()
                self.display.display_full(dest)
            else:
                self.display.display_full(dest)

            sleep_s = (
                self._test_sleep_override
                if self._test_sleep_override is not None
                else self.config.cycle.quote_seconds
            )
            await asyncio.sleep(sleep_s)

            # Daily deep-clean check.
            now = datetime.now()
            if (
                now.hour == self._deep_clean_hour
                and self._last_deep_clean_date != now.date()
            ):
                log.info("running daily deep-clean")
                self.display.deep_clean()
                self._last_deep_clean_date = now.date()

            cycle += 1
            self.polarity_history.append(polarity.value)
            if cycle % self.config.cycle.invert_polarity_every == 0:
                polarity = polarity.flipped()
            prev_image = dest

            if self._test_max_cycles is not None and cycle >= self._test_max_cycles:
                self._stop = True

    def _pick_animation(self) -> BaseAnimation:
        reg = animation_registry()
        names = [n for n in reg if n not in self.config.animations.blocklist]
        if not names:
            return fallback_animation()()
        if self.config.animations.shuffle == "random":
            return reg[random.choice(names)]()
        return reg[sorted(names)[len(self.polarity_history) % len(names)]]()

    def stop(self) -> None:
        self._stop = True


def run_service() -> int:
    """systemd entry point. Loads config, library, hardware display, and runs forever.

    Note: ``loop.add_signal_handler`` is not available on Windows asyncio loops
    and will raise ``NotImplementedError``. This entry point is only invoked on
    the Pi in production; tests construct :class:`Scheduler` directly and never
    pass through here.
    """
    from quotatron.config import load_config
    from quotatron.content import ContentLibrary
    from quotatron.display.epaper import WaveshareDisplay
    from quotatron.emergency_quotes import emergency_library
    from quotatron.models import ContentItem
    from quotatron.render import compose

    cfg = load_config("config/quotatron.yaml")
    logging.basicConfig(
        level=cfg.logging.level,
        filename=cfg.logging.path,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        lib = ContentLibrary.from_disk("content")
    except Exception:
        log.exception("content library failed to load — using emergency quotes")
        lib = emergency_library()
    display = WaveshareDisplay(driver=cfg.display.driver)
    sch = Scheduler(config=cfg, library=lib, display=display)
    loop = asyncio.new_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, sch.stop)
    try:
        loop.run_until_complete(sch.run())
    finally:
        farewell = compose(
            ContentItem(
                kind="quote",
                text="Quotatron offline.",
                author="-",
                category="philosophy",
                source="system",
            ),
            polarity=Polarity.NORMAL,
            rotation=cfg.display.rotation,
        )
        display.shutdown(farewell)
    return 0
