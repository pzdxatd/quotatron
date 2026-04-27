"""JokeAPI v2 — categorized jokes with NSFW filtering."""
from __future__ import annotations
import httpx
from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource


class JokeApiSource(BaseSource):
    name = "jokeapi"
    base_url = "https://v2.jokeapi.dev/joke/Programming,Misc,Pun"
    kind = "joke"

    async def fetch(self, limit: int) -> list[ContentItem]:
        out: list[ContentItem] = []
        params = {
            "amount": min(limit, 10),  # API max amount is 10
            "blacklistFlags": "nsfw,religious,political,racist,sexist,explicit",
        }
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            r = await client.get(self.base_url, params=params)
            r.raise_for_status()
            data = r.json()
            if not isinstance(data, dict):
                return out
            jokes = data.get("jokes")
            # Single-joke responses have {type, joke/setup+delivery} at top level.
            if jokes is None and data.get("type") in ("single", "twopart"):
                jokes = [data]
            if not isinstance(jokes, list):
                return out
            for entry in jokes:
                if not isinstance(entry, dict):
                    continue
                if entry.get("type") == "twopart":
                    setup = (entry.get("setup") or "").strip()
                    delivery = (entry.get("delivery") or "").strip()
                    text = f"{setup}\n{delivery}".strip()
                else:
                    text = (entry.get("joke") or "").strip()
                if not text:
                    continue
                out.append(ContentItem(
                    kind="joke", text=text, author="anonymous",
                    category="oneliner", source=self.name,
                ))
        return out
