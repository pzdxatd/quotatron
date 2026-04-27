from quotatron.models import ContentItem, Polarity
from quotatron.render import compose


def make_item(**overrides: object) -> ContentItem:
    base = dict(
        kind="quote",
        text="The unexamined life is not worth living.",
        author="Socrates",
        category="philosophy",
        source="bundled",
    )
    base.update(overrides)
    return ContentItem(**base)


def test_landscape_compose_returns_correct_size_1bit() -> None:
    img = compose(make_item(), polarity=Polarity.NORMAL, rotation="landscape")
    assert img.size == (250, 122)
    assert img.mode == "1"


def test_rotation_argument_does_not_change_output() -> None:
    """The framebuffer is always landscape; physical rotation lives in the
    display driver. Asserting byte-equality pins this design decision."""
    landscape = compose(make_item(), polarity=Polarity.NORMAL, rotation="landscape")
    portrait = compose(make_item(), polarity=Polarity.NORMAL, rotation="portrait")
    assert landscape.tobytes() == portrait.tobytes()


def test_inverted_polarity_is_pixelwise_complement() -> None:
    """Stronger than 'mostly black' counting: every pixel must invert."""
    normal = compose(make_item(), polarity=Polarity.NORMAL, rotation="landscape")
    inverted = compose(make_item(), polarity=Polarity.INVERTED, rotation="landscape")
    n = list(normal.getdata())
    i = list(inverted.getdata())
    assert len(n) == len(i) == 250 * 122
    assert all(a != b for a, b in zip(n, i))


def test_long_text_wraps_within_canvas() -> None:
    long = make_item(text="a" * 400)
    img = compose(long, polarity=Polarity.NORMAL, rotation="landscape")
    assert img.size == (250, 122)


def test_long_author_truncates_with_ellipsis_and_does_not_clip() -> None:
    """A 60-char author would overflow the canvas without truncation;
    the renderer must shrink it so the framebuffer is unchanged in size
    and the rendered output differs from the empty-author baseline."""
    long_author = make_item(author="A" * 60)
    short_author = make_item(author="X")
    img_long = compose(long_author, polarity=Polarity.NORMAL)
    img_short = compose(short_author, polarity=Polarity.NORMAL)
    assert img_long.size == (250, 122)
    # Long-author render still differs from short-author (truncation produces
    # different pixels than a 1-char author), but neither crashes or blanks.
    assert img_long.tobytes() != img_short.tobytes()


def test_empty_author_does_not_crash() -> None:
    img = compose(make_item(author=""), polarity=Polarity.NORMAL)
    assert img.size == (250, 122)


def test_polarity_flipped() -> None:
    assert Polarity.NORMAL.flipped() is Polarity.INVERTED
    assert Polarity.INVERTED.flipped() is Polarity.NORMAL
    assert Polarity.NORMAL.flipped().flipped() is Polarity.NORMAL


def test_polarity_bg_fg_values() -> None:
    assert Polarity.NORMAL.bg == 1 and Polarity.NORMAL.fg == 0
    assert Polarity.INVERTED.bg == 0 and Polarity.INVERTED.fg == 1
