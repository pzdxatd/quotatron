import asyncio
from quotatron.api_refresh import refresh_once


def test_refresh_once_handles_empty_source_list() -> None:
    fetched = asyncio.run(refresh_once(sources=[], cache_dir="/tmp/quotatron-test-refresh"))
    assert fetched == 0
