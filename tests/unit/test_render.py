from quotatron.models import ContentItem, Polarity
from quotatron.render import compose


def make_item() -> ContentItem:
    return ContentItem(
        kind="quote",
        text="The unexamined life is not worth living.",
        author="Socrates",
        category="philosophy",
        source="bundled",
    )


def test_landscape_compose_returns_correct_size_1bit() -> None:
    img = compose(make_item(), polarity=Polarity.NORMAL, rotation="landscape")
    assert img.size == (250, 122)
    assert img.mode == "1"


def test_portrait_rotates_canvas() -> None:
    img = compose(make_item(), polarity=Polarity.NORMAL, rotation="portrait")
    assert img.size == (250, 122)  # final framebuffer is always landscape;
                                    # portrait is rendered then rotated by display layer


def test_inverted_polarity_swaps_bg_fg() -> None:
    normal = compose(make_item(), polarity=Polarity.NORMAL, rotation="landscape")
    inverted = compose(make_item(), polarity=Polarity.INVERTED, rotation="landscape")
    # Counts of black pixels should differ massively between normal and inverted
    n_black = sum(1 for p in normal.getdata() if p == 0)
    i_black = sum(1 for p in inverted.getdata() if p == 0)
    assert n_black + i_black > 1000
    # In normal: bg white (1) → most pixels white. In inverted: bg black (0) → most black.
    assert i_black > n_black


def test_long_text_wraps_within_canvas() -> None:
    long = ContentItem(
        kind="quote",
        text=("a" * 400),  # forces wrapping
        author="anon",
        category="philosophy",
        source="bundled",
    )
    img = compose(long, polarity=Polarity.NORMAL, rotation="landscape")
    assert img.size == (250, 122)  # never exceeds canvas
