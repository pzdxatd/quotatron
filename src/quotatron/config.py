"""Pydantic config models and YAML loader for Quotatron."""
from __future__ import annotations
from pathlib import Path
from typing import Literal
import yaml
from pydantic import BaseModel, Field, ConfigDict


class DisplayConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rotation: Literal["landscape", "portrait"] = "landscape"
    driver: Literal[
        "waveshare_2in13_v2",
        "waveshare_2in13_v3",
        "waveshare_2in13_v4",
        "dfrobot_2in13",
    ] = "waveshare_2in13_v3"
    full_refresh_every: int = Field(1, ge=1)


class CycleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quote_seconds: int = Field(50, ge=1, le=600)
    animation_seconds: int = Field(10, ge=1, le=600)
    invert_polarity_every: int = Field(1, ge=1)


class ContentWeightSection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quotes: dict[str, float] = Field(default_factory=dict)
    jokes: dict[str, float] = Field(default_factory=dict)


class ContentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quote_to_joke_ratio: float = Field(0.7, ge=0.0, le=1.0)
    no_repeat_window: int = Field(200, ge=0)
    weights: ContentWeightSection = Field(default_factory=ContentWeightSection)


class SourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    kind: Literal["quote", "joke"]
    target_categories: list[str] = Field(default_factory=list)
    options: dict = Field(default_factory=dict)


class ApiRefreshConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    interval_minutes: int = Field(60, ge=1)
    fail_silently: bool = True
    per_source_timeout_seconds: float = Field(5.0, ge=0.5)
    max_items_per_refresh: int = Field(50, ge=1)
    sources: list[SourceConfig] = Field(default_factory=list)


class AnimationsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = True
    shuffle: Literal["random", "sequential"] = "random"
    blocklist: list[str] = Field(default_factory=list)
    per_animation_overrides: dict[str, dict] = Field(default_factory=dict)


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    path: str = "/var/log/quotatron.log"


class WebPreviewConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled_in_dev: bool = True
    host: str = "127.0.0.1"
    port: int = Field(8080, ge=1, le=65535)


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display: DisplayConfig = Field(default_factory=DisplayConfig)
    cycle: CycleConfig = Field(default_factory=CycleConfig)
    content: ContentConfig = Field(default_factory=ContentConfig)
    api_refresh: ApiRefreshConfig = Field(default_factory=ApiRefreshConfig)
    animations: AnimationsConfig = Field(default_factory=AnimationsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    web_preview: WebPreviewConfig = Field(default_factory=WebPreviewConfig)


def load_config(path: str | Path) -> Config:
    with open(path) as f:
        raw = yaml.safe_load(f) or {}
    return Config.model_validate(raw)
