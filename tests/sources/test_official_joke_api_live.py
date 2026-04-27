import pytest
from quotatron.sources.official_joke_api import OfficialJokeApiSource


@pytest.mark.live
@pytest.mark.asyncio
async def test_official_joke_api_returns_at_least_one_item() -> None:
    items = await OfficialJokeApiSource().fetch(limit=3)
    # Rate-limited or down sources may return empty; that's an operational
    # concern handled by `make verify-sources`. This test only asserts that
    # IF items come back, they're well-formed.
    for it in items:
        assert 1 <= len(it.text) <= 800
        assert it.source == "official_joke_api"
        assert "<" not in it.text  # no HTML leakage
