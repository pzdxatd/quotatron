from PIL import Image
from quotatron.display.mock import MockDisplay


def test_mock_records_images_with_mode_tags() -> None:
    d = MockDisplay(width=250, height=122)
    img = Image.new("1", (250, 122), 1)
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
    import pytest
    with pytest.raises(ValueError):
        d.display_full(img)
