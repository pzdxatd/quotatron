import pytest

from quotatron.emergency_quotes import EMERGENCY, emergency_library
from quotatron.models import ContentItem


def test_emergency_list_size() -> None:
    assert len(EMERGENCY) == 30


@pytest.mark.parametrize("item", EMERGENCY, ids=lambda i: i.text[:30])
def test_emergency_items_are_valid(item: ContentItem) -> None:
    assert item.kind == "quote"
    assert item.source == "emergency"
    assert item.category == "philosophy"
    assert 1 <= len(item.text) <= 800


def test_emergency_library_loads() -> None:
    lib = emergency_library()
    assert len(lib.items) == 30
