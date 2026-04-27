"""Quotable.io — broad/general quotes, tagged."""
from __future__ import annotations
import httpx
from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource


class QuotableIoSource(BaseSource):
    name = "quotable_io"
    base_url = "https://api.quotable.io/quotes/random"
    kind = "quote"

    async def fetch(self, limit: int) -> list[ContentItem]:
        out: list[ContentItem] = []
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            r = await client.get(self.base_url, params={"limit": min(limit, 20)})
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, list):
                return out
            for entry in data[:limit]:
                text = (entry.get("content") or "").strip()
                author = (entry.get("author") or "anonymous").strip() or "anonymous"
                if not text:
                    continue
                out.append(ContentItem(
                    kind="quote", text=text, author=author,
                    category="philosophy", source=self.name,
                ))
        return out
