"""Shared data models."""
from __future__ import annotations
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


class ContentItem(BaseModel):
    kind: Literal["quote", "joke"]
    text: str = Field(min_length=1, max_length=2000)
    author: str = "anonymous"
    category: str
    source: str = "bundled"


class Polarity(Enum):
    NORMAL = "normal"      # white bg, black text/fg
    INVERTED = "inverted"  # black bg, white text/fg

    def flipped(self) -> "Polarity":
        return Polarity.INVERTED if self is Polarity.NORMAL else Polarity.NORMAL

    @property
    def bg(self) -> int:
        return 1 if self is Polarity.NORMAL else 0

    @property
    def fg(self) -> int:
        return 0 if self is Polarity.NORMAL else 1
