"""official-joke-api — generic Q&A jokes."""
from __future__ import annotations
import httpx
from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource


class OfficialJokeApiSource(BaseSource):
    name = "official_joke_api"
    base_url = "https://official-joke-api.appspot.com/jokes/random"
    kind = "joke"

    async def fetch(self, limit: int) -> list[ContentItem]:
        out: list[ContentItem] = []
        url = f"{self.base_url}/{int(limit)}"
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, list):
                return out
            for entry in data[:limit]:
                if not isinstance(entry, dict):
                    continue
                setup = (entry.get("setup") or "").strip()
                punchline = (entry.get("punchline") or "").strip()
                text = f"{setup}\n{punchline}".strip()
                if not text:
                    continue
                out.append(ContentItem(
                    kind="joke", text=text, author="anonymous",
                    category="oneliner", source=self.name,
                ))
        return out
