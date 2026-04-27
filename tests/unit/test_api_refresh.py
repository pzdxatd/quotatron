import asyncio
import json
from pathlib import Path

import quotatron.api_refresh as api_refresh
from quotatron.api_refresh import refresh_once
from quotatron.config import SourceConfig
from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource


def test_refresh_once_handles_empty_source_list(tmp_path: Path) -> None:
    fetched = asyncio.run(refresh_once(sources=[], cache_dir=tmp_path))
    assert fetched == 0


class _FakeSource(BaseSource):
    name = "fake"
    base_url = "https://example.invalid"
    kind = "quote"

    async def fetch(self, limit: int) -> list[ContentItem]:
        return [
            ContentItem(
                kind="quote", text=f"q{i}", author="anon",
                category="philosophy", source=self.name,
            )
            for i in range(limit)
        ]


def test_refresh_once_writes_json_with_correct_shape(tmp_path: Path) -> None:
    api_refresh._load_source_classes(refresh=True)
    api_refresh._SOURCE_CLASSES["fake"] = _FakeSource
    try:
        sources = [SourceConfig(name="fake", kind="quote", target_categories=["philosophy"])]
        n = asyncio.run(refresh_once(sources=sources, cache_dir=tmp_path, per_source_limit=3))
        assert n == 3
        out = tmp_path / "fake.json"
        assert out.exists()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 3
        assert data[0]["text"] == "q0"
        assert data[0]["source"] == "fake"
        assert data[0]["category"] == "philosophy"
    finally:
        api_refresh._load_source_classes(refresh=True)


def test_refresh_once_caps_cache_at_500_entries(tmp_path: Path) -> None:
    api_refresh._load_source_classes(refresh=True)
    api_refresh._SOURCE_CLASSES["fake"] = _FakeSource
    try:
        out = tmp_path / "fake.json"
        seed = [
            ContentItem(
                kind="quote", text=f"old{i}", author="anon",
                category="philosophy", source="fake",
            ).model_dump()
            for i in range(600)
        ]
        out.write_text(json.dumps(seed), encoding="utf-8")

        sources = [SourceConfig(name="fake", kind="quote")]
        asyncio.run(refresh_once(sources=sources, cache_dir=tmp_path, per_source_limit=5))
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 500
        # Cap retains the tail — the 5 newly-added items end the file.
        assert data[-1]["text"] == "q4"
        assert data[-5]["text"] == "q0"
    finally:
        api_refresh._load_source_classes(refresh=True)


def test_load_source_classes_finds_eleven_real_sources() -> None:
    classes = api_refresh._load_source_classes(refresh=True)
    assert len(classes) == 11
    expected = {
        "quotable_io", "zenquotes", "type_fit", "stoic_quotes",
        "programming_quotes", "forismatic", "icanhazdadjoke", "jokeapi",
        "official_joke_api", "chuck_norris_io", "geek_jokes",
    }
    assert set(classes) == expected
