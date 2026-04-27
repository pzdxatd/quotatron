"""ZenQuotes — inspirational/philosophical quotes. Rate-limited (429 → empty)."""
from __future__ import annotations
import httpx
from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource


class ZenQuotesSource(BaseSource):
    name = "zenquotes"
    base_url = "https://zenquotes.io/api/quotes/"
    kind = "quote"

    async def fetch(self, limit: int) -> list[ContentItem]:
        out: list[ContentItem] = []
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            try:
                r = await client.get(self.base_url)
            except httpx.HTTPError:
                return out
            if r.status_code == 429:
                return out  # rate-limited; caller will retry next cycle
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, list):
                return out
            for entry in data[:limit]:
                text = (entry.get("q") or "").strip()
                author = (entry.get("a") or "anonymous").strip() or "anonymous"
                if not text:
                    continue
                out.append(ContentItem(
                    kind="quote", text=text, author=author,
                    category="philosophy", source=self.name,
                ))
        return out
