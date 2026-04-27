import json
from collections import Counter
from pathlib import Path

import pytest

from quotatron.content import ContentLibrary
from quotatron.models import ContentItem


def make_lib() -> ContentLibrary:
    items = [
        ContentItem(kind="quote", text="q1", author="a", category="philosophy", source="bundled"),
        ContentItem(kind="quote", text="q2", author="a", category="science", source="bundled"),
        ContentItem(kind="joke",  text="j1", author="a", category="dad", source="bundled"),
        ContentItem(kind="joke",  text="j2", author="a", category="oneliner", source="bundled"),
    ]
    return ContentLibrary(items=items)


def test_empty_items_raises() -> None:
    with pytest.raises(ValueError, match="at least one item"):
        ContentLibrary(items=[])


def test_picker_respects_quote_to_joke_ratio_in_aggregate() -> None:
    lib = make_lib()
    counts: Counter[str] = Counter()
    for _ in range(2000):
        item = lib.next_item(
            quote_to_joke_ratio=0.7,
            quote_weights={"philosophy": 1.0, "science": 1.0},
            joke_weights={"dad": 1.0, "oneliner": 1.0},
            no_repeat_window=0,
            seed=None,
        )
        counts[item.kind] += 1
    ratio = counts["quote"] / (counts["quote"] + counts["joke"])
    assert 0.65 < ratio < 0.75


def test_no_repeat_window_excludes_last_two_items() -> None:
    """With a 6-item pool and window=2, item[i] must not equal item[i-1] or
    item[i-2]. The previous version of this test only checked for triplets,
    which would have passed even if the dedup logic were deleted entirely."""
    items = [
        ContentItem(kind="quote", text=f"q{i}", author="a", category="philosophy", source="bundled")
        for i in range(6)
    ]
    lib = ContentLibrary(items=items)
    seen: list[str] = []
    for _ in range(50):
        seen.append(lib.next_item(
            quote_to_joke_ratio=1.0,
            quote_weights={"philosophy": 1.0},
            joke_weights={},
            no_repeat_window=2,
            seed=None,
        ).text)
    for i in range(2, len(seen)):
        assert seen[i] != seen[i - 1], f"window=2 violated at i={i}: {seen[i-2:i+1]}"
        assert seen[i] != seen[i - 2], f"window=2 violated at i={i}: {seen[i-2:i+1]}"


def test_falls_back_when_window_excludes_all_and_yields_diversity() -> None:
    items = [
        ContentItem(kind="quote", text="x", author="a", category="philosophy", source="bundled"),
        ContentItem(kind="quote", text="y", author="a", category="philosophy", source="bundled"),
    ]
    lib = ContentLibrary(items=items)
    seen: list[str] = []
    for _ in range(40):
        out = lib.next_item(
            quote_to_joke_ratio=1.0,
            quote_weights={"philosophy": 1.0},
            joke_weights={},
            no_repeat_window=5,
            seed=None,
        )
        assert out.text in {"x", "y"}
        seen.append(out.text)
    # Both items must show up in 40 draws (probability of either being absent
    # is essentially zero given the window=5 fallback to full pool).
    assert set(seen) == {"x", "y"}


def test_seeded_call_is_deterministic_for_a_single_draw() -> None:
    lib_a = make_lib()
    lib_b = make_lib()
    args = dict(
        quote_to_joke_ratio=0.7,
        quote_weights={"philosophy": 1.0, "science": 1.0},
        joke_weights={"dad": 1.0, "oneliner": 1.0},
        no_repeat_window=0,
        seed=42,
    )
    assert lib_a.next_item(**args).text == lib_b.next_item(**args).text


def test_from_disk_loads_bundled_corpus(tmp_path: Path) -> None:
    """from_disk reads quotes/ and jokes/ subdirs, normalizes ContentItem
    fields, and applies defaults for missing optional fields."""
    (tmp_path / "quotes").mkdir()
    (tmp_path / "jokes").mkdir()
    (tmp_path / "quotes" / "philosophy.json").write_text(
        json.dumps([
            {"text": "p1", "author": "Plato", "category": "philosophy"},
            {"text": "p2"},  # missing author + category — defaults expected
        ]),
        encoding="utf-8",
    )
    (tmp_path / "jokes" / "dad.json").write_text(
        json.dumps([
            {"text": "j1", "author": "anonymous", "category": "dad"},
        ]),
        encoding="utf-8",
    )
    lib = ContentLibrary.from_disk(tmp_path)
    assert len(lib.items) == 3
    by_text = {it.text: it for it in lib.items}
    assert by_text["p1"].kind == "quote"
    assert by_text["p1"].source == "bundled"
    # Defaults applied to p2:
    assert by_text["p2"].author == "anonymous"
    assert by_text["p2"].category == "philosophy"  # falls back to filename stem
    assert by_text["j1"].kind == "joke"
