"""Auto-discover BaseAnimation subclasses in this package directory.

User plugins live in animations/<name>.py. Any module starting with `_` is
skipped (treated as private/builtin).
"""
from __future__ import annotations
import importlib
import pkgutil
from pathlib import Path
from quotatron.animations._base import BaseAnimation
from quotatron.animations._builtin_simple_fade import SimpleFade

_REGISTRY: dict[str, type[BaseAnimation]] = {}
_BUILTIN_FALLBACK: type[BaseAnimation] = SimpleFade


def _discover() -> None:
    pkg_path = Path(__file__).parent
    for info in pkgutil.iter_modules([str(pkg_path)]):
        if info.name.startswith("_"):
            continue
        mod = importlib.import_module(f"{__name__}.{info.name}")
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseAnimation)
                and obj is not BaseAnimation
            ):
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
