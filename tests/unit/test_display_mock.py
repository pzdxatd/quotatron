import pytest
from PIL import Image
from quotatron.display import Display, MockDisplay


def _img(d: MockDisplay) -> Image.Image:
    return Image.new("1", (d.width, d.height), 1)


def test_mock_records_images_with_mode_tags() -> None:
    d = MockDisplay(width=250, height=122)
    img = _img(d)
    d.display_full(img)
    d.enter_partial_mode()
    d.display_partial(img)
    d.display_partial(img)
    d.exit_partial_mode()
    d.display_full(img)
    assert [m for m, _ in d.history] == [
        "full", "enter_partial", "partial", "partial", "exit_partial", "full"
    ]
    assert d.current_image() is not None


def test_mock_rejects_wrong_size() -> None:
    d = MockDisplay(width=250, height=122)
    img = Image.new("1", (200, 122), 1)
    with pytest.raises(ValueError):
        d.display_full(img)


def test_display_partial_before_enter_partial_mode_raises() -> None:
    d = MockDisplay()
    with pytest.raises(RuntimeError, match="enter_partial_mode"):
        d.display_partial(_img(d))


def test_exit_partial_mode_actually_exits() -> None:
    d = MockDisplay()
    d.enter_partial_mode()
    d.display_partial(_img(d))  # OK
    d.exit_partial_mode()
    with pytest.raises(RuntimeError):
        d.display_partial(_img(d))


def test_current_image_returns_most_recent_and_isolates_caller() -> None:
    d = MockDisplay()
    img1 = _img(d)
    d.display_full(img1)
    out = d.current_image()
    assert out is not None
    # Mutating the returned copy must not affect what the mock holds.
    out.putpixel((0, 0), 0)
    assert d.current_image().getpixel((0, 0)) == 1


def test_shutdown_with_farewell_records_both_full_and_shutdown_with_image() -> None:
    d = MockDisplay()
    img = _img(d)
    d.shutdown(img)
    modes = [m for m, _ in d.history]
    assert modes == ["full", "shutdown"]
    last_mode, last_img = d.history[-1]
    assert last_mode == "shutdown"
    assert last_img is not None
    assert last_img.size == (d.width, d.height)


def test_shutdown_without_farewell_records_only_shutdown_none() -> None:
    d = MockDisplay()
    d.shutdown()
    assert d.history == [("shutdown", None)]


def test_deep_clean_records_event() -> None:
    d = MockDisplay()
    d.deep_clean()
    assert d.history == [("deep_clean", None)]


def test_mock_satisfies_display_protocol() -> None:
    # Static type-check; if MockDisplay drifts from Display, this assignment
    # will type-error in pyright/mypy and the runtime test still passes.
    d: Display = MockDisplay()
    assert d.width == 250 and d.height == 122
