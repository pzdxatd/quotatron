"""Programming-quotes API — programmer aphorisms. Maps to category=science."""
from __future__ import annotations
import httpx
from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource


class ProgrammingQuotesSource(BaseSource):
    name = "programming_quotes"
    base_url = "https://programming-quotes-api.herokuapp.com/Quotes/random/quotes"
    kind = "quote"

    async def fetch(self, limit: int) -> list[ContentItem]:
        out: list[ContentItem] = []
        url = f"{self.base_url}/{limit}"
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, list):
                return out
            for entry in data[:limit]:
                text = (entry.get("en") or entry.get("text") or "").strip()
                author = (entry.get("author") or "anonymous").strip()
                if not text:
                    continue
                out.append(ContentItem(
                    kind="quote", text=text, author=author,
                    category="science", source=self.name,
                ))
        return out
