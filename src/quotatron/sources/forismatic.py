"""Forismatic API — random quotes, one per request."""
from __future__ import annotations
import asyncio
import httpx
from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource


class ForismaticSource(BaseSource):
    name = "forismatic"
    base_url = "http://api.forismatic.com/api/1.0/"
    kind = "quote"

    async def fetch(self, limit: int) -> list[ContentItem]:
        out: list[ContentItem] = []
        params = {"method": "getQuote", "format": "json", "lang": "en"}
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            for i in range(limit):
                try:
                    r = await client.get(self.base_url, params=params)
                    r.raise_for_status()
                    data = r.json()
                except httpx.HTTPError:
                    break  # one failure ends the batch — don't pile on
                text = (data.get("quoteText") or "").strip()
                author = (data.get("quoteAuthor") or "anonymous").strip() or "anonymous"
                if text:
                    out.append(ContentItem(
                        kind="quote", text=text, author=author,
                        category="philosophy", source=self.name,
                    ))
                if i < limit - 1:
                    await asyncio.sleep(0.05)
        return out
