"""Stoic Quotes API — Marcus Aurelius, Seneca, Epictetus."""
from __future__ import annotations
import httpx
from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource


class StoicQuotesSource(BaseSource):
    name = "stoic_quotes"
    base_url = "https://stoic-quotes.com/api/quotes"
    kind = "quote"

    async def fetch(self, limit: int) -> list[ContentItem]:
        out: list[ContentItem] = []
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            r = await client.get(self.base_url)
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, list):
                return out
            for entry in data[:limit]:
                text = (entry.get("text") or "").strip()
                author = (entry.get("author") or "anonymous").strip()
                if not text:
                    continue
                out.append(ContentItem(
                    kind="quote", text=text, author=author,
                    category="philosophy", source=self.name,
                ))
        return out
