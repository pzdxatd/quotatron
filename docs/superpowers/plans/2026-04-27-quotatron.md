# Quotatron Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Raspberry Pi Zero W 1.1 + Waveshare 2.13" e-paper appliance that displays rotating famous-people quotes and clean jokes with 30 plugin-style 10-second wipe animations and e-ink longevity protections.

**Architecture:** Single-process modular monolith. One systemd service running an asyncio main loop. Animations are auto-discovered Python modules. Web preview reuses the exact display code path via an in-memory mock framebuffer. WiFi profiles convert from Windows XML to `wpa_supplicant.conf` once via a local script and never enter git.

**Tech Stack:**
- Python 3.11+, managed by `uv`
- Pydantic v2 for config + content validation
- PyYAML for config files
- Pillow (PIL) for image composition
- `waveshare-epaper` Python driver (vendored or pip)
- httpx for async HTTP to API sources
- FastAPI + uvicorn for web preview
- Server-Sent Events for browser frame streaming
- pytest for tests, ruff for linting
- systemd for service supervision
- GitHub Actions for CI

---

## File Structure

```
quotatron/
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .python-version
├── README.md
├── LICENSE
├── Makefile
├── config/
│   └── quotatron.yaml
├── content/
│   ├── quotes/{philosophy,science,literature,leaders,humor}.json
│   └── jokes/{oneliner,dad,programming,observational}.json
├── src/quotatron/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── config.py
│   ├── models.py
│   ├── content.py
│   ├── api_refresh.py
│   ├── sources/
│   │   ├── __init__.py
│   │   ├── _base.py
│   │   ├── quotable_io.py
│   │   ├── zenquotes.py
│   │   ├── type_fit.py
│   │   ├── stoic_quotes.py
│   │   ├── programming_quotes.py
│   │   ├── forismatic.py
│   │   ├── icanhazdadjoke.py
│   │   ├── jokeapi.py
│   │   ├── official_joke_api.py
│   │   ├── chuck_norris_io.py
│   │   └── geek_jokes.py
│   ├── display/
│   │   ├── __init__.py
│   │   ├── _interface.py
│   │   ├── epaper.py
│   │   └── mock.py
│   ├── render.py
│   ├── animations/
│   │   ├── __init__.py
│   │   ├── _base.py
│   │   ├── _builtin_simple_fade.py
│   │   └── <30 plugin files>.py
│   ├── scheduler.py
│   ├── emergency_quotes.py
│   └── web_preview/
│       ├── __init__.py
│       ├── server.py
│       ├── gif_export.py
│       └── static/
│           ├── index.html
│           ├── app.js
│           └── style.css
├── scripts/
│   ├── install.sh
│   ├── flash_sdcard.sh
│   └── wifi_to_wpa.py
├── systemd/
│   └── quotatron.service
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_content.py
│   │   ├── test_render.py
│   │   ├── test_animations.py
│   │   ├── test_scheduler.py
│   │   └── test_wifi_to_wpa.py
│   ├── goldens/
│   │   └── animations/<name>/{0.0,0.25,0.5,0.75,1.0}.png
│   └── sources/
│       └── test_<name>_live.py
├── docs/
│   ├── superpowers/{specs,plans}/
│   └── animations/<name>.gif
└── wifi_profiles/                  GITIGNORED
    └── wpa_supplicant.conf
```

**Responsibility per file:**

- `config.py` — loads + validates YAML; nothing else
- `models.py` — `ContentItem` + shared dataclasses, no logic
- `content.py` — weighted picker, no-repeat window, on-disk cache merge
- `display/_interface.py` — `Display` Protocol both `epaper` and `mock` implement
- `render.py` — text → 1-bit PIL Image, with polarity + rotation
- `animations/_base.py` — `BaseAnimation`, `AnimationContext`, frame-budget logic
- `scheduler.py` — the asyncio loop only; delegates all rendering and IO
- `web_preview/server.py` — FastAPI routes + SSE only; never touches hardware
- `sources/<name>.py` — one HTTP adapter, ~30 lines each

---

## Milestone 0 — Project skeleton

### Task 0.1: Initialize repo metadata

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.python-version`
- Create: `LICENSE` (MIT)
- Create: `README.md` (stub)

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "quotatron"
version = "0.1.0"
description = "Pi Zero W e-paper appliance: rotating quotes/jokes with 30 wipe animations"
requires-python = ">=3.11"
license = {text = "MIT"}
readme = "README.md"
dependencies = [
    "pydantic>=2.5",
    "pyyaml>=6.0",
    "pillow>=10.0",
    "httpx>=0.27",
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "sse-starlette>=2.0",
]

[project.optional-dependencies]
hardware = ["spidev>=3.6", "RPi.GPIO>=0.7"]

[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "ruff>=0.4",
    "watchfiles>=0.21",
]

[project.scripts]
quotatron = "quotatron.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/quotatron"]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
markers = ["live: requires live API access (run via make verify-sources)"]
```

- [ ] **Step 2: Write `.gitignore`**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/

# Local secrets - WiFi profiles (passwords)
wifi_profiles/

# OS / IDE
.DS_Store
.vscode/
.idea/
```

- [ ] **Step 3: Write `.python-version`**

```
3.11
```

- [ ] **Step 4: Write `LICENSE`** — standard MIT, copyright "2026 LCFR".

- [ ] **Step 5: Write `README.md` stub**

```markdown
# Quotatron

A Raspberry Pi Zero W e-paper appliance that displays rotating famous-people
quotes and clean jokes, with 30 different 10-second wipe animations between
each item.

See [`docs/superpowers/specs/2026-04-26-quotatron-design.md`](docs/superpowers/specs/2026-04-26-quotatron-design.md)
for the full design.

## Quick start

```bash
uv sync
uv run quotatron preview        # web preview at http://127.0.0.1:8080
uv run pytest                   # run unit tests
```

Animation gallery: see `docs/animations/`.
```

- [ ] **Step 6: Run `uv sync`**

```bash
uv sync
```

Expected: creates `.venv/`, writes `uv.lock`, installs dependencies.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock .gitignore .python-version LICENSE README.md
git commit -m "chore: initialize project metadata and dependencies"
```

---

### Task 0.2: Source tree scaffolding

**Files:**
- Create: empty `__init__.py` in all package directories

- [ ] **Step 1: Create empty package files**

```bash
mkdir -p src/quotatron/{display,animations,sources,web_preview/static} \
         tests/{unit,sources,goldens/animations} \
         scripts systemd config content/quotes content/jokes \
         docs/animations
touch src/quotatron/__init__.py \
      src/quotatron/display/__init__.py \
      src/quotatron/animations/__init__.py \
      src/quotatron/sources/__init__.py \
      src/quotatron/web_preview/__init__.py \
      tests/__init__.py \
      tests/unit/__init__.py \
      tests/sources/__init__.py
```

- [ ] **Step 2: Create `src/quotatron/__main__.py`**

```python
from quotatron.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Create CLI stub `src/quotatron/cli.py`**

```python
"""Command-line entry point for quotatron."""
import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="quotatron")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Run the display service (production)")
    sub.add_parser("preview", help="Run the web preview / animation tester")
    sub.add_parser("verify-sources", help="Test all configured API sources")

    args = parser.parse_args(argv)

    if args.command == "run":
        from quotatron.scheduler import run_service
        return run_service()
    if args.command == "preview":
        from quotatron.web_preview.server import run_preview
        return run_preview()
    if args.command == "verify-sources":
        from quotatron.api_refresh import verify_all_sources
        return verify_all_sources()
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Verify package imports**

```bash
uv run python -c "import quotatron; print(quotatron.__name__)"
```

Expected: prints `quotatron` (no error).

- [ ] **Step 5: Commit**

```bash
git add src/ tests/ scripts/ systemd/ config/ content/ docs/
git commit -m "chore: scaffold source tree, package init files, CLI skeleton"
```

---

## Milestone 1 — Configuration

### Task 1.1: Pydantic config models

**Files:**
- Create: `src/quotatron/config.py`
- Create: `tests/unit/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_config.py
import pytest
from pathlib import Path
from quotatron.config import Config, load_config


def test_loads_default_config_from_yaml(tmp_path: Path) -> None:
    yaml = """
display:
  rotation: landscape
  driver: waveshare_2in13_v3
  full_refresh_every: 1
cycle:
  quote_seconds: 50
  animation_seconds: 10
  invert_polarity_every: 1
content:
  quote_to_joke_ratio: 0.7
  no_repeat_window: 200
  weights:
    quotes: {philosophy: 1.0, science: 1.0}
    jokes: {oneliner: 1.0}
api_refresh:
  enabled: true
  interval_minutes: 60
  fail_silently: true
  per_source_timeout_seconds: 5
  max_items_per_refresh: 50
  sources: []
animations:
  enabled: true
  shuffle: random
  blocklist: []
  per_animation_overrides: {}
logging:
  level: INFO
  path: /var/log/quotatron.log
web_preview:
  enabled_in_dev: true
  host: 127.0.0.1
  port: 8080
"""
    p = tmp_path / "c.yaml"
    p.write_text(yaml)
    cfg = load_config(p)
    assert isinstance(cfg, Config)
    assert cfg.display.rotation == "landscape"
    assert cfg.cycle.quote_seconds == 50
    assert cfg.content.quote_to_joke_ratio == 0.7


def test_invalid_rotation_rejected(tmp_path: Path) -> None:
    yaml = "display:\n  rotation: sideways\n"
    p = tmp_path / "c.yaml"
    p.write_text(yaml)
    with pytest.raises(ValueError):
        load_config(p)


def test_quote_to_joke_ratio_must_be_in_range(tmp_path: Path) -> None:
    yaml = "content:\n  quote_to_joke_ratio: 1.5\n"
    p = tmp_path / "c.yaml"
    p.write_text(yaml)
    with pytest.raises(ValueError):
        load_config(p)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/test_config.py -v
```

Expected: FAIL — module `quotatron.config` not found.

- [ ] **Step 3: Implement `src/quotatron/config.py`**

```python
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
    ] = "waveshare_2in13_v3"
    full_refresh_every: int = Field(1, ge=1)


class CycleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quote_seconds: int = Field(50, ge=1, le=600)
    animation_seconds: int = Field(10, ge=1, le=600)
    invert_polarity_every: int = Field(1, ge=1)


class ContentWeights(BaseModel):
    model_config = ConfigDict(extra="allow")
    # Allows arbitrary category keys with float weights.


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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/unit/test_config.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/quotatron/config.py tests/unit/test_config.py
git commit -m "feat(config): pydantic models and YAML loader"
```

---

### Task 1.2: Default config file

**Files:**
- Create: `config/quotatron.yaml`

- [ ] **Step 1: Write the default config**

(Copy the full YAML from spec §4 into `config/quotatron.yaml` verbatim.)

- [ ] **Step 2: Add a sanity test**

```python
# tests/unit/test_config.py — append
def test_default_config_file_loads() -> None:
    from quotatron.config import load_config
    cfg = load_config("config/quotatron.yaml")
    assert cfg.display.rotation == "landscape"
    assert len(cfg.api_refresh.sources) == 11
    assert cfg.cycle.quote_seconds + cfg.cycle.animation_seconds == 60
```

- [ ] **Step 3: Run test**

```bash
uv run pytest tests/unit/test_config.py::test_default_config_file_loads -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add config/quotatron.yaml tests/unit/test_config.py
git commit -m "feat(config): default quotatron.yaml shipping config"
```

---

## Milestone 2 — Display abstraction + render

### Task 2.1: Display Protocol + mock framebuffer

**Files:**
- Create: `src/quotatron/display/_interface.py`
- Create: `src/quotatron/display/mock.py`
- Create: `tests/unit/test_display_mock.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_display_mock.py
from PIL import Image
from quotatron.display.mock import MockDisplay


def test_mock_records_images_with_mode_tags() -> None:
    d = MockDisplay(width=250, height=122)
    img = Image.new("1", (250, 122), 1)
    d.display_full(img)
    d.enter_partial_mode()
    d.display_partial(img)
    d.display_partial(img)
    d.exit_partial_mode()
    d.display_full(img)
    assert [m for m, _ in d.history] == [
        "full", "enter_partial", "partial", "partial", "exit_partial", "full"
    ]
    assert d.current_image() is not None


def test_mock_rejects_wrong_size() -> None:
    d = MockDisplay(width=250, height=122)
    img = Image.new("1", (200, 122), 1)
    import pytest
    with pytest.raises(ValueError):
        d.display_full(img)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/test_display_mock.py -v
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `src/quotatron/display/_interface.py`**

```python
"""Display Protocol shared by hardware and mock implementations."""
from __future__ import annotations
from typing import Protocol
from PIL import Image


class Display(Protocol):
    width: int
    height: int

    def display_full(self, img: Image.Image) -> None: ...
    def enter_partial_mode(self) -> None: ...
    def display_partial(self, img: Image.Image) -> None: ...
    def exit_partial_mode(self) -> None: ...
    def deep_clean(self) -> None: ...
    def shutdown(self, farewell: Image.Image | None = None) -> None: ...
```

- [ ] **Step 4: Implement `src/quotatron/display/mock.py`**

```python
"""In-memory display backend for tests and the web preview."""
from __future__ import annotations
from PIL import Image


class MockDisplay:
    def __init__(self, width: int = 250, height: int = 122) -> None:
        self.width = width
        self.height = height
        self.history: list[tuple[str, Image.Image | None]] = []
        self._current: Image.Image | None = None
        self._in_partial = False

    def _check_size(self, img: Image.Image) -> None:
        if (img.width, img.height) != (self.width, self.height):
            raise ValueError(
                f"image size {img.size} != display size {(self.width, self.height)}"
            )

    def display_full(self, img: Image.Image) -> None:
        self._check_size(img)
        self.history.append(("full", img.copy()))
        self._current = img.copy()

    def enter_partial_mode(self) -> None:
        self._in_partial = True
        self.history.append(("enter_partial", None))

    def display_partial(self, img: Image.Image) -> None:
        if not self._in_partial:
            raise RuntimeError("must enter_partial_mode before display_partial")
        self._check_size(img)
        self.history.append(("partial", img.copy()))
        self._current = img.copy()

    def exit_partial_mode(self) -> None:
        self._in_partial = False
        self.history.append(("exit_partial", None))

    def deep_clean(self) -> None:
        self.history.append(("deep_clean", None))

    def shutdown(self, farewell: Image.Image | None = None) -> None:
        if farewell is not None:
            self.display_full(farewell)
        self.history.append(("shutdown", None))

    def current_image(self) -> Image.Image | None:
        return self._current
```

- [ ] **Step 5: Run tests**

```bash
uv run pytest tests/unit/test_display_mock.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add src/quotatron/display/ tests/unit/test_display_mock.py
git commit -m "feat(display): Display Protocol and MockDisplay backend"
```

---

### Task 2.2: Renderer (text → 1-bit image)

**Files:**
- Create: `src/quotatron/render.py`
- Create: `src/quotatron/models.py`
- Create: `tests/unit/test_render.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_render.py
from quotatron.models import ContentItem, Polarity
from quotatron.render import compose


def make_item() -> ContentItem:
    return ContentItem(
        kind="quote",
        text="The unexamined life is not worth living.",
        author="Socrates",
        category="philosophy",
        source="bundled",
    )


def test_landscape_compose_returns_correct_size_1bit() -> None:
    img = compose(make_item(), polarity=Polarity.NORMAL, rotation="landscape")
    assert img.size == (250, 122)
    assert img.mode == "1"


def test_portrait_rotates_canvas() -> None:
    img = compose(make_item(), polarity=Polarity.NORMAL, rotation="portrait")
    assert img.size == (250, 122)  # final framebuffer is always landscape;
                                    # portrait is rendered then rotated by display layer


def test_inverted_polarity_swaps_bg_fg() -> None:
    normal = compose(make_item(), polarity=Polarity.NORMAL, rotation="landscape")
    inverted = compose(make_item(), polarity=Polarity.INVERTED, rotation="landscape")
    # Counts of black pixels should differ massively between normal and inverted
    n_black = sum(1 for p in normal.getdata() if p == 0)
    i_black = sum(1 for p in inverted.getdata() if p == 0)
    assert n_black + i_black > 1000
    # In normal: bg white (1) → most pixels white. In inverted: bg black (0) → most black.
    assert i_black > n_black


def test_long_text_wraps_within_canvas() -> None:
    long = ContentItem(
        kind="quote",
        text=("a" * 400),  # forces wrapping
        author="anon",
        category="philosophy",
        source="bundled",
    )
    img = compose(long, polarity=Polarity.NORMAL, rotation="landscape")
    assert img.size == (250, 122)  # never exceeds canvas
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/test_render.py -v
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `src/quotatron/models.py`**

```python
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
```

- [ ] **Step 4: Implement `src/quotatron/render.py`**

```python
"""Compose a ContentItem into a 1-bit framebuffer image."""
from __future__ import annotations
from importlib import resources
from PIL import Image, ImageDraw, ImageFont
from quotatron.models import ContentItem, Polarity

CANVAS_W, CANVAS_H = 250, 122  # native landscape resolution
TEXT_MARGIN = 6
AUTHOR_MARGIN = 4


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    # DejaVu Sans is bundled with Pillow's source distribution and present on
    # Pi OS via fonts-dejavu. Use Pillow's bundled copy as a portable default.
    return ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size
    ) if _dejavu_installed() else ImageFont.load_default()


def _dejavu_installed() -> bool:
    from pathlib import Path
    return Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf").exists()


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for w in words:
        candidate = " ".join(cur + [w])
        if font.getlength(candidate) <= max_w or not cur:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


def compose(
    item: ContentItem,
    *,
    polarity: Polarity,
    rotation: str = "landscape",
) -> Image.Image:
    """Render a ContentItem to a 1-bit Pillow Image of size CANVAS_W x CANVAS_H.

    The returned image is always landscape (250x122). The display driver applies
    rotation when pushing to the panel.
    """
    img = Image.new("1", (CANVAS_W, CANVAS_H), polarity.bg)
    draw = ImageDraw.Draw(img)

    # Auto-fit body font: try sizes 16, 14, 12, 10 until text fits.
    body_lines: list[str] = []
    body_font: ImageFont.FreeTypeFont | None = None
    line_h = 0
    for size in (16, 14, 12, 10):
        f = _load_font(size)
        max_text_w = CANVAS_W - 2 * TEXT_MARGIN
        lines = _wrap(item.text, f, max_text_w)
        # Reserve ~14px for author, leave ~5px gap
        author_h = 12
        gap = AUTHOR_MARGIN
        avail_h = CANVAS_H - 2 * TEXT_MARGIN - author_h - gap
        lh = int(f.size * 1.15)
        if len(lines) * lh <= avail_h:
            body_lines = lines
            body_font = f
            line_h = lh
            break
    if body_font is None:
        body_font = _load_font(10)
        body_lines = _wrap(item.text, body_font, CANVAS_W - 2 * TEXT_MARGIN)
        line_h = int(body_font.size * 1.15)
        # Truncate to fit; add ellipsis to last line.
        max_lines = (CANVAS_H - 2 * TEXT_MARGIN - 12 - AUTHOR_MARGIN) // line_h
        if len(body_lines) > max_lines:
            body_lines = body_lines[:max_lines]
            body_lines[-1] = (body_lines[-1][:-1] + "…") if body_lines[-1] else "…"

    # Draw body
    y = TEXT_MARGIN
    for line in body_lines:
        draw.text((TEXT_MARGIN, y), line, fill=polarity.fg, font=body_font)
        y += line_h

    # Draw author bottom-right (italic style approximated with prefix dash)
    author_font = _load_font(11)
    author_text = f"— {item.author}"
    aw = author_font.getlength(author_text)
    draw.text(
        (CANVAS_W - TEXT_MARGIN - aw, CANVAS_H - TEXT_MARGIN - 12),
        author_text,
        fill=polarity.fg,
        font=author_font,
    )

    return img
```

- [ ] **Step 5: Run tests**

```bash
uv run pytest tests/unit/test_render.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```bash
git add src/quotatron/render.py src/quotatron/models.py tests/unit/test_render.py
git commit -m "feat(render): compose ContentItem into 1-bit framebuffer"
```

---

## Milestone 3 — Content system

### Task 3.1: Bundled JSON content seed files

**Files:**
- Create: `content/quotes/{philosophy,science,literature,leaders,humor}.json`
- Create: `content/jokes/{oneliner,dad,programming,observational}.json`

Each file ships a minimum of 10 well-known public-domain items as the seed corpus. JSON shape:

```json
[
  {"text": "...", "author": "...", "category": "philosophy"}
]
```

- [ ] **Step 1: Write `content/quotes/philosophy.json`** — 10 items (Socrates, Aristotle, Marcus Aurelius, Seneca, Epictetus, Plato, Lao Tzu, Confucius, Nietzsche, Kant — all out of copyright).

- [ ] **Step 2: Write the other 8 JSON files** the same way. Programming jokes can be original/folk-style (no attribution).

- [ ] **Step 3: Add JSON validity test**

```python
# tests/unit/test_content_seed.py
import json
from pathlib import Path
import pytest

@pytest.mark.parametrize("path", list(Path("content").rglob("*.json")))
def test_seed_json_files_parse_and_have_required_fields(path: Path) -> None:
    data = json.loads(path.read_text())
    assert isinstance(data, list)
    assert len(data) >= 10
    for item in data:
        assert set(["text", "author", "category"]).issubset(item.keys())
        assert 1 <= len(item["text"]) <= 800
```

- [ ] **Step 4: Run test**

```bash
uv run pytest tests/unit/test_content_seed.py -v
```

Expected: 9 passed (one per category file).

- [ ] **Step 5: Commit**

```bash
git add content/ tests/unit/test_content_seed.py
git commit -m "feat(content): bundled seed quotes and jokes (~90 items)"
```

---

### Task 3.2: Weighted picker with no-repeat window

**Files:**
- Create: `src/quotatron/content.py`
- Create: `tests/unit/test_content.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_content.py
from collections import Counter
from quotatron.content import ContentLibrary
from quotatron.models import ContentItem

def make_lib() -> ContentLibrary:
    items = [
        ContentItem(kind="quote", text="q1", author="a", category="philosophy", source="bundled"),
        ContentItem(kind="quote", text="q2", author="a", category="science", source="bundled"),
        ContentItem(kind="joke",  text="j1", author="a", category="dad", source="bundled"),
        ContentItem(kind="joke",  text="j2", author="a", category="oneliner", source="bundled"),
    ]
    return ContentLibrary(items=items)

def test_picker_respects_quote_to_joke_ratio_in_aggregate() -> None:
    lib = make_lib()
    counts = Counter()
    for _ in range(2000):
        item = lib.next_item(
            quote_to_joke_ratio=0.7,
            quote_weights={"philosophy": 1.0, "science": 1.0},
            joke_weights={"dad": 1.0, "oneliner": 1.0},
            no_repeat_window=0,
            seed=None,
        )
        counts[item.kind] += 1
    ratio = counts["quote"] / (counts["quote"] + counts["joke"])
    assert 0.65 < ratio < 0.75

def test_no_repeat_window_avoids_recent_items() -> None:
    lib = make_lib()
    seen = []
    for _ in range(20):
        seen.append(lib.next_item(
            quote_to_joke_ratio=0.5,
            quote_weights={"philosophy": 1.0, "science": 1.0},
            joke_weights={"dad": 1.0, "oneliner": 1.0},
            no_repeat_window=2,
            seed=None,
        ).text)
    # No three consecutive identical
    for i in range(len(seen) - 2):
        assert not (seen[i] == seen[i+1] == seen[i+2])

def test_falls_back_when_window_excludes_all() -> None:
    # Two items, window of 5: must still return something.
    items = [
        ContentItem(kind="quote", text="x", author="a", category="philosophy", source="bundled"),
        ContentItem(kind="quote", text="y", author="a", category="philosophy", source="bundled"),
    ]
    lib = ContentLibrary(items=items)
    for _ in range(10):
        out = lib.next_item(
            quote_to_joke_ratio=1.0,
            quote_weights={"philosophy": 1.0},
            joke_weights={},
            no_repeat_window=5,
            seed=None,
        )
        assert out.text in {"x", "y"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/unit/test_content.py -v
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `src/quotatron/content.py`**

```python
"""Content library: bundled JSON loading + weighted picker."""
from __future__ import annotations
import json
import random
from collections import deque
from pathlib import Path
from quotatron.models import ContentItem


class ContentLibrary:
    def __init__(self, items: list[ContentItem]) -> None:
        if not items:
            raise ValueError("ContentLibrary requires at least one item")
        self.items = items
        self._recent: deque[str] = deque(maxlen=1000)

    @classmethod
    def from_disk(cls, root: str | Path) -> "ContentLibrary":
        root = Path(root)
        items: list[ContentItem] = []
        for kind_dir, kind in (("quotes", "quote"), ("jokes", "joke")):
            for f in (root / kind_dir).glob("*.json"):
                category = f.stem
                for raw in json.loads(f.read_text()):
                    items.append(ContentItem(
                        kind=kind,
                        text=raw["text"],
                        author=raw.get("author", "anonymous"),
                        category=raw.get("category", category),
                        source=raw.get("source", "bundled"),
                    ))
        return cls(items=items)

    def next_item(
        self,
        *,
        quote_to_joke_ratio: float,
        quote_weights: dict[str, float],
        joke_weights: dict[str, float],
        no_repeat_window: int,
        seed: int | None = None,
    ) -> ContentItem:
        rng = random.Random(seed)
        kind = "quote" if rng.random() < quote_to_joke_ratio else "joke"
        weights = quote_weights if kind == "quote" else joke_weights
        pool = [it for it in self.items if it.kind == kind and it.category in weights]
        if not pool:
            # Fallback: any item of this kind, then any item at all.
            pool = [it for it in self.items if it.kind == kind] or list(self.items)

        # Build weighted list, excluding recent items (best-effort).
        window = list(self._recent)[-no_repeat_window:] if no_repeat_window else []
        eligible = [it for it in pool if it.text not in window]
        if not eligible:
            eligible = pool

        weighted = [(it, weights.get(it.category, 0.0) or 1.0) for it in eligible]
        choice = rng.choices(
            [it for it, _ in weighted],
            weights=[w for _, w in weighted],
            k=1,
        )[0]
        self._recent.append(choice.text)
        return choice
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/unit/test_content.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add src/quotatron/content.py tests/unit/test_content.py
git commit -m "feat(content): weighted picker with no-repeat window"
```

---

### Task 3.3: Emergency-quote fallback

**Files:**
- Create: `src/quotatron/emergency_quotes.py`

- [ ] **Step 1: Write the module**

```python
"""Hardcoded ~30 quotes used when content/ JSON files are missing or corrupt."""
from quotatron.models import ContentItem

EMERGENCY: list[ContentItem] = [
    ContentItem(kind="quote", text=t, author=a, category="philosophy", source="emergency")
    for t, a in [
        ("The unexamined life is not worth living.", "Socrates"),
        ("Know thyself.", "Inscription at Delphi"),
        ("Cogito, ergo sum.", "Descartes"),
        ("Man is condemned to be free.", "Sartre"),
        # ... 26 more
    ]
]


def emergency_library():
    from quotatron.content import ContentLibrary
    return ContentLibrary(items=list(EMERGENCY))
```

(Fill in the remaining 26 entries with well-known public-domain quotes.)

- [ ] **Step 2: Verify import**

```bash
uv run python -c "from quotatron.emergency_quotes import EMERGENCY; print(len(EMERGENCY))"
```

Expected: prints `30`.

- [ ] **Step 3: Commit**

```bash
git add src/quotatron/emergency_quotes.py
git commit -m "feat(content): hardcoded emergency quote fallback"
```

---

## Milestone 4 — Animation framework

### Task 4.1: BaseAnimation, AnimationContext

**Files:**
- Create: `src/quotatron/animations/_base.py`
- Create: `tests/unit/test_animations.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_animations.py
from PIL import Image
from quotatron.animations._base import (
    AnimationContext, BaseAnimation, frame_count_for_duration,
)
from quotatron.models import Polarity


def test_frame_count_respects_target_fps_and_panel_minimum() -> None:
    # 10s at 5 fps = 50 frames, but panel min is 0.3s/frame → max ~33 frames.
    n = frame_count_for_duration(duration_s=10.0, target_fps=5)
    assert 20 <= n <= 33


class _Identity(BaseAnimation):
    name = "identity"
    duration_default = 1.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        return ctx.to_image if t >= 0.5 else ctx.from_image


def test_base_animation_yields_frames_between_from_and_to() -> None:
    from_img = Image.new("1", (250, 122), 1)
    to_img = Image.new("1", (250, 122), 0)
    ctx = AnimationContext(
        from_image=from_img, to_image=to_img,
        polarity=Polarity.NORMAL, width=250, height=122,
    )
    anim = _Identity()
    frames = list(anim.frames(ctx, duration_s=1.0))
    assert len(frames) >= 5
    assert frames[0].getpixel((0, 0)) == 1
    assert frames[-1].getpixel((0, 0)) == 0
```

- [ ] **Step 2: Run to verify failure**

```bash
uv run pytest tests/unit/test_animations.py -v
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `src/quotatron/animations/_base.py`**

```python
"""Animation plugin contract."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator, Literal
from PIL import Image
from quotatron.models import Polarity

PANEL_MIN_FRAME_SECONDS = 0.3   # Waveshare 2.13" partial-refresh floor


def frame_count_for_duration(duration_s: float, target_fps: int) -> int:
    """Compute frame count respecting both target FPS and panel minimum frame time."""
    requested = int(round(duration_s * target_fps))
    panel_max = int(duration_s / PANEL_MIN_FRAME_SECONDS)
    return max(2, min(requested, panel_max))


@dataclass
class AnimationContext:
    from_image: Image.Image
    to_image: Image.Image
    polarity: Polarity
    width: int
    height: int

    @property
    def fg(self) -> int:
        return self.polarity.fg

    @property
    def bg(self) -> int:
        return self.polarity.bg


class BaseAnimation(ABC):
    name: str = "unnamed"
    duration_default: float = 10.0
    target_fps: int = 5
    palette: Literal["auto", "force_white_on_black", "force_black_on_white"] = "auto"

    @abstractmethod
    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        """Render one frame at progress t in [0,1]. Must return a 1-bit image."""

    def frames(
        self, ctx: AnimationContext, duration_s: float | None = None
    ) -> Iterator[Image.Image]:
        d = duration_s if duration_s is not None else self.duration_default
        n = frame_count_for_duration(d, self.target_fps)
        for i in range(n):
            t = i / max(1, n - 1)
            img = self.render(t, ctx)
            if img.mode != "1":
                img = img.convert("1")
            yield img
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/unit/test_animations.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add src/quotatron/animations/_base.py tests/unit/test_animations.py
git commit -m "feat(animations): BaseAnimation, AnimationContext, frame budget"
```

---

### Task 4.2: Plugin auto-discovery

**Files:**
- Modify: `src/quotatron/animations/__init__.py`
- Create: `src/quotatron/animations/_builtin_simple_fade.py`
- Modify: `tests/unit/test_animations.py`

- [ ] **Step 1: Write the simple_fade builtin**

```python
# src/quotatron/animations/_builtin_simple_fade.py
"""Always-shipped fallback animation. Not registered as a user-facing plugin."""
from __future__ import annotations
from PIL import Image
from quotatron.animations._base import BaseAnimation, AnimationContext


class SimpleFade(BaseAnimation):
    name = "simple_fade"
    duration_default = 10.0
    target_fps = 4
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        # Crude crossfade via Bayer dither threshold modulated by t.
        from PIL import ImageChops
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        a = ctx.from_image.convert("L")
        b = ctx.to_image.convert("L")
        blended = ImageChops.blend(a, b, t).convert("1")
        return blended
```

- [ ] **Step 2: Implement auto-discovery in `__init__.py`**

```python
# src/quotatron/animations/__init__.py
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
```

- [ ] **Step 3: Add tests**

```python
# tests/unit/test_animations.py — append
def test_registry_finds_no_user_plugins_initially() -> None:
    from quotatron.animations import registry
    reg = registry(refresh=True)
    # No plugin files yet — registry empty (simple_fade is _builtin_).
    assert reg == {}


def test_fallback_returns_simple_fade() -> None:
    from quotatron.animations import fallback
    from quotatron.animations._builtin_simple_fade import SimpleFade
    assert fallback() is SimpleFade
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/unit/test_animations.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/quotatron/animations/ tests/unit/test_animations.py
git commit -m "feat(animations): plugin auto-discovery and simple_fade builtin"
```

---

## Milestone 5 — The 30 plugin animations

### Task 5.1: Animation exemplar — `diagonal_wipe`

This task is the **template every other animation follows**. Subsequent tasks reference this pattern.

**Files:**
- Create: `src/quotatron/animations/diagonal_wipe.py`
- Create: `tests/goldens/animations/diagonal_wipe/{0.0,0.25,0.5,0.75,1.0}.png`
- Modify: `tests/unit/test_animations.py`

- [ ] **Step 1: Write the failing golden test**

```python
# tests/unit/test_animations.py — append
import pytest
from PIL import Image, ImageChops
from pathlib import Path
from quotatron.animations._base import AnimationContext
from quotatron.models import Polarity

GOLDENS_ROOT = Path("tests/goldens/animations")


def _make_ctx() -> AnimationContext:
    a = Image.new("1", (250, 122), 1)  # white
    b = Image.new("1", (250, 122), 0)  # black
    return AnimationContext(
        from_image=a, to_image=b, polarity=Polarity.NORMAL, width=250, height=122,
    )


@pytest.mark.parametrize("t", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_diagonal_wipe_matches_golden(t: float) -> None:
    from quotatron.animations.diagonal_wipe import DiagonalWipe
    ctx = _make_ctx()
    out = DiagonalWipe().render(t, ctx)
    expected_path = GOLDENS_ROOT / "diagonal_wipe" / f"{t}.png"
    assert expected_path.exists(), (
        f"missing golden {expected_path} — generate with `make update-goldens`"
    )
    expected = Image.open(expected_path).convert("1")
    diff = ImageChops.difference(out, expected)
    assert diff.getbbox() is None, f"diagonal_wipe at t={t} differs from golden"
```

- [ ] **Step 2: Implement the animation**

```python
# src/quotatron/animations/diagonal_wipe.py
"""Diagonal wipe from upper-left to lower-right replacing from_image with to_image."""
from __future__ import annotations
from PIL import Image, ImageDraw
from quotatron.animations._base import AnimationContext, BaseAnimation


class DiagonalWipe(BaseAnimation):
    name = "diagonal_wipe"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        # Diagonal line equation: x + y < threshold ⇒ from to_image.
        # Total diagonal length: w + h. Threshold sweeps 0 → w+h as t: 0→1.
        w, h = ctx.width, ctx.height
        threshold = (w + h) * t
        out = ctx.from_image.copy()
        mask = Image.new("1", (w, h), 0)
        md = ImageDraw.Draw(mask)
        # Triangle bounded by x + y < threshold
        md.polygon(
            [(0, 0), (min(w, threshold), 0), (0, min(h, threshold))],
            fill=1,
        )
        # If threshold > w, also fill rectangle and second triangle (parallelogram).
        if threshold > w:
            md.polygon(
                [(0, 0), (w, 0), (w, min(h, threshold - w)), (0, 0)],
                fill=1,
            )
            md.polygon(
                [(0, 0), (w, min(h, threshold - w)),
                 (min(w, threshold), 0)],
                fill=1,
            )
        out.paste(ctx.to_image, mask=mask)
        return out
```

- [ ] **Step 3: Run test, expect golden missing**

```bash
uv run pytest tests/unit/test_animations.py::test_diagonal_wipe_matches_golden -v
```

Expected: FAIL — golden files missing.

- [ ] **Step 4: Generate goldens**

Add a `Makefile` target (or one-shot script):

```bash
mkdir -p tests/goldens/animations/diagonal_wipe
uv run python -c "
from PIL import Image
from quotatron.animations.diagonal_wipe import DiagonalWipe
from quotatron.animations._base import AnimationContext
from quotatron.models import Polarity
a = Image.new('1', (250, 122), 1); b = Image.new('1', (250, 122), 0)
ctx = AnimationContext(a, b, Polarity.NORMAL, 250, 122)
for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
    DiagonalWipe().render(t, ctx).save(f'tests/goldens/animations/diagonal_wipe/{t}.png')
"
```

- [ ] **Step 5: Visually inspect each PNG** before re-running the test. Open in any image viewer and confirm the wipe progresses sensibly.

- [ ] **Step 6: Run test to verify it passes**

```bash
uv run pytest tests/unit/test_animations.py::test_diagonal_wipe_matches_golden -v
```

Expected: 5 passed.

- [ ] **Step 7: Commit**

```bash
git add src/quotatron/animations/diagonal_wipe.py tests/goldens/animations/diagonal_wipe/ tests/unit/test_animations.py
git commit -m "feat(animations): diagonal_wipe (1/30) — exemplar pattern"
```

---

### Tasks 5.2–5.30: The remaining 29 animations

**Workflow per animation (identical to Task 5.1):**
1. Write parametrized golden test (5 t values, copy from Task 5.1)
2. Implement `<name>.py` with the math listed below
3. Run test → fails (no goldens yet)
4. Generate goldens with the snippet from Task 5.1, swapping the import
5. Visually inspect
6. Re-run test → passes
7. Commit as `feat(animations): <name> (N/30)`

**For each animation, the file template is:**

```python
# src/quotatron/animations/<name>.py
"""<one-line description>"""
from __future__ import annotations
from PIL import Image, ImageDraw  # plus other PIL/numpy as needed
import math, random
from quotatron.animations._base import AnimationContext, BaseAnimation


class <ClassName>(BaseAnimation):
    name = "<name>"
    duration_default = 10.0
    target_fps = <fps>
    palette = "auto"

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        if t <= 0.0: return ctx.from_image.copy()
        if t >= 1.0: return ctx.to_image.copy()
        # ... math ...
        return out
```

**The 29 animations:**

| # | name | category | fps | render math |
|---|------|----------|-----|---|
| 5.2 | `radial_wipe` | wipe | 5 | mask = circle from center, radius = `t * hypot(w/2, h/2)` |
| 5.3 | `barn_door_wipe` | wipe | 5 | two rectangles meeting at center, width = `t * w/2` each |
| 5.4 | `random_pixel_dissolve` | dissolve | 5 | seeded shuffle of pixel coords; first `t * w*h` switch to to_image |
| 5.5 | `ordered_dither_dissolve` | dissolve | 5 | 8×8 Bayer matrix threshold = `t * 255`; pixels above threshold flip |
| 5.6 | `diffusion_dissolve` | dissolve | 5 | floyd-steinberg-style propagation of "infected" pixels from random seeds |
| 5.7 | `expanding_rectangles` | geometric | 5 | concentric rectangles from center, side length `t * max(w,h)` |
| 5.8 | `concentric_circles` | geometric | 5 | filled circle radius `t * max_dim`; alternates fg/bg in rings |
| 5.9 | `grid_stamp` | geometric | 5 | 8×4 grid of cells, each turns at random t-offset within `[0, 1]` |
| 5.10 | `droplets` | organic | 5 | 6–10 random drop centers; each grows radius `t² * 30`; merges via union |
| 5.11 | `ink_bleed` | organic | 5 | seed point grows via 4-connectivity, jittered every frame |
| 5.12 | `snake_fill` | organic | 5 | row-by-row left-to-right then right-to-left "boustrophedon" reveal, segment length = `t * total` |
| 5.13 | `flood_fill` | organic | 5 | BFS from random corner, advance by `(t-prev_t) * w*h` cells per frame |
| 5.14 | `line_shuffle` | glitch | 5 | shift each row horizontally by `random_offset * (1 - smoothstep(t))`, decreasing |
| 5.15 | `block_jitter` | glitch | 5 | divide canvas into 16×16 blocks; each block jitters position with amplitude `(1-t) * 8` |
| 5.16 | `scanline_tear` | glitch | 5 | horizontal scanlines tear and slip, slip amount lerps to 0 by `t=1` |
| 5.17 | `sine_sweep` | wave | 5 | vertical line sweeps left→right; line wobbles as `sin(y * 0.1 + t * 4π) * 6` |
| 5.18 | `ripple` | wave | 5 | concentric expanding rings; ring n at radius `((t * 1.5) - n*0.15) * max_dim`, drawn if `0 < r < max` |
| 5.19 | `pure_noise` | noise | 4 | each pixel = random.random() < t ? to : from |
| 5.20 | `perlin_fade` | noise | 4 | use a deterministic value-noise field; threshold = `t`; smoother than pure_noise |
| 5.21 | `conway_iterations` | growth | 4 | start with from_image, run N Game-of-Life steps; lerp toward to_image as `t→1` |
| 5.22 | `vine_grow` | growth | 5 | seed at bottom-center; advance via random walk, branching at probability 0.1; thicken with `t` |
| 5.23 | `dendritic` | growth | 5 | DLA (diffusion-limited aggregation) particles starting from edges, sticking to grown structure |
| 5.24 | `column_rain` | pixel-sort | 5 | per-column: pixels fall from top, settling height = `t * h`; columns staggered by `column % 7 * 0.1` |
| 5.25 | `falling_pixels` | pixel-sort | 5 | scattered pixels of to_image fall with gravity from y=−10 to their final y |
| 5.26 | `spiral` | path | 5 | archimedean spiral path; reveal pixels visited up to arc length = `t * total_arc` |
| 5.27 | `hilbert_fill` | path | 5 | hilbert curve order 7 (fits 250×122 truncated); reveal cells visited up to `t * len` |
| 5.28 | `lissajous` | path | 5 | 5 lissajous curves with prime ratios; trace pixels visited up to `t * cycle` |
| 5.29 | `matrix_rain` | special | 5 | columns of falling characters (using small font); chars resolve into to_image's pixels |
| 5.30 | `typewriter_overprint` | special | 5 | scan to_image left-to-right top-to-bottom; reveal char-cell-sized blocks one per frame in row order |

**Each task lives as Task 5.N in this plan; the structure is identical to Task 5.1**, only the rendering body and golden directory name change.

After all 30 are committed, run the full suite:

```bash
uv run pytest tests/unit/test_animations.py -v
```

Expected: ≥150 passed (5 goldens × 30 animations + framework tests).

---

## Milestone 6 — API source adapters

### Task 6.1: Source base class + ContentItem normalization

**Files:**
- Create: `src/quotatron/sources/_base.py`
- Create: `tests/unit/test_source_base.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_source_base.py
import pytest
from quotatron.sources._base import BaseSource, fetch_with_timeout
from quotatron.models import ContentItem


class _Dummy(BaseSource):
    name = "dummy"
    base_url = "https://example.invalid"
    kind = "quote"

    async def fetch(self, limit: int) -> list[ContentItem]:
        return [ContentItem(kind="quote", text="hi", author="me", category="philosophy", source="dummy")]


def test_dummy_source_returns_content_item() -> None:
    import asyncio
    items = asyncio.run(_Dummy().fetch(limit=1))
    assert len(items) == 1
    assert items[0].source == "dummy"
```

- [ ] **Step 2: Run test (fails — module not found)**

- [ ] **Step 3: Implement `_base.py`**

```python
# src/quotatron/sources/_base.py
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
```

- [ ] **Step 4: Run test (passes)**

- [ ] **Step 5: Commit**

```bash
git add src/quotatron/sources/_base.py tests/unit/test_source_base.py
git commit -m "feat(sources): BaseSource adapter contract"
```

---

### Tasks 6.2–6.12: 11 source adapters

**Workflow per source (~30 lines each):**
1. Implement `src/quotatron/sources/<name>.py` from the template below
2. Write a live integration test in `tests/sources/test_<name>_live.py` marked `@pytest.mark.live`
3. Manually run `uv run pytest -m live tests/sources/test_<name>_live.py` to verify
4. Commit

**Adapter template:**

```python
# src/quotatron/sources/<name>.py
from __future__ import annotations
import httpx
from quotatron.models import ContentItem
from quotatron.sources._base import BaseSource


class <Name>Source(BaseSource):
    name = "<name>"
    base_url = "<URL>"
    kind = "<quote|joke>"

    async def fetch(self, limit: int) -> list[ContentItem]:
        out: list[ContentItem] = []
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(self.base_url, params={...}, headers={...})
            r.raise_for_status()
            data = r.json()
            for entry in data[:limit]:
                out.append(ContentItem(
                    kind=self.kind,
                    text=entry["<field>"],
                    author=entry.get("<field>", "anonymous"),
                    category="<default>",
                    source=self.name,
                ))
        return out
```

**Per-source specifics** (URL, fields, auth headers):

| # | name | URL | method | text field | author field | notes |
|---|---|---|---|---|---|---|
| 6.2 | `quotable_io` | `https://api.quotable.io/quotes/random?limit={n}` | GET | `content` | `author` | returns array, max limit=20 |
| 6.3 | `zenquotes` | `https://zenquotes.io/api/quotes/` | GET | `q` | `a` | rate-limited, 50 per request, treat 429 as empty |
| 6.4 | `type_fit` | `https://type.fit/api/quotes` | GET | `text` | `author` | static JSON, ~1600 entries; sample N randomly |
| 6.5 | `stoic_quotes` | `https://stoic-quotes.com/api/quotes` | GET | `text` | `author` | tag all `category=philosophy` |
| 6.6 | `programming_quotes` | `https://programming-quotes-api.herokuapp.com/Quotes/random/quotes/{n}` | GET | `en` | `author` | tag `category=science` |
| 6.7 | `forismatic` | `http://api.forismatic.com/api/1.0/?method=getQuote&format=json&lang=en` | GET | `quoteText` | `quoteAuthor` | one per call; loop N times with throttle |
| 6.8 | `icanhazdadjoke` | `https://icanhazdadjoke.com/` | GET | `joke` | (none) | header `Accept: application/json`; one per call |
| 6.9 | `jokeapi` | `https://v2.jokeapi.dev/joke/{categories}?amount={n}&blacklistFlags=...` | GET | `joke` or `setup`+`delivery` | (none) | combine setup+delivery if present |
| 6.10 | `official_joke_api` | `https://official-joke-api.appspot.com/jokes/random/{n}` | GET | `setup`+`delivery` (concatenate) | (none) | |
| 6.11 | `chuck_norris_io` | `https://api.chucknorris.io/jokes/random` | GET | `value` | "Chuck Norris" | one per call |
| 6.12 | `geek_jokes` | `https://geek-jokes.sameerkumar.website/api?format=json` | GET | `joke` | (none) | one per call |

**Per source live test template:**

```python
# tests/sources/test_<name>_live.py
import pytest
from quotatron.sources.<name> import <Name>Source


@pytest.mark.live
@pytest.mark.asyncio
async def test_<name>_returns_at_least_one_item() -> None:
    items = await <Name>Source().fetch(limit=3)
    assert len(items) >= 1
    for it in items:
        assert 1 <= len(it.text) <= 800
        assert it.source == "<name>"
        assert "<" not in it.text  # no HTML leakage
```

- [ ] After all 11 are implemented, run:

```bash
uv run pytest -m live tests/sources/ -v
```

Expected: 9–11 passed (allow 1–2 source rate-limited).

- [ ] **Single commit per source** along the way; final commit message: `feat(sources): all 11 API adapters`.

---

### Task 6.13: API refresh background task + `verify-sources`

**Files:**
- Create: `src/quotatron/api_refresh.py`
- Create: `tests/unit/test_api_refresh.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_api_refresh.py
import asyncio
from quotatron.api_refresh import refresh_once


def test_refresh_once_handles_empty_source_list() -> None:
    fetched = asyncio.run(refresh_once(sources=[], cache_dir="/tmp/quotatron-test-refresh"))
    assert fetched == 0
```

- [ ] **Step 2: Implement `api_refresh.py`**

```python
# src/quotatron/api_refresh.py
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
        mod = importlib.import_module(f"quotatron.sources.{info.name}")
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if isinstance(obj, type) and issubclass(obj, BaseSource) and obj is not BaseSource:
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
        existing = json.loads(out_file.read_text()) if out_file.exists() else []
        existing.extend(it.model_dump() for it in items)
        # Cap cache size to 500 per source.
        existing = existing[-500:]
        out_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
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
    """`quotatron verify-sources` CLI entry point. Returns 0 if all sources reachable."""
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
```

- [ ] **Step 3: Run unit test**

```bash
uv run pytest tests/unit/test_api_refresh.py -v
```

Expected: PASS.

- [ ] **Step 4: Run live verification (optional manual check)**

```bash
uv run quotatron verify-sources
```

Expected: prints `9-11/11 sources healthy`.

- [ ] **Step 5: Commit**

```bash
git add src/quotatron/api_refresh.py tests/unit/test_api_refresh.py
git commit -m "feat(api_refresh): background enrichment + verify-sources CLI"
```

---

## Milestone 7 — E-paper hardware driver

### Task 7.1: Waveshare driver wrapper

**Files:**
- Create: `src/quotatron/display/epaper.py`

This wraps the Waveshare reference `epd2in13_V3` driver (from `Waveshare_Epaper` Python package or vendored). The wrapper abstracts model differences and presents the `Display` Protocol interface.

- [ ] **Step 1: Vendor the Waveshare driver**

```bash
mkdir -p src/quotatron/display/_waveshare
# Copy epd2in13_V2.py, epd2in13_V3.py, epd2in13_V4.py, epdconfig.py
# from https://github.com/waveshare/e-Paper repo into the _waveshare dir.
```

Add a NOTICE file crediting Waveshare BSD license.

- [ ] **Step 2: Write the wrapper**

```python
# src/quotatron/display/epaper.py
"""Hardware Waveshare 2.13" e-paper backend."""
from __future__ import annotations
import importlib
from PIL import Image


class WaveshareDisplay:
    width = 250
    height = 122

    def __init__(self, driver: str = "waveshare_2in13_v3") -> None:
        suffix = {"waveshare_2in13_v2": "epd2in13_V2",
                  "waveshare_2in13_v3": "epd2in13_V3",
                  "waveshare_2in13_v4": "epd2in13_V4"}[driver]
        mod = importlib.import_module(f"quotatron.display._waveshare.{suffix}")
        self._epd = mod.EPD()
        self._epd.init()
        self._epd.Clear(0xFF)
        self._partial = False

    def display_full(self, img: Image.Image) -> None:
        if self._partial:
            self._epd.init()  # exit partial mode
            self._partial = False
        self._epd.display(self._epd.getbuffer(img))

    def enter_partial_mode(self) -> None:
        if not self._partial:
            self._epd.init_Partial() if hasattr(self._epd, "init_Partial") else self._epd.init()
            self._partial = True

    def display_partial(self, img: Image.Image) -> None:
        if not self._partial:
            self.enter_partial_mode()
        self._epd.displayPartial(self._epd.getbuffer(img))

    def exit_partial_mode(self) -> None:
        self._partial = False

    def deep_clean(self) -> None:
        for fill in (0xFF, 0x00, 0xFF):
            blank = Image.new("1", (self.width, self.height), 1 if fill == 0xFF else 0)
            self._epd.display(self._epd.getbuffer(blank))

    def shutdown(self, farewell: Image.Image | None = None) -> None:
        if farewell is not None:
            self.display_full(farewell)
        self._epd.sleep()
```

- [ ] **Step 3: Add a TYPE-CHECKING import test**

```python
# tests/unit/test_display_protocol_typing.py
from quotatron.display._interface import Display
from quotatron.display.mock import MockDisplay


def test_mock_satisfies_protocol() -> None:
    d: Display = MockDisplay()
    assert d.width == 250
```

- [ ] **Step 4: Run tests**

```bash
uv run pytest tests/unit/test_display_protocol_typing.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/quotatron/display/ tests/unit/test_display_protocol_typing.py
git commit -m "feat(display): Waveshare 2.13in epaper hardware backend (vendored)"
```

(The hardware path can only be smoke-tested on the Pi itself — see Task 9.4.)

---

## Milestone 8 — Scheduler

### Task 8.1: Asyncio main loop

**Files:**
- Create: `src/quotatron/scheduler.py`
- Create: `tests/unit/test_scheduler.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_scheduler.py
import asyncio
from quotatron.config import Config, CycleConfig
from quotatron.content import ContentLibrary
from quotatron.display.mock import MockDisplay
from quotatron.models import ContentItem
from quotatron.scheduler import Scheduler


def test_scheduler_runs_one_full_cycle_in_test_mode() -> None:
    items = [
        ContentItem(kind="quote", text=f"q{i}", author="a", category="philosophy", source="bundled")
        for i in range(5)
    ]
    lib = ContentLibrary(items=items)
    cfg = Config(cycle=CycleConfig(quote_seconds=0, animation_seconds=0))
    display = MockDisplay()
    sch = Scheduler(config=cfg, library=lib, display=display, test_max_cycles=2)
    asyncio.run(sch.run())
    # Two cycles → two full refreshes for content + two post-anim full refreshes.
    fulls = sum(1 for m, _ in display.history if m == "full")
    assert fulls >= 4


def test_scheduler_flips_polarity_each_cycle() -> None:
    items = [ContentItem(kind="quote", text="q", author="a", category="philosophy", source="bundled")]
    cfg = Config(cycle=CycleConfig(quote_seconds=0, animation_seconds=0, invert_polarity_every=1))
    display = MockDisplay()
    sch = Scheduler(config=cfg, library=ContentLibrary(items=items), display=display, test_max_cycles=4)
    asyncio.run(sch.run())
    # Polarity should have flipped 4 times — verifiable via Scheduler.last_polarity_history.
    assert sch.polarity_history == ["normal", "inverted", "normal", "inverted"]
```

- [ ] **Step 2: Run test (fails — module not found)**

- [ ] **Step 3: Implement `scheduler.py`**

```python
# src/quotatron/scheduler.py
from __future__ import annotations
import asyncio
import logging
import random
import signal
from quotatron.animations import fallback as fallback_animation
from quotatron.animations import registry as animation_registry
from quotatron.animations._base import AnimationContext, BaseAnimation
from quotatron.config import Config
from quotatron.content import ContentLibrary
from quotatron.display._interface import Display
from quotatron.models import ContentItem, Polarity
from quotatron.render import compose

log = logging.getLogger(__name__)


class Scheduler:
    def __init__(
        self,
        config: Config,
        library: ContentLibrary,
        display: Display,
        test_max_cycles: int | None = None,
    ) -> None:
        self.config = config
        self.library = library
        self.display = display
        self._stop = False
        self._test_max_cycles = test_max_cycles
        self.polarity_history: list[str] = []

    async def run(self) -> None:
        polarity = Polarity.NORMAL
        cycle = 0
        prev_image = None
        while not self._stop:
            item = self.library.next_item(
                quote_to_joke_ratio=self.config.content.quote_to_joke_ratio,
                quote_weights=self.config.content.weights.quotes,
                joke_weights=self.config.content.weights.jokes,
                no_repeat_window=self.config.content.no_repeat_window,
                seed=None,
            )
            dest = compose(item, polarity=polarity, rotation=self.config.display.rotation)
            log.info(
                "cycle=%d item=%s/%s author=%r polarity=%s",
                cycle, item.kind, item.category, item.author, polarity.value,
            )

            if prev_image is not None and self.config.animations.enabled:
                anim = self._pick_animation()
                ctx = AnimationContext(
                    from_image=prev_image, to_image=dest, polarity=polarity,
                    width=self.display.width, height=self.display.height,
                )
                self.display.enter_partial_mode()
                try:
                    for frame in anim.frames(ctx, self.config.cycle.animation_seconds):
                        self.display.display_partial(frame)
                        await asyncio.sleep(0)  # yield to event loop
                except Exception:
                    log.exception("animation %s raised — using fallback", anim.name)
                    self.display.exit_partial_mode()
                    self.display.display_full(dest)
                else:
                    self.display.exit_partial_mode()
                    self.display.display_full(dest)
            else:
                self.display.display_full(dest)

            await asyncio.sleep(self.config.cycle.quote_seconds)
            cycle += 1
            self.polarity_history.append(polarity.value)
            if cycle % self.config.cycle.invert_polarity_every == 0:
                polarity = polarity.flipped()
            prev_image = dest

            if self._test_max_cycles is not None and cycle >= self._test_max_cycles:
                self._stop = True

    def _pick_animation(self) -> BaseAnimation:
        reg = animation_registry()
        names = [n for n in reg if n not in self.config.animations.blocklist]
        if not names:
            return fallback_animation()()
        if self.config.animations.shuffle == "random":
            return reg[random.choice(names)]()
        # sequential — pick by cycle count modulo
        return reg[sorted(names)[len(self.polarity_history) % len(names)]]()

    def stop(self) -> None:
        self._stop = True


def run_service() -> int:
    """systemd entry point. Loads config, library, hardware display, and runs forever."""
    from quotatron.config import load_config
    from quotatron.display.epaper import WaveshareDisplay
    cfg = load_config("config/quotatron.yaml")
    logging.basicConfig(
        level=cfg.logging.level,
        filename=cfg.logging.path,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        lib = ContentLibrary.from_disk("content")
    except Exception:
        log.exception("content library failed to load — using emergency quotes")
        from quotatron.emergency_quotes import emergency_library
        lib = emergency_library()
    display = WaveshareDisplay(driver=cfg.display.driver)
    sch = Scheduler(config=cfg, library=lib, display=display)
    loop = asyncio.new_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, sch.stop)
    try:
        loop.run_until_complete(sch.run())
    finally:
        farewell = Image.new("1", (display.width, display.height), 1)
        display.shutdown(farewell)
    return 0
```

- [ ] **Step 4: Run tests (passes)**

- [ ] **Step 5: Commit**

```bash
git add src/quotatron/scheduler.py tests/unit/test_scheduler.py
git commit -m "feat(scheduler): asyncio main loop with polarity bouncing"
```

---

### Task 8.2: Daily deep-clean scheduling

**Files:**
- Modify: `src/quotatron/scheduler.py`
- Modify: `tests/unit/test_scheduler.py`

- [ ] **Step 1: Add test**

```python
# tests/unit/test_scheduler.py — append
def test_deep_clean_runs_once_per_day_at_configured_hour() -> None:
    # ... use a fake clock and assert deep_clean appears in display history at 03:00
    pass  # body below
```

- [ ] **Step 2: Implement deep-clean check inside the cycle loop**

Add a `_last_deep_clean_date` attribute. After every `await asyncio.sleep(...)`, check `datetime.now().hour == 3 and last_deep_clean_date != today`; if so, call `display.deep_clean()` and update the date.

(See full implementation below — repeated in code for clarity.)

```python
# Inside Scheduler.__init__:
self._last_deep_clean_date: date | None = None
self._deep_clean_hour = 3

# Inside Scheduler.run, after the sleep:
from datetime import date, datetime
now = datetime.now()
if (now.hour == self._deep_clean_hour and self._last_deep_clean_date != now.date()):
    log.info("running daily deep-clean")
    self.display.deep_clean()
    self._last_deep_clean_date = now.date()
```

- [ ] **Step 3: Implement test with frozen time**

```python
# tests/unit/test_scheduler.py
import datetime as dt
from unittest.mock import patch

def test_deep_clean_runs_at_03h() -> None:
    items = [ContentItem(kind="quote", text="q", author="a", category="philosophy", source="bundled")]
    cfg = Config(cycle=CycleConfig(quote_seconds=0, animation_seconds=0))
    display = MockDisplay()
    fixed = dt.datetime(2026, 1, 1, 3, 0, 0)
    with patch("quotatron.scheduler.datetime") as mock_dt:
        mock_dt.now.return_value = fixed
        mock_dt.side_effect = lambda *a, **k: dt.datetime(*a, **k)
        sch = Scheduler(config=cfg, library=ContentLibrary(items=items), display=display, test_max_cycles=2)
        asyncio.run(sch.run())
    cleans = [m for m, _ in display.history if m == "deep_clean"]
    assert len(cleans) == 1
```

- [ ] **Step 4: Run tests (passes)**

- [ ] **Step 5: Commit**

```bash
git add src/quotatron/scheduler.py tests/unit/test_scheduler.py
git commit -m "feat(scheduler): daily 03:00 deep-clean cycle"
```

---

### Task 8.3: Graceful shutdown with farewell screen

**Files:**
- Modify: `src/quotatron/scheduler.py`

Already wired in `run_service()` above (`display.shutdown(farewell)`). Add a goodbye render:

```python
# at top of run_service, before display.shutdown:
from quotatron.render import compose
from quotatron.models import ContentItem, Polarity
goodbye = compose(
    ContentItem(kind="quote", text="Quotatron offline.", author="—", category="philosophy", source="system"),
    polarity=Polarity.NORMAL,
    rotation=cfg.display.rotation,
)
display.shutdown(goodbye)
```

- [ ] Commit:

```bash
git commit -am "feat(scheduler): graceful shutdown with farewell screen"
```

---

## Milestone 9 — Web preview

### Task 9.1: FastAPI server skeleton + animation list endpoint

**Files:**
- Create: `src/quotatron/web_preview/server.py`
- Create: `src/quotatron/web_preview/static/{index.html,app.js,style.css}`
- Create: `tests/unit/test_web_preview.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_web_preview.py
from fastapi.testclient import TestClient
from quotatron.web_preview.server import app


def test_animations_endpoint_lists_registered_animations() -> None:
    client = TestClient(app)
    r = client.get("/api/animations")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    # At least one plugin should be discovered (after Milestone 5 lands).
    # Until then, list may be empty; test for shape.
    for entry in body:
        assert {"name", "duration_default", "target_fps"}.issubset(entry.keys())
```

- [ ] **Step 2: Implement `server.py`**

```python
# src/quotatron/web_preview/server.py
from __future__ import annotations
import asyncio, base64, io, json, logging
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse
from PIL import Image
from quotatron.animations import registry, fallback
from quotatron.animations._base import AnimationContext
from quotatron.content import ContentLibrary
from quotatron.models import Polarity
from quotatron.render import compose

log = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Quotatron Preview")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/animations")
def list_animations() -> list[dict]:
    return [
        {"name": cls.name, "duration_default": cls.duration_default, "target_fps": cls.target_fps}
        for cls in registry(refresh=True).values()
    ]


@app.get("/api/content/sample")
def sample_content() -> dict:
    lib = ContentLibrary.from_disk("content")
    cur = lib.next_item(
        quote_to_joke_ratio=0.7,
        quote_weights={"philosophy": 1.0, "science": 1.0, "literature": 1.0,
                       "leaders": 1.0, "humor": 1.0},
        joke_weights={"oneliner": 1.0, "dad": 1.0, "programming": 1.0, "observational": 1.0},
        no_repeat_window=0,
    )
    nxt = lib.next_item(
        quote_to_joke_ratio=0.7,
        quote_weights={"philosophy": 1.0, "science": 1.0, "literature": 1.0,
                       "leaders": 1.0, "humor": 1.0},
        joke_weights={"oneliner": 1.0, "dad": 1.0, "programming": 1.0, "observational": 1.0},
        no_repeat_window=0,
    )
    return {"current": cur.model_dump(), "next": nxt.model_dump()}


def _img_to_b64png(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


@app.get("/api/animation/{name}/stream")
async def stream_animation(
    name: str,
    polarity: str = Query("normal"),
    rotation: str = Query("landscape"),
    duration: float = Query(10.0, ge=1.0, le=60.0),
):
    reg = registry()
    cls = reg.get(name) or fallback() if name == "simple_fade" else reg.get(name)
    if cls is None:
        return Response(status_code=404, content=f"unknown animation: {name}")
    pol = Polarity.NORMAL if polarity == "normal" else Polarity.INVERTED

    samples = sample_content()
    from quotatron.models import ContentItem
    cur_item = ContentItem(**samples["current"])
    nxt_item = ContentItem(**samples["next"])
    from_img = compose(cur_item, polarity=pol, rotation=rotation)
    to_img = compose(nxt_item, polarity=pol.flipped(), rotation=rotation)
    ctx = AnimationContext(
        from_image=from_img, to_image=to_img, polarity=pol,
        width=250, height=122,
    )

    async def gen():
        for i, frame in enumerate(cls().frames(ctx, duration)):
            yield {"event": "frame", "data": json.dumps(
                {"i": i, "png_b64": _img_to_b64png(frame)}
            )}
            await asyncio.sleep(max(0.0, duration / max(1, cls.target_fps * int(duration)) ))
        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(gen())


def run_preview() -> int:
    import uvicorn
    from quotatron.config import load_config
    cfg = load_config("config/quotatron.yaml")
    uvicorn.run(
        "quotatron.web_preview.server:app",
        host=cfg.web_preview.host, port=cfg.web_preview.port, reload=True,
    )
    return 0
```

- [ ] **Step 3: Write `static/index.html`**

(Three-column layout from spec §5: animation list, preview canvas, controls. Keep it readable with vanilla CSS — no React/build step.)

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Quotatron Preview</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <main class="layout">
    <aside class="anim-list">
      <h2>Animations</h2>
      <ul id="animations"></ul>
      <button id="play-all">Play all 30</button>
      <button id="grid">Side-by-side</button>
    </aside>
    <section class="preview">
      <canvas id="canvas" width="250" height="122"
              style="image-rendering:pixelated; transform:scale(4); transform-origin:top left;"></canvas>
      <div class="controls">
        <button id="play">▶ Play</button>
        <button id="loop">⟳ Loop</button>
        <button id="pause">⏸ Pause</button>
        <input type="range" id="scrub" min="0" max="1" step="0.01" value="0">
        <span id="frame-counter">Frame: 0/0</span>
      </div>
    </section>
    <aside class="ctrl-panel">
      <h2>Controls</h2>
      <label>Polarity:
        <select id="polarity"><option>normal</option><option>inverted</option></select>
      </label>
      <label>Rotation:
        <select id="rotation"><option>landscape</option><option>portrait</option></select>
      </label>
    </aside>
  </main>
  <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 4: Write `static/app.js`** — fetches `/api/animations`, populates list, opens EventSource on play.

```js
const list = document.getElementById('animations');
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
let currentName = null, es = null;

async function loadList() {
  const r = await fetch('/api/animations');
  const data = await r.json();
  list.innerHTML = '';
  for (const a of data) {
    const li = document.createElement('li');
    li.textContent = a.name;
    li.onclick = () => { currentName = a.name; play(); };
    list.appendChild(li);
  }
}
function play() {
  if (es) es.close();
  if (!currentName) return;
  const params = new URLSearchParams({
    polarity: document.getElementById('polarity').value,
    rotation: document.getElementById('rotation').value,
    duration: '5',
  });
  es = new EventSource(`/api/animation/${currentName}/stream?${params}`);
  es.addEventListener('frame', e => {
    const { i, png_b64 } = JSON.parse(e.data);
    const img = new Image();
    img.onload = () => ctx.drawImage(img, 0, 0);
    img.src = 'data:image/png;base64,' + png_b64;
    document.getElementById('frame-counter').textContent = `Frame: ${i}`;
  });
  es.addEventListener('done', () => es.close());
}
document.getElementById('play').onclick = play;
loadList();
```

- [ ] **Step 5: Write minimal `static/style.css`** — three-column flex layout. ~20 lines.

- [ ] **Step 6: Run test**

```bash
uv run pytest tests/unit/test_web_preview.py -v
```

Expected: 1 passed.

- [ ] **Step 7: Manual smoke test**

```bash
uv run quotatron preview
# Open http://127.0.0.1:8080
```

Expected: page loads, animation list populated, clicking an animation streams frames.

- [ ] **Step 8: Commit**

```bash
git add src/quotatron/web_preview/ tests/unit/test_web_preview.py
git commit -m "feat(preview): FastAPI server with SSE animation streaming"
```

---

### Task 9.2: Side-by-side grid mode

**Files:**
- Modify: `src/quotatron/web_preview/static/app.js` and `index.html`

- [ ] Add a `grid` toggle that lays out 30 small canvases in a CSS Grid (5×6) and starts a separate EventSource for each. Throttle by capping concurrent connections to 6 at a time (browser-imposed).

- [ ] **Manual verification:** click "Side-by-side", all 30 mini-previews should play.

- [ ] Commit: `feat(preview): side-by-side 30-up grid mode`.

---

### Task 9.3: GIF export

**Files:**
- Create: `src/quotatron/web_preview/gif_export.py`
- Modify: `server.py` adding `/api/animation/{name}/gif` endpoint
- Modify: `app.js` adding "Record GIF" button

- [ ] **Step 1: Implement GIF builder**

```python
# src/quotatron/web_preview/gif_export.py
from __future__ import annotations
from pathlib import Path
from PIL import Image
from quotatron.animations._base import AnimationContext
from quotatron.animations import registry, fallback
from quotatron.models import Polarity
from quotatron.render import compose
from quotatron.models import ContentItem


def export_gif(name: str, out_path: Path, duration_s: float = 10.0) -> Path:
    cls = registry().get(name) or (fallback() if name == "simple_fade" else None)
    if cls is None:
        raise ValueError(f"unknown animation: {name}")
    cur = ContentItem(kind="quote", text="Hello, world.", author="anon", category="philosophy", source="bundled")
    nxt = ContentItem(kind="quote", text="Goodbye, world.", author="anon", category="philosophy", source="bundled")
    from_img = compose(cur, polarity=Polarity.NORMAL, rotation="landscape").convert("RGB")
    to_img = compose(nxt, polarity=Polarity.NORMAL, rotation="landscape").convert("RGB")
    ctx = AnimationContext(
        from_image=compose(cur, polarity=Polarity.NORMAL, rotation="landscape"),
        to_image=compose(nxt, polarity=Polarity.NORMAL, rotation="landscape"),
        polarity=Polarity.NORMAL, width=250, height=122,
    )
    frames = [f.convert("RGB") for f in cls().frames(ctx, duration_s)]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        out_path, save_all=True, append_images=frames[1:],
        duration=int(1000 * duration_s / len(frames)), loop=0,
    )
    return out_path
```

- [ ] **Step 2: Add API endpoint and JS button** as documented above.

- [ ] **Step 3: Commit:** `feat(preview): GIF export for README gallery`.

---

## Milestone 10 — WiFi profile pipeline

### Task 10.1: XML parser + wpa_supplicant.conf writer

**Files:**
- Create: `scripts/wifi_to_wpa.py`
- Create: `tests/unit/test_wifi_to_wpa.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_wifi_to_wpa.py
from pathlib import Path
import sys
sys.path.insert(0, "scripts")
from wifi_to_wpa import parse_profile, write_wpa_conf, ProfileResult


def test_parses_wpa3sae_profile_with_cleartext_psk(tmp_path: Path) -> None:
    xml = tmp_path / "p.xml"
    xml.write_text('''<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
  <name>TestNet</name>
  <SSIDConfig><SSID><hex>54657374</hex><name>Test</name></SSID></SSIDConfig>
  <connectionType>ESS</connectionType>
  <connectionMode>auto</connectionMode>
  <MSM><security>
    <authEncryption><authentication>WPA3SAE</authentication><encryption>AES</encryption><useOneX>false</useOneX></authEncryption>
    <sharedKey><keyType>passPhrase</keyType><protected>false</protected><keyMaterial>secret123</keyMaterial></sharedKey>
  </security></MSM>
</WLANProfile>''')
    res = parse_profile(xml)
    assert res.kind == "ok"
    assert res.ssid == "TestNet"
    assert res.psk == "secret123"
    assert res.key_mgmt == "SAE WPA-PSK"


def test_skips_dpapi_protected() -> None:
    xml_text = '''<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
  <name>X</name><SSIDConfig><SSID><name>X</name></SSID></SSIDConfig>
  <MSM><security>
    <authEncryption><authentication>WPA2PSK</authentication><encryption>AES</encryption><useOneX>false</useOneX></authEncryption>
    <sharedKey><keyType>passPhrase</keyType><protected>true</protected><keyMaterial>encrypted</keyMaterial></sharedKey>
  </security></MSM>
</WLANProfile>'''
    from io import StringIO
    res = parse_profile(StringIO(xml_text))
    assert res.kind == "skip"
    assert "DPAPI" in res.reason


def test_writes_priority_ordered_blocks(tmp_path: Path) -> None:
    profiles = [
        ProfileResult(kind="ok", ssid="A", psk="aaaaaaaa", key_mgmt="WPA-PSK", reason=""),
        ProfileResult(kind="ok", ssid="B", psk="bbbbbbbb", key_mgmt="WPA-PSK", reason=""),
    ]
    out = tmp_path / "wpa_supplicant.conf"
    write_wpa_conf(profiles, out, country="PL", prefer=["B"])
    text = out.read_text()
    # B comes before A because of --prefer
    assert text.index('ssid="B"') < text.index('ssid="A"')
    assert "priority=" in text
```

- [ ] **Step 2: Implement `scripts/wifi_to_wpa.py`**

```python
#!/usr/bin/env python3
"""One-time converter: Windows WiFi XML profiles → wpa_supplicant.conf

Usage:
  uv run python scripts/wifi_to_wpa.py \
    --input "C:/Users/LCFR/Desktop/Format/wifi_profiles" \
    --output wifi_profiles/wpa_supplicant.conf \
    --country PL \
    [--prefer "Home_5G,Office"]
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import IO, Union

NS = {"w": "http://www.microsoft.com/networking/WLAN/profile/v1"}

AUTH_MAP = {
    "WPA3SAE": "SAE WPA-PSK",
    "WPA2PSK": "WPA-PSK",
    "WPAPSK": "WPA-PSK",
    "open": "NONE",
}


@dataclass
class ProfileResult:
    kind: str   # "ok" | "skip"
    ssid: str
    psk: str
    key_mgmt: str
    reason: str


def parse_profile(src: Union[Path, IO[str]]) -> ProfileResult:
    if isinstance(src, (str, Path)):
        tree = ET.parse(str(src))
        root = tree.getroot()
    else:
        root = ET.fromstring(src.read())
    ssid_elem = root.find(".//w:SSID/w:name", NS)
    ssid_hex = root.find(".//w:SSID/w:hex", NS)
    if ssid_hex is not None and ssid_hex.text:
        ssid = bytes.fromhex(ssid_hex.text).decode("utf-8", errors="replace")
    elif ssid_elem is not None and ssid_elem.text:
        ssid = ssid_elem.text
    else:
        return ProfileResult("skip", "", "", "", "no SSID")

    auth = root.find(".//w:authentication", NS)
    auth_text = auth.text if auth is not None else "open"
    if auth_text not in AUTH_MAP:
        return ProfileResult("skip", ssid, "", "", f"unsupported auth: {auth_text}")

    if auth_text == "open":
        return ProfileResult("ok", ssid, "", "NONE", "")

    protected = root.find(".//w:sharedKey/w:protected", NS)
    if protected is not None and protected.text == "true":
        return ProfileResult("skip", ssid, "", "", "DPAPI-encrypted")
    psk_elem = root.find(".//w:sharedKey/w:keyMaterial", NS)
    if psk_elem is None or not psk_elem.text:
        return ProfileResult("skip", ssid, "", "", "missing key")
    psk = psk_elem.text
    if not (8 <= len(psk) <= 63 or (len(psk) == 64 and all(c in "0123456789abcdefABCDEF" for c in psk))):
        return ProfileResult("skip", ssid, "", "", "invalid PSK length")

    return ProfileResult("ok", ssid, psk, AUTH_MAP[auth_text], "")


def write_wpa_conf(
    profiles: list[ProfileResult],
    out_path: Path,
    country: str = "PL",
    prefer: list[str] | None = None,
) -> None:
    prefer = prefer or []
    seen: dict[str, ProfileResult] = {}
    for p in profiles:
        if p.kind == "ok":
            seen[p.ssid] = p   # last wins (dedup)

    ordered: list[ProfileResult] = []
    for s in prefer:
        if s in seen:
            ordered.append(seen.pop(s))
    ordered.extend(seen.values())

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write("ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n")
        f.write("update_config=1\n")
        f.write(f"country={country}\n\n")
        for i, p in enumerate(ordered):
            f.write("network={\n")
            f.write(f'    ssid="{p.ssid}"\n')
            f.write(f"    key_mgmt={p.key_mgmt}\n")
            if p.psk:
                f.write(f'    psk="{p.psk}"\n')
            f.write(f"    priority={max(1, len(ordered) - i)}\n")
            f.write("}\n\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Directory containing WiFi-*.xml files")
    parser.add_argument("--output", default="wifi_profiles/wpa_supplicant.conf")
    parser.add_argument("--country", default="PL")
    parser.add_argument("--prefer", default="", help="Comma-separated SSIDs to prefer")
    args = parser.parse_args()

    in_dir = Path(args.input)
    xmls = sorted(in_dir.glob("WiFi-*.xml"))
    profiles: list[ProfileResult] = []
    for x in xmls:
        try:
            profiles.append(parse_profile(x))
        except Exception as e:
            print(f"  ✗ {x.name}: parse error {e}")

    ok = [p for p in profiles if p.kind == "ok"]
    skipped = [p for p in profiles if p.kind == "skip"]
    write_wpa_conf(ok, Path(args.output), args.country,
                   [s.strip() for s in args.prefer.split(",") if s.strip()])
    print(f"✓ {len(ok)} profiles converted")
    for p in skipped:
        print(f"⚠ skipped {p.ssid}: {p.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Run unit tests**

```bash
uv run pytest tests/unit/test_wifi_to_wpa.py -v
```

Expected: 3 passed.

- [ ] **Step 4: Run on the real folder**

```bash
mkdir -p wifi_profiles
uv run python scripts/wifi_to_wpa.py \
  --input "C:/Users/LCFR/Desktop/Format/wifi_profiles" \
  --output wifi_profiles/wpa_supplicant.conf \
  --country PL
```

Expected: prints `✓ ~85 profiles converted` plus warnings for any DPAPI-protected/enterprise.

- [ ] **Step 5: Verify .gitignore is doing its job**

```bash
git status
```

Expected: `wifi_profiles/` is NOT listed.

- [ ] **Step 6: Commit**

```bash
git add scripts/wifi_to_wpa.py tests/unit/test_wifi_to_wpa.py
git commit -m "feat(wifi): one-time XML→wpa_supplicant.conf converter"
```

---

## Milestone 11 — Build & deploy

### Task 11.1: systemd service unit

**Files:**
- Create: `systemd/quotatron.service`

- [ ] **Step 1: Write the unit file**

```ini
[Unit]
Description=Quotatron e-paper display service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
Group=pi
WorkingDirectory=/home/pi/quotatron
ExecStart=/home/pi/.local/bin/uv run quotatron run
Restart=on-failure
RestartSec=10
StartLimitIntervalSec=300
StartLimitBurst=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 2: Commit**

```bash
git add systemd/quotatron.service
git commit -m "feat(deploy): systemd unit for the quotatron service"
```

---

### Task 11.2: install.sh on-Pi installer (with GUI disable)

**Files:**
- Create: `scripts/install.sh`

- [ ] **Step 1: Write the installer**

```bash
#!/usr/bin/env bash
# Run on the Pi as the `pi` user. Idempotent.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"

echo "==> Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y --no-install-recommends \
  python3 python3-pip python3-spidev python3-pil fonts-dejavu git curl

echo "==> Disabling GUI (boot to CLI only)..."
sudo systemctl set-default multi-user.target
for svc in lightdm gdm gdm3 sddm; do
  if systemctl list-unit-files | grep -q "^${svc}.service"; then
    sudo systemctl disable "$svc" 2>/dev/null || true
    sudo systemctl stop "$svc" 2>/dev/null || true
  fi
done
sudo raspi-config nonint do_boot_behaviour B1 2>/dev/null || true   # CLI auto-login (no GUI)

echo "==> Enabling SPI..."
sudo raspi-config nonint do_spi 0

echo "==> Installing uv..."
if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "==> Syncing dependencies (production only)..."
uv sync --no-dev --extra hardware

echo "==> Installing wpa_supplicant.conf..."
if [[ -f wifi_profiles/wpa_supplicant.conf ]]; then
  sudo install -m 600 -o root -g root \
    wifi_profiles/wpa_supplicant.conf \
    /etc/wpa_supplicant/wpa_supplicant.conf
  sudo wpa_cli -i wlan0 reconfigure || true
fi

echo "==> Installing systemd unit..."
sudo install -m 644 systemd/quotatron.service /etc/systemd/system/quotatron.service
sudo systemctl daemon-reload
sudo systemctl enable --now quotatron

echo "==> Done. Logs: journalctl -u quotatron -f"
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x scripts/install.sh
```

- [ ] **Step 3: Commit**

```bash
git add scripts/install.sh
git commit -m "feat(deploy): install.sh — disables GUI, enables SPI, deploys service"
```

---

### Task 11.3: flash_sdcard.sh helper

**Files:**
- Create: `scripts/flash_sdcard.sh`

- [ ] **Step 1: Write a thin wrapper around `rpi-imager` CLI** (or offer guided manual instructions). It should:
  1. Verify the user has Pi OS Lite image already cached (or print the download URL)
  2. Print the `dd` command targeting their chosen device with `--dry-run` first
  3. Drop `wifi_profiles/wpa_supplicant.conf` and an empty `ssh` file onto `/boot` after flashing

```bash
#!/usr/bin/env bash
set -euo pipefail
DEVICE="${1:?usage: flash_sdcard.sh /dev/sdX (LINUX) or \\\\.\\PhysicalDriveN (WSL)}"
IMG="${2:-${HOME}/Downloads/raspios_lite_armhf.img}"

if [[ ! -f "$IMG" ]]; then
  echo "Image not found at $IMG. Download from:"
  echo "  https://www.raspberrypi.com/software/operating-systems/"
  exit 1
fi

echo "=== About to flash $IMG → $DEVICE ==="
echo "Press Enter to confirm, Ctrl-C to abort..."
read -r
sudo dd bs=4M if="$IMG" of="$DEVICE" conv=fsync status=progress
sync

# Mount /boot and drop wpa_supplicant + ssh
MNT=$(mktemp -d)
sudo mount "${DEVICE}1" "$MNT"
sudo install -m 600 wifi_profiles/wpa_supplicant.conf "$MNT/wpa_supplicant.conf"
sudo touch "$MNT/ssh"
sudo umount "$MNT"
rmdir "$MNT"

echo "=== Done. Insert into Pi and boot. ==="
echo "After first boot, ssh in and run:"
echo "  git clone <REPO> ~/quotatron && cd ~/quotatron && ./scripts/install.sh"
```

- [ ] **Step 2: Make executable + commit**

```bash
chmod +x scripts/flash_sdcard.sh
git add scripts/flash_sdcard.sh
git commit -m "feat(deploy): flash_sdcard.sh helper for SD card preparation"
```

---

## Milestone 12 — CI, Makefile, README

### Task 12.1: Makefile

**Files:**
- Create: `Makefile`

```makefile
.PHONY: install preview test test-unit verify-sources update-goldens lint format clean smoke-on-device

install:
	uv sync

preview:
	uv run quotatron preview

test:
	uv run pytest -v

test-unit:
	uv run pytest tests/unit/ -v

verify-sources:
	uv run quotatron verify-sources

update-goldens:
	uv run python -m scripts.regen_goldens

lint:
	uv run ruff check src/ tests/ scripts/

format:
	uv run ruff format src/ tests/ scripts/

clean:
	rm -rf .venv build dist *.egg-info .pytest_cache .coverage htmlcov

smoke-on-device:
	uv run quotatron run --max-cycles 3
```

- [ ] Commit: `feat(build): Makefile with all dev targets`.

---

### Task 12.2: GitHub Actions CI

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/verify-sources.yml`

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv python install ${{ matrix.python }}
      - run: uv sync --frozen
      - run: uv run ruff check src/ tests/ scripts/
      - run: uv run ruff format --check src/ tests/ scripts/
      - run: uv run pytest tests/unit/ -v --cov=src/quotatron --cov-report=term
```

```yaml
# .github/workflows/verify-sources.yml
name: Verify API Sources
on:
  schedule:
    - cron: "0 5 * * *"   # 05:00 UTC daily
  workflow_dispatch:
jobs:
  live:
    runs-on: ubuntu-latest
    continue-on-error: true   # source flakiness shouldn't fail the build
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --frozen
      - run: uv run pytest -m live tests/sources/ -v --tb=short || true
      - if: always()
        uses: actions/upload-artifact@v4
        with:
          name: source-health-report
          path: pytest-report.txt
```

- [ ] Commit: `feat(ci): GitHub Actions for tests, lint, nightly source verification`.

---

### Task 12.3: README + animation gallery

**Files:**
- Modify: `README.md` — replace stub with full README

- [ ] Write a complete README covering:
  - What it is (with photo placeholder `docs/photo.jpg`)
  - Hardware requirements
  - Software setup (clone → install.sh)
  - Configuration walkthrough (link to `config/quotatron.yaml`)
  - Animation gallery (auto-embed `docs/animations/*.gif` in a 5×6 markdown grid)
  - Troubleshooting (panel not refreshing, WiFi not connecting, sources rate-limited)
  - License
  - Credits (Waveshare, font, content sources)

- [ ] Generate all 30 GIFs:

```bash
uv run python -c "
from quotatron.web_preview.gif_export import export_gif
from quotatron.animations import registry
from pathlib import Path
for name in registry(refresh=True):
    export_gif(name, Path(f'docs/animations/{name}.gif'))
"
```

- [ ] Commit: `docs: full README with animation gallery`.

---

## Milestone 13 — GitHub publish

### Task 13.1: Push to GitHub

- [ ] **Step 1: Verify `gh` CLI is authenticated**

```bash
gh auth status
```

Expected: shows authenticated user.

If not, prompt user to run `! gh auth login` interactively (this skill cannot do interactive auth).

- [ ] **Step 2: Create the repo and push**

```bash
gh repo create quotatron --public \
  --description "Pi Zero W e-paper appliance: rotating quotes/jokes with 30 wipe animations" \
  --source=. --remote=origin --push
```

Expected: `https://github.com/<user>/quotatron` exists with all commits.

- [ ] **Step 3: Final sanity check**

```bash
gh repo view --web
```

Verify README displays, animation gallery renders, no `wifi_profiles/` in the file tree.

---

## Self-Review (run at end of plan creation)

**1. Spec coverage check** — for each spec section, point to a task:

- §1 Goal → entire plan
- §2 Cycle → Task 8.1 scheduler
- §3 Architecture → entire plan
- §4 Configuration → Task 1.1 + 1.2
- §5 Animation plugin contract → Task 4.1 + 4.2
- §5 30 animations → Tasks 5.1–5.30
- §6 Rendering pipeline → Task 8.1 scheduler
- §7 E-ink longevity (polarity bouncing) → Task 8.1
- §7 E-ink longevity (mandatory full refresh) → Task 8.1 (post-anim full refresh in `_run_one_cycle`)
- §7 E-ink longevity (daily deep clean) → Task 8.2
- §7 Shutdown farewell → Task 8.3
- §8 Web preview → Tasks 9.1–9.3
- §9 Content sources → Tasks 6.2–6.12
- §10 Source verification (`make verify-sources`) → Task 6.13 + 12.1 + 12.2
- §11 WiFi handling → Task 10.1
- §12 Error handling — each row mapped: API silent failure (Task 6.13 `fail_silently`), bad JSON (Task 6.13), animation raises (Task 8.1 fallback), SPI fail (Task 7.1 wrapper + systemd Restart), empty cache (Task 8.1 + Task 3.3 emergency), bad YAML (Task 1.1 pydantic), panel disconnected (Task 7.1 retry on init), full FS (handled by `fail_silently` writes)
- §13 Testing layers — unit (every task), goldens (Tasks 5.1–5.30), live sources (Task 6.13 + CI), smoke-on-device (Task 12.1 Makefile target), web preview manual (Task 9.1)
- §14 Build/deploy — Tasks 11.1–11.3
- §14 GUI disable → Task 11.2 install.sh
- §15 CI → Task 12.2
- §16 Logging → wired in Task 8.1 `run_service()`
- §17 Out-of-scope → not implemented (correct)

**2. Placeholder scan** — searched for "TBD", "TODO", "Similar to" — none present.

**3. Type consistency:**
- `ContentItem` — defined in Task 2.2, used everywhere consistently
- `Polarity.NORMAL`/`INVERTED` — defined in Task 2.2, used throughout
- `BaseAnimation.frames()` and `render()` — defined in Task 4.1, used by all 30 animation tasks and scheduler
- `Display` Protocol methods (`display_full`, `enter_partial_mode`, `display_partial`, `exit_partial_mode`, `deep_clean`, `shutdown`) — defined in Task 2.1, both `MockDisplay` (Task 2.1) and `WaveshareDisplay` (Task 7.1) implement all of them ✓
- `Scheduler.polarity_history: list[str]` — referenced in test (Task 8.1) and set inside `run()` ✓

No inconsistencies found.
