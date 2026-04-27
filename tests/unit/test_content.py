from collections import Counter
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


def test_picker_respects_quote_to_joke_ratio_in_aggregate() -> None:
    lib = make_lib()
    counts = Counter()
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


def test_no_repeat_window_avoids_recent_items() -> None:
    lib = make_lib()
    seen = []
    for _ in range(20):
        seen.append(lib.next_item(
            quote_to_joke_ratio=0.5,
            quote_weights={"philosophy": 1.0, "science": 1.0},
            joke_weights={"dad": 1.0, "oneliner": 1.0},
            no_repeat_window=2,
            seed=None,
        ).text)
    # No three consecutive identical
    for i in range(len(seen) - 2):
        assert not (seen[i] == seen[i+1] == seen[i+2])


def test_falls_back_when_window_excludes_all() -> None:
    # Two items, window of 5: must still return something.
    items = [
        ContentItem(kind="quote", text="x", author="a", category="philosophy", source="bundled"),
        ContentItem(kind="quote", text="y", author="a", category="philosophy", source="bundled"),
    ]
    lib = ContentLibrary(items=items)
    for _ in range(10):
        out = lib.next_item(
            quote_to_joke_ratio=1.0,
            quote_weights={"philosophy": 1.0},
            joke_weights={},
            no_repeat_window=5,
            seed=None,
        )
        assert out.text in {"x", "y"}
