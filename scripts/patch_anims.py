"""One-shot script to wrap module-level animation precomputes in disk_cached().

Each animation file has a pattern:
    from quotatron.animations._base import AnimationContext, BaseAnimation
    ...
    _<NAME> = _build_<thing>(...)

We:
  1. Add `from quotatron.animations._precompute import disk_cached` right
     after the _base import.
  2. Replace `_<NAME> = _build_<thing>(args)` with
     `_<NAME> = disk_cached("<file_stem>_<name_lower>_v1", lambda: _build_<thing>(args))`
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "src" / "quotatron" / "animations"

PATTERNS = {
    "block_jitter.py":            ("_BLOCK_THRESHOLDS",      "_build_block_thresholds()"),
    "conway_iterations.py":       ("_THRESHOLD_MAP",         "_build_threshold_map()"),
    "dendritic.py":               ("_RANK_MAP",              "_build_rank_map()"),
    "diffusion_dissolve.py":      ("_DIST_MAP_NP",           "_build_dist_map()"),
    "falling_pixels.py":          ("_RANK_MAP",              "_build_rank_map()"),
    "flood_fill.py":              ("_RANK_MAP_NP",           "_build_rank_map()"),
    "grid_stamp.py":              ("_THRESHOLDS",            "_build_thresholds()"),
    "hilbert_fill.py":            ("_RANK_MAP",              "_build_rank_map()"),
    "ink_bleed.py":               ("_BLEED_MAP",             "_build_bleed_map(250, 122)"),
    "line_shuffle.py":            ("_ROW_THRESHOLDS",        "_build_row_thresholds(122)"),
    "lissajous.py":               ("_RANK_MAP",              "_build_rank_map()"),
    "matrix_rain.py":             ("_PHASES",                "_build_column_phases()"),
    "perlin_fade.py":             ("_SMOOTH_NOISE",          "_build_smooth_noise()"),
    "pure_noise.py":              ("_NOISE",                 "_build_noise_field()"),
    "random_pixel_dissolve.py":   ("_RANK_MAP_NP",           "_build_rank_map()"),
    "ripple.py":                  ("_DIST_MAP",              "_build_dist_map()"),
    "scanline_tear.py":           ("_SCANLINE_THRESHOLDS",   "_build_scanline_thresholds()"),
    "snake_fill.py":              ("_RANK_MAP_NP",           "_build_rank_map()"),
    "spiral.py":                  ("_RANK_MAP",              "_build_rank_map()"),
}

IMPORT_LINE = "from quotatron.animations._precompute import disk_cached\n"
BASE_IMPORT_RE = re.compile(
    r"^from quotatron\.animations\._base import .*$",
    re.MULTILINE,
)


def patch(path: Path, var: str, expr: str) -> bool:
    text = path.read_text(encoding="utf-8")
    changed = False

    if "from quotatron.animations._precompute import disk_cached" not in text:
        match = BASE_IMPORT_RE.search(text)
        if not match:
            print(f"  ! {path.name}: no _base import found, skipping")
            return False
        insert_at = match.end()
        text = text[: insert_at] + "\n" + IMPORT_LINE.rstrip() + text[insert_at:]
        changed = True

    key = f"{path.stem}_{var.lower().lstrip('_')}_v1"
    old_line = f"{var} = {expr}"
    new_line = f"{var} = disk_cached({key!r}, lambda: {expr})"
    if old_line in text:
        text = text.replace(old_line, new_line)
        changed = True
    elif new_line in text:
        # already patched
        pass
    else:
        print(f"  ! {path.name}: assignment line not found ({old_line!r})")
        return False

    if changed:
        path.write_text(text, encoding="utf-8")
        print(f"  patched {path.name}")
    return changed


def main() -> None:
    for fname, (var, expr) in PATTERNS.items():
        patch(ROOT / fname, var, expr)


if __name__ == "__main__":
    main()
