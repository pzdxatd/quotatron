"""icanhazdadjoke — dad jokes (one per request)."""
from __future__ import annotations
import asyncio
import httpx
from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource


class IcanhazdadjokeSource(BaseSource):
    name = "icanhazdadjoke"
    base_url = "https://icanhazdadjoke.com/"
    kind = "joke"

    async def fetch(self, limit: int) -> list[ContentItem]:
        out: list[ContentItem] = []
        headers = {"Accept": "application/json", "User-Agent": "Quotatron/0.1"}
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True, headers=headers) as client:
            for i in range(limit):
                try:
                    r = await client.get(self.base_url)
                    r.raise_for_status()
                    data = r.json()
                except httpx.HTTPError:
                    break
                if not isinstance(data, dict):
                    break
                text = (data.get("joke") or "").strip()
                if text:
                    out.append(ContentItem(
                        kind="joke", text=text, author="anonymous",
                        category="dad", source=self.name,
                    ))
                if i < limit - 1:
                    await asyncio.sleep(0.05)
        return out
