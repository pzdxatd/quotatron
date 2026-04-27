import asyncio

import httpx
import pytest

from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource, fetch_with_timeout


class _Dummy(BaseSource):
    name = "dummy"
    base_url = "https://example.invalid"
    kind = "quote"

    async def fetch(self, limit: int) -> list[ContentItem]:
        return [ContentItem(kind="quote", text="hi", author="me", category="philosophy", source="dummy")]


def test_dummy_source_returns_content_item() -> None:
    items = asyncio.run(_Dummy().fetch(limit=1))
    assert len(items) == 1
    assert items[0].source == "dummy"


def test_subclass_without_required_attrs_raises_at_import() -> None:
    with pytest.raises(TypeError, match="must define 'base_url'"):
        class _NoUrl(BaseSource):
            name = "x"
            kind = "quote"

            async def fetch(self, limit: int) -> list[ContentItem]:
                return []


def test_fetch_with_timeout_returns_empty_on_timeout() -> None:
    class _Slow(BaseSource):
        name = "slow"
        base_url = "https://example.invalid"
        kind = "quote"

        async def fetch(self, limit: int) -> list[ContentItem]:
            await asyncio.sleep(10)
            return []

    items = asyncio.run(fetch_with_timeout(_Slow(), limit=1, timeout_s=0.05))
    assert items == []


def test_fetch_with_timeout_returns_empty_on_httpx_error() -> None:
    class _BadHttp(BaseSource):
        name = "bad_http"
        base_url = "https://example.invalid"
        kind = "quote"

        async def fetch(self, limit: int) -> list[ContentItem]:
            raise httpx.ConnectError("simulated", request=None)

    items = asyncio.run(fetch_with_timeout(_BadHttp(), limit=1, timeout_s=1.0))
    assert items == []


def test_fetch_with_timeout_returns_empty_on_value_error() -> None:
    class _BadJson(BaseSource):
        name = "bad_json"
        base_url = "https://example.invalid"
        kind = "quote"

        async def fetch(self, limit: int) -> list[ContentItem]:
            raise ValueError("simulated JSON decode error")

    items = asyncio.run(fetch_with_timeout(_BadJson(), limit=1, timeout_s=1.0))
    assert items == []


def test_fetch_with_timeout_passes_through_happy_path() -> None:
    items = asyncio.run(fetch_with_timeout(_Dummy(), limit=1, timeout_s=1.0))
    assert len(items) == 1
    assert items[0].source == "dummy"
