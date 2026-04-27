"""Auto-discover BaseAnimation subclasses in this package directory.

User plugins live in animations/<name>.py. Any module starting with `_` is
skipped (treated as private/builtin).
"""
from __future__ import annotations
import importlib
import logging
import pkgutil
from pathlib import Path
from quotatron.animations._base import BaseAnimation
from quotatron.animations._builtin_simple_fade import SimpleFade

log = logging.getLogger(__name__)

_REGISTRY: dict[str, type[BaseAnimation]] = {}
_BUILTIN_FALLBACK: type[BaseAnimation] = SimpleFade


def _discover() -> None:
    pkg_path = Path(__file__).parent
    for info in pkgutil.iter_modules([str(pkg_path)]):
        if info.name.startswith("_"):
            continue
        # An import error in one plugin must not take down the whole
        # animations subsystem; the device should keep working with whatever
        # plugins did load (and fall back to simple_fade for the rest).
        try:
            mod = importlib.import_module(f"{__name__}.{info.name}")
        except Exception:
            log.exception("failed to import animation plugin %r — skipping", info.name)
            continue
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseAnimation)
                and obj is not BaseAnimation
            ):
                # Only register classes defined in the module itself, not
                # re-imports from sibling modules.
                if getattr(obj, "__module__", None) != mod.__name__:
                    continue
                if obj.name in _REGISTRY and _REGISTRY[obj.name] is not obj:
                    raise RuntimeError(
                        f"duplicate animation name '{obj.name}' "
                        f"in {_REGISTRY[obj.name].__module__} and {obj.__module__}"
                    )
                _REGISTRY[obj.name] = obj


def registry(refresh: bool = False) -> dict[str, type[BaseAnimation]]:
    if refresh or not _REGISTRY:
        _REGISTRY.clear()
        _discover()
    return dict(_REGISTRY)


def fallback() -> type[BaseAnimation]:
    return _BUILTIN_FALLBACK
