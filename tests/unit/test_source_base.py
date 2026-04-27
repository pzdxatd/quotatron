import pytest
from quotatron.sources._base import BaseSource, fetch_with_timeout
from quotatron.models import ContentItem


class _Dummy(BaseSource):
    name = "dummy"
    base_url = "https://example.invalid"
    kind = "quote"

    async def fetch(self, limit: int) -> list[ContentItem]:
        return [ContentItem(kind="quote", text="hi", author="me", category="philosophy", source="dummy")]


def test_dummy_source_returns_content_item() -> None:
    import asyncio
    items = asyncio.run(_Dummy().fetch(limit=1))
    assert len(items) == 1
    assert items[0].source == "dummy"
