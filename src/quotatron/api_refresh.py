"""Background API enrichment task."""
from __future__ import annotations
import asyncio
import json
import logging
import sys
from pathlib import Path
from quotatron.config import SourceConfig, load_config
from quotatron.sources._base import BaseSource, fetch_with_timeout

log = logging.getLogger(__name__)


_SOURCE_CLASSES: dict[str, type[BaseSource]] = {}


def _load_source_classes() -> dict[str, type[BaseSource]]:
    if _SOURCE_CLASSES:
        return _SOURCE_CLASSES
    import importlib, pkgutil
    import quotatron.sources as pkg
    for info in pkgutil.iter_modules(pkg.__path__):
        if info.name.startswith("_"):
            continue
        try:
            mod = importlib.import_module(f"quotatron.sources.{info.name}")
        except Exception:
            log.exception("failed to import source %r — skipping", info.name)
            continue
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if isinstance(obj, type) and issubclass(obj, BaseSource) and obj is not BaseSource:
                if getattr(obj, "__module__", None) != mod.__name__:
                    continue
                _SOURCE_CLASSES[obj.name] = obj
    return _SOURCE_CLASSES


async def refresh_once(
    sources: list[SourceConfig],
    cache_dir: str | Path,
    timeout_s: float = 5.0,
    per_source_limit: int = 5,
) -> int:
    classes = _load_source_classes()
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    total = 0
    for sc in sources:
        cls = classes.get(sc.name)
        if cls is None:
            log.warning("unknown source %s — skipping", sc.name)
            continue
        items = await fetch_with_timeout(cls(), per_source_limit, timeout_s)
        if not items:
            log.warning("source %s returned no items", sc.name)
            continue
        out_file = cache_dir / f"{sc.name}.json"
        existing = json.loads(out_file.read_text(encoding="utf-8")) if out_file.exists() else []
        existing.extend(it.model_dump() for it in items)
        # Cap cache size to 500 per source.
        existing = existing[-500:]
        out_file.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        total += len(items)
    return total


async def refresh_loop(
    sources: list[SourceConfig], cache_dir: str | Path, interval_minutes: int
) -> None:
    while True:
        try:
            n = await refresh_once(sources=sources, cache_dir=cache_dir)
            log.info("api_refresh: %d new items", n)
        except Exception:
            log.exception("api_refresh failed (silenced)")
        await asyncio.sleep(interval_minutes * 60)


def verify_all_sources() -> int:
    """`quotatron verify-sources` CLI entry point. Returns 0 if all sources reachable.

    Behavior:
    - Iterates the configured sources, fetches limit=3 from each.
    - Prints a one-line PASS/EMPTY/FAIL per source plus a summary.
    - Exits 0 unless --strict is passed AND any source failed.
    """
    cfg = load_config("config/quotatron.yaml")
    classes = _load_source_classes()
    print(f"Verifying {len(cfg.api_refresh.sources)} sources...")
    ok = 0
    fail = 0
    for sc in cfg.api_refresh.sources:
        cls = classes.get(sc.name)
        if cls is None:
            print(f"  ✗ {sc.name}: unknown")
            fail += 1
            continue
        try:
            items = asyncio.run(fetch_with_timeout(cls(), 3, 5.0))
            if items:
                print(f"  ✓ {sc.name}: {len(items)} items")
                ok += 1
            else:
                print(f"  ⚠ {sc.name}: empty (rate-limited or down)")
        except Exception as e:
            print(f"  ✗ {sc.name}: {type(e).__name__}: {e}")
            fail += 1
    print(f"{ok}/{len(cfg.api_refresh.sources)} sources healthy")
    return 1 if fail and "--strict" in sys.argv else 0
