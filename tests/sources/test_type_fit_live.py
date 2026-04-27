import pytest
from quotatron.sources.type_fit import TypeFitSource


@pytest.mark.live
@pytest.mark.asyncio
async def test_type_fit_returns_at_least_one_item() -> None:
    items = await TypeFitSource().fetch(limit=3)
    # NOTE: rate-limited or down sources may return empty; that's an
    # operational concern handled by `make verify-sources`. This test only
    # asserts that IF items come back, they're well-formed.
    for it in items:
        assert 1 <= len(it.text) <= 800
        assert it.source == "type_fit"
        assert "<" not in it.text  # no HTML leakage
