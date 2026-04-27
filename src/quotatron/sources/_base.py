"""Base class for API source adapters."""
from __future__ import annotations
import asyncio
from abc import ABC, abstractmethod
from typing import Literal
import httpx
from quotatron.models import ContentItem


class BaseSource(ABC):
    name: str
    base_url: str
    kind: Literal["quote", "joke"]

    @abstractmethod
    async def fetch(self, limit: int) -> list[ContentItem]: ...


async def fetch_with_timeout(
    source: BaseSource, limit: int, timeout_s: float
) -> list[ContentItem]:
    try:
        return await asyncio.wait_for(source.fetch(limit), timeout=timeout_s)
    except (asyncio.TimeoutError, httpx.HTTPError, ValueError, KeyError) as e:
        return []  # caller decides whether to log
