"""type.fit — large static collection of quotes (~1600). Sample N randomly."""
from __future__ import annotations
import random
import httpx
from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource


class TypeFitSource(BaseSource):
    name = "type_fit"
    base_url = "https://type.fit/api/quotes"
    kind = "quote"

    async def fetch(self, limit: int) -> list[ContentItem]:
        out: list[ContentItem] = []
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            r = await client.get(self.base_url)
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, list):
                return out
            picks = random.sample(data, min(limit, len(data))) if data else []
            for entry in picks:
                text = (entry.get("text") or "").strip()
                author = (entry.get("author") or "anonymous").strip() or "anonymous"
                if not text:
                    continue
                out.append(ContentItem(
                    kind="quote", text=text, author=author,
                    category="philosophy", source=self.name,
                ))
        return out
