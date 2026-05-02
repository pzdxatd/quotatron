"""Disk-cached lazy precomputation for animation modules.

Many animations build a large per-pixel rank/threshold map at import time
(e.g. random walks, DLA, BFS). These can take minutes on the Pi Zero W,
which blocks the first call to the animation registry — and therefore
the first animation cycle after every restart.

``disk_cached(key, builder)`` runs ``builder()`` once and pickles the
result under ``QUOTATRON_PRECOMPUTE_DIR`` (default
``~/.cache/quotatron/precomputed``). Subsequent loads are near-instant.
The cache is keyed on ``key`` only — bump the key string when changing
the builder semantics so old caches are not silently reused.
"""
from __future__ import annotations

import logging
import os
import pickle
from pathlib import Path
from typing import Any, Callable, TypeVar

log = logging.getLogger(__name__)

_T = TypeVar("_T")


def _cache_dir() -> Path:
    override = os.environ.get("QUOTATRON_PRECOMPUTE_DIR")
    if override:
        return Path(override)
    return Path.home() / ".cache" / "quotatron" / "precomputed"


def disk_cached(key: str, builder: Callable[[], _T]) -> _T:
    """Compute ``builder()`` once and persist the result keyed on ``key``."""
    cache_path = _cache_dir() / f"{key}.pkl"
    if cache_path.exists():
        try:
            with cache_path.open("rb") as fh:
                return pickle.load(fh)
        except Exception:
            log.warning(
                "precompute cache %s unreadable — recomputing", cache_path,
                exc_info=True,
            )
    result = builder()
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache_path.with_suffix(".pkl.tmp")
        with tmp.open("wb") as fh:
            pickle.dump(result, fh, protocol=pickle.HIGHEST_PROTOCOL)
        tmp.replace(cache_path)
    except Exception:
        # Cache writes are best-effort; never fail the import path.
        log.warning("could not write precompute cache %s", cache_path, exc_info=True)
    return result
