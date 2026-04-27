"""Content library: bundled JSON loading + weighted picker."""
from __future__ import annotations
import json
import random
from collections import deque
from pathlib import Path
from quotatron.models import ContentItem


class ContentLibrary:
    def __init__(self, items: list[ContentItem]) -> None:
        if not items:
            raise ValueError("ContentLibrary requires at least one item")
        self.items = items
        self._recent: deque[str] = deque(maxlen=1000)

    @classmethod
    def from_disk(cls, root: str | Path) -> "ContentLibrary":
        root = Path(root)
        items: list[ContentItem] = []
        for kind_dir, kind in (("quotes", "quote"), ("jokes", "joke")):
            for f in (root / kind_dir).glob("*.json"):
                category = f.stem
                for raw in json.loads(f.read_text(encoding="utf-8")):
                    items.append(ContentItem(
                        kind=kind,
                        text=raw["text"],
                        author=raw.get("author", "anonymous"),
                        category=raw.get("category", category),
                        source=raw.get("source", "bundled"),
                    ))
        return cls(items=items)

    def next_item(
        self,
        *,
        quote_to_joke_ratio: float,
        quote_weights: dict[str, float],
        joke_weights: dict[str, float],
        no_repeat_window: int,
        seed: int | None = None,
    ) -> ContentItem:
        """Pick the next item.

        ``quote_to_joke_ratio`` endpoints: ``1.0`` always picks a quote,
        ``0.0`` always picks a joke. Each call constructs a fresh RNG, so
        ``seed`` makes a single draw deterministic but does NOT produce a
        deterministic stream — pass ``seed=None`` (the default) for normal
        production use.

        Not thread-safe: ``self._recent`` mutates without locking. Intended
        for single-event-loop use by the scheduler.
        """
        rng = random.Random(seed)
        kind = "quote" if rng.random() < quote_to_joke_ratio else "joke"
        weights = quote_weights if kind == "quote" else joke_weights
        pool = [it for it in self.items if it.kind == kind and it.category in weights]
        if not pool:
            # Fallback: any item of this kind, then any item at all.
            pool = [it for it in self.items if it.kind == kind] or list(self.items)

        # Build weighted list, excluding recent items (best-effort).
        window = list(self._recent)[-no_repeat_window:] if no_repeat_window else []
        eligible = [it for it in pool if it.text not in window]
        if not eligible:
            eligible = pool

        weighted = [(it, weights.get(it.category, 0.0) or 1.0) for it in eligible]
        choice = rng.choices(
            [it for it, _ in weighted],
            weights=[w for _, w in weighted],
            k=1,
        )[0]
        self._recent.append(choice.text)
        return choice
