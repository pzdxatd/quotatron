"""api.chucknorris.io — Chuck Norris one-liners (one per request)."""
from __future__ import annotations
import asyncio
import httpx
from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource


class ChuckNorrisIoSource(BaseSource):
    name = "chuck_norris_io"
    base_url = "https://api.chucknorris.io/jokes/random"
    kind = "joke"

    async def fetch(self, limit: int) -> list[ContentItem]:
        out: list[ContentItem] = []
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            for i in range(limit):
                try:
                    r = await client.get(self.base_url)
                    r.raise_for_status()
                    data = r.json()
                except httpx.HTTPError:
                    break
                if not isinstance(data, dict):
                    break
                text = (data.get("value") or "").strip()
                if text:
                    out.append(ContentItem(
                        kind="joke", text=text, author="Chuck Norris",
                        category="oneliner", source=self.name,
                    ))
                if i < limit - 1:
                    await asyncio.sleep(0.05)
        return out
