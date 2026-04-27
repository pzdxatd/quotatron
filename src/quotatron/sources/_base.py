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

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Mirror BaseAnimation's pattern: catch missing class attributes at
        # import time, before fetch_with_timeout sees an AttributeError.
        for attr in ("name", "base_url", "kind"):
            if not isinstance(getattr(cls, attr, None), str):
                raise TypeError(
                    f"{cls.__module__}.{cls.__qualname__} must define {attr!r} as a class attribute"
                )

    @abstractmethod
    async def fetch(self, limit: int) -> list[ContentItem]: ...


async def fetch_with_timeout(
    source: BaseSource, limit: int, timeout_s: float
) -> list[ContentItem]:
    try:
        return await asyncio.wait_for(source.fetch(limit), timeout=timeout_s)
    except (asyncio.TimeoutError, httpx.HTTPError, ValueError, KeyError):
        return []  # caller decides whether to log
