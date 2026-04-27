"""Geek-Jokes API — programming/geek humor (one per request)."""
from __future__ import annotations
import asyncio
import httpx
from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource


class GeekJokesSource(BaseSource):
    name = "geek_jokes"
    base_url = "https://geek-jokes.sameerkumar.website/api"
    kind = "joke"

    async def fetch(self, limit: int) -> list[ContentItem]:
        out: list[ContentItem] = []
        params = {"format": "json"}
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            for i in range(limit):
                try:
                    r = await client.get(self.base_url, params=params)
                    r.raise_for_status()
                    data = r.json()
                except httpx.HTTPError:
                    break
                if not isinstance(data, dict):
                    break
                text = (data.get("joke") or data.get("value") or "").strip()
                if text:
                    out.append(ContentItem(
                        kind="joke", text=text, author="anonymous",
                        category="programming", source=self.name,
                    ))
                if i < limit - 1:
                    await asyncio.sleep(0.05)
        return out
