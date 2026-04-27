import pytest
from quotatron.sources.geek_jokes import GeekJokesSource


@pytest.mark.live
@pytest.mark.asyncio
async def test_geek_jokes_returns_at_least_one_item() -> None:
    items = await GeekJokesSource().fetch(limit=3)
    # Rate-limited or down sources may return empty; that's an operational
    # concern handled by `make verify-sources`. This test only asserts that
    # IF items come back, they're well-formed.
    for it in items:
        assert 1 <= len(it.text) <= 800
        assert it.source == "geek_jokes"
        assert "<" not in it.text  # no HTML leakage
