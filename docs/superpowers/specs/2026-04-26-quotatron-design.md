# Quotatron — Design Spec

**Date:** 2026-04-26
**Status:** Draft for user review
**Hardware:** Raspberry Pi Zero W 1.1 + Waveshare 2.13" e-paper HAT (V2/V3/V4)

## 1. Goal

A small Pi Zero W appliance that displays a rotating feed of famous-people quotes
and clean jokes on a 2.13" e-paper HAT. Each minute it shows one item for ~50 s,
then plays one of 30 randomly selected 10 s "wipe" animations as a transition
into the next item. Pixel polarity bounces each cycle to extend e-ink lifetime.

## 2. Cycle (per minute)

```
[full refresh: render quote/joke]  →  hold 50 s  →  partial-refresh wipe (10 s)  →  next minute
```

A clean full-refresh after every animation prevents partial-refresh ghosting.
A daily "deep clean" (3× black/white inversions) runs at 03:00 to fully reset
panel state.

## 3. Architecture — modular monolith with plugin animations

One Python package, one systemd service, one asyncio main loop. Animations are
auto-discovered Python modules that all share a `BaseAnimation` contract.

```
quotatron/
├── pyproject.toml                  uv-managed
├── README.md
├── LICENSE                         MIT
├── .gitignore                      excludes wifi_profiles/, .venv, __pycache__
├── config/quotatron.yaml           runtime config (committed defaults)
├── content/
│   ├── quotes/{philosophy,science,literature,leaders,humor}.json
│   └── jokes/{oneliner,dad,programming,observational}.json
├── src/quotatron/
│   ├── __main__.py                 `python -m quotatron`
│   ├── config.py                   pydantic-validated YAML loader
│   ├── content.py                  weighted picker with no-repeat window
│   ├── api_refresh.py              async background task that grows local cache
│   ├── sources/<name>.py           one adapter per API source (11 sources total)
│   ├── display/
│   │   ├── epaper.py               Waveshare driver wrapper
│   │   └── mock.py                 in-memory framebuffer (preview + tests)
│   ├── render.py                   text layout, font, polarity, framing
│   ├── animations/
│   │   ├── __init__.py             auto-discovery
│   │   ├── _base.py                BaseAnimation, AnimationContext
│   │   └── *.py                    one file per animation (30 plugins)
│   ├── scheduler.py                50 s/10 s asyncio loop
│   └── web_preview/
│       ├── server.py               FastAPI app
│       └── static/                 browser UI
├── scripts/
│   ├── install.sh                  on-Pi installer
│   ├── flash_sdcard.sh             local SD-card flasher
│   └── wifi_to_wpa.py              one-time XML → wpa_supplicant.conf converter
├── systemd/quotatron.service
├── tests/
│   ├── unit/
│   ├── goldens/                    PNGs for visual regression
│   └── sources/                    live API integration tests
├── docs/
│   ├── superpowers/specs/          this spec
│   └── animations/                 auto-generated GIFs of each animation
└── wifi_profiles/                  GITIGNORED — contains only the converted output
    └── wpa_supplicant.conf         baked into the SD-card image at flash time
```

## 4. Configuration (`config/quotatron.yaml`)

```yaml
display:
  rotation: landscape          # landscape | portrait
  driver: waveshare_2in13_v3   # supports v2/v3/v4
  full_refresh_every: 1        # cycles between full refreshes (1 = every cycle)

cycle:
  quote_seconds: 50
  animation_seconds: 10
  invert_polarity_every: 1     # 1 = bounce black/white every cycle

content:
  quote_to_joke_ratio: 0.7     # 70% quotes, 30% jokes
  no_repeat_window: 200
  weights:
    quotes:
      philosophy: 1.0
      science: 1.0
      literature: 1.0
      leaders: 0.7
      humor: 0.5
    jokes:
      oneliner: 1.0
      dad: 0.8
      programming: 0.6
      observational: 0.4

api_refresh:
  enabled: true
  interval_minutes: 60
  fail_silently: true
  per_source_timeout_seconds: 5
  max_items_per_refresh: 50
  sources:
    - { name: quotable_io,        kind: quote, target_categories: [philosophy, literature, leaders, humor] }
    - { name: zenquotes,          kind: quote, target_categories: [philosophy, leaders] }
    - { name: type_fit,           kind: quote, target_categories: [philosophy, literature, humor] }
    - { name: stoic_quotes,       kind: quote, target_categories: [philosophy] }
    - { name: programming_quotes, kind: quote, target_categories: [science] }
    - { name: forismatic,         kind: quote, target_categories: [philosophy, humor] }
    - { name: icanhazdadjoke,     kind: joke,  target_categories: [dad] }
    - { name: jokeapi,            kind: joke,  target_categories: [oneliner, programming, observational],
        options: { blacklist_flags: [nsfw, religious, political, racist, sexist, explicit],
                   categories: [Programming, Misc, Pun] } }
    - { name: official_joke_api,  kind: joke,  target_categories: [oneliner, observational] }
    - { name: chuck_norris_io,    kind: joke,  target_categories: [oneliner] }
    - { name: geek_jokes,         kind: joke,  target_categories: [programming] }

animations:
  enabled: true
  shuffle: random              # random | sequential
  blocklist: []
  per_animation_overrides: {}  # e.g. noise_dissolve: { duration_seconds: 8 }

logging:
  level: INFO
  path: /var/log/quotatron.log

web_preview:
  enabled_in_dev: true
  host: 127.0.0.1
  port: 8080
```

Loaded by pydantic. Unknown keys → warning; missing keys → defaults from a
hardcoded baseline.

## 5. Animation plugin contract

Every animation lives in `src/quotatron/animations/<name>.py`:

```python
from quotatron.animations._base import AnimationContext, BaseAnimation
from PIL import Image

class DiagonalWipe(BaseAnimation):
    name = "diagonal_wipe"
    duration_default = 10.0
    target_fps = 5
    palette = "auto"   # follows current polarity

    def render(self, t: float, ctx: AnimationContext) -> Image.Image:
        """t in [0.0, 1.0] = animation progress. Returns 1-bit Pillow image."""
```

`BaseAnimation` handles canvas allocation at the rotated resolution, frame
timing, partial-refresh dispatch, and gives the renderer access to
`ctx.from_image` and `ctx.to_image` so wipes transition between actual content
frames, not blank screens. `ctx.fg` / `ctx.bg` swap with the current polarity.

`animations/__init__.py` walks the directory at import, registers every
`BaseAnimation` subclass by `name`, and validates uniqueness. The web preview
reads from this registry.

**Initial 30 animations**, distributed across categories for maximum visual
variety:

- **Wipes (3):** diagonal, radial, barn-door
- **Dissolves (3):** random-pixel, ordered-dither, diffusion
- **Geometric (3):** expanding rectangles, concentric circles, grid-stamp
- **Organic (4):** droplets, ink-bleed, snake, flood-fill
- **Glitch (3):** line-shuffle, block-jitter, scanline-tear
- **Wave (2):** sine-sweep, ripple
- **Noise (2):** pure-noise transition, Perlin-like fade
- **Growth (3):** Conway's life iterations, vine-grow, dendritic
- **Pixel sort (2):** column rain, falling pixels
- **Path (3):** spiral, hilbert curve fill, lissajous
- **Special (2):** matrix-rain text, typewriter-overprint

Frame budget: Waveshare 2.13" partial refresh is ~300 ms minimum, so 10 s ≈ 25
usable frames with safety margin. Animations specifying more than 25 frames
are decimated; fewer are padded with hold frames.

## 6. Rendering pipeline per minute

```
[1] content.next_item()  →  text + metadata
[2] render.compose(text, polarity, font, rotation)  →  destination image
[3] scheduler waits 50 s with destination on display
[4] animations.pick()  →  one plugin instance
[5] driver enters partial-refresh mode
[6] for frame in plugin.frames(from=current, to=destination, duration=10s):
        epaper.display_partial(frame)
[7] driver does one full-refresh of destination to clear ghosting
[8] polarity flips (per invert_polarity_every), loop
```

The next destination image is pre-rendered before the animation starts so
wipes can transition from current content to next content directly.

## 7. E-ink longevity

Three layered protections:

1. **Polarity bouncing** — every cycle by default. Each black pixel one cycle
   becomes white the next. Standard Waveshare longevity practice.
2. **Mandatory full-refresh after every animation** — resets accumulated
   partial-refresh ghosting. ~2 s cost per minute, already in the cycle budget.
3. **Daily deep-clean at 03:00** (configurable) — three white→black→white
   full-refresh cycles. Manufacturer-recommended deep reset.

On `SIGTERM` from systemd: cancel the scheduler task, run one final clean
full-refresh of a "Quotatron offline" message, exit. The panel never sits in
a partial-refresh state when the service stops.

## 8. Web preview / animation tester

Started with `make preview` (or `uv run quotatron preview`). FastAPI app on
`127.0.0.1:8080`. Renders via `display/mock.py` — the same code path the Pi
uses, writing to a PNG buffer instead of SPI.

UI is a single page with three columns:

- **Animation list** (auto-discovered, plus "Play all 30" and "Side-by-side" modes)
- **Preview canvas** (4× scaled 250×122, with Play / Loop / Pause / scrubber)
- **Controls** (content source selector, polarity, rotation toggles)

Key features:

- **Live reload.** Saving an animation file reimports just that module.
- **Side-by-side mode.** 5×6 grid of mini-previews, all 30 simultaneously.
- **From → to with real content.** Pick actual current and next items.
- **Frame scrubber** for spotting bad individual frames.
- **Record GIF** button — exports any animation as a GIF to
  `docs/animations/<name>.gif`. The GitHub README's gallery is built from this.
- **Block / unblock** — toggle in the browser, written to a local override
  config so prod config stays clean.

The preview deliberately does NOT talk to e-paper hardware, does NOT call APIs
(uses on-disk cache), and does NOT run on the Pi.

Tech: frames stream as base64 PNG via Server-Sent Events. Server-side Python
rendering ensures preview ≡ device pixels.

## 9. Content sources & API refresh

Hybrid: the repo ships curated bundled JSON for both quotes and jokes; an
async background task (`api_refresh.py`) opportunistically grows the on-disk
cache from the configured sources.

**11 sources total** (see config above): 6 quote sources, 5 joke sources, all
free, all no-auth (Accept-header for icanhazdadjoke). Each lives as a tiny
adapter under `sources/<name>.py` implementing
`async def fetch(limit) -> list[ContentItem]`. Failed sources are logged and
skipped — the display loop never sees the failure.

Items are tagged with `kind`, `source`, `category`, and `text` so the weighted
picker can balance them per the config `weights` block.

## 10. Build-phase source verification

`make verify-sources` runs one live `fetch(limit=3)` per source, asserting:

- HTTP success within timeout
- Response parses without exception
- ≥1 well-formed `ContentItem` returned
- Text length 1–800 chars, no HTML leakage

Tests are marked `pytest.mark.live` and excluded from normal `pytest`. CI runs
them nightly with warnings-only behavior; `--strict` flag flips to gating
mode for releases. Output format:

```
9/10 sources healthy (zenquotes rate-limited, retry tomorrow)
```

This catches the realistic failure mode of a source silently changing JSON
shape so an adapter starts returning empty lists.

## 11. WiFi profile handling

Source: `C:\Users\LCFR\Desktop\Format\wifi_profiles\*.xml` (90 Windows
profile exports, passwords in cleartext).

**One-time conversion:** `scripts/wifi_to_wpa.py` reads from an input
directory (default `C:\Users\LCFR\Desktop\Format\wifi_profiles`,
overridable via `--input <path>`) and writes
`wifi_profiles/wpa_supplicant.conf` inside the repo. The XMLs themselves
never enter the repo. The script is run once locally during dev setup.
Never executes on the Pi.

**Per-profile mapping:**

| Windows `<authentication>` | wpa_supplicant `key_mgmt` |
|---|---|
| `WPA3SAE` | `SAE WPA-PSK` (transitional fallback for BCM43143) |
| `WPA2PSK` | `WPA-PSK` |
| `WPAPSK` | `WPA-PSK proto=WPA` |
| `open` | `NONE` |

SSIDs use the `<hex>` form when present (handles non-ASCII). PSKs are
validated 8–63 ASCII or 64-hex. Profiles with `<protected>true</protected>`
(DPAPI-encrypted) are skipped with a warning. Duplicates are deduplicated by
SSID, last entry wins.

Output is a single `wpa_supplicant.conf` with priority-ordered `network={}`
blocks. Script accepts `--prefer "SSID1,SSID2"` to bump preferred networks.

A conversion report is printed and saved alongside the output:

```
✓ 87 profiles converted
⚠ 2 skipped (DPAPI-encrypted)
⚠ 1 skipped (enterprise auth, not supported)
ℹ 6 WPA3SAE profiles converted as transitional WPA2-PSK fallback
```

`scripts/install.sh` copies `wifi_profiles/wpa_supplicant.conf` to
`/etc/wpa_supplicant/wpa_supplicant.conf` (mode 600, root-owned) and triggers
`wpa_cli reconfigure`.

**Git hygiene.** `.gitignore` blocks the entire `wifi_profiles/` tree. An
optional pre-commit hook greps staged files for `psk=` patterns and aborts
the commit if it sees one.

## 12. Error handling

| Failure | Behavior |
|---|---|
| API source down | `fail_silently: true` → log warning, skip refresh |
| Bad JSON from API | Adapter validates with pydantic, drops malformed items |
| Animation plugin raises | Caught, logged with traceback, falls back to `simple_fade` (an always-shipped builtin, separate from the 30 user-facing animations) |
| E-paper SPI write fails | Retry once after 500 ms; 3 consecutive failures → systemd restart |
| Content cache empty/corrupted | Fall back to ~30-quote emergency list compiled into the package |
| Config file invalid YAML | Service refuses to start; clear error to journal; exit non-zero |
| Display panel disconnected at boot | Detect → wait 30 s → retry; logged; no CPU burn |
| Filesystem full | Log refresh failures; hold last good item until disk recovers |

## 13. Testing

1. **Unit** (`pytest`) — content selection, polarity math, weight sampling,
   animation frame math, config validation, SSID hex decoding. Fast, no IO.
2. **Frame goldens** — each animation renders frames at
   `t = {0, 0.25, 0.5, 0.75, 1.0}` and compares pixel-for-pixel against
   committed PNGs in `tests/goldens/`. `make update-goldens` regenerates.
3. **Live source tests** (`make verify-sources`) — see §10.
4. **Hardware smoke test** (`make smoke-on-device`) — runs on the Pi.
   Cycles 3 quotes + 3 animations, exits 0. Validates fresh flashes.
5. **Web preview manual** — open `http://127.0.0.1:8080`, all 30 render,
   gallery doesn't 500.

Coverage target: 80% on non-IO modules. The display driver is exercised by
the smoke test rather than mocked.

## 14. Build & deploy

```
Local dev:
  uv sync
  uv run quotatron preview
  uv run pytest
  make verify-sources

Flash + first-boot:
  scripts/flash_sdcard.sh    writes Pi OS Lite, copies repo, drops wpa_supplicant.conf
  → boot Pi
  scripts/install.sh         on-Pi installer:
    - apt install python3-spidev python3-pil fonts-dejavu
    - install uv
    - uv sync --no-dev
    - copy systemd/quotatron.service → /etc/systemd/system/
    - systemctl enable --now quotatron

Update:
  ssh pi@quotatron.local "cd ~/quotatron && git pull && uv sync && systemctl restart quotatron"
```

## 15. CI (GitHub Actions)

- `pytest` on every push (Python 3.11 + 3.12)
- `make verify-sources` nightly (cron), warnings only, attached as artifact
- `ruff check` + `ruff format --check` on every push
- Tag → release: build a zip with `wifi_profiles/` excluded (CI never sees secrets)

## 16. Logging

- Default INFO to `/var/log/quotatron.log`, rotated 10 MB × 5 files
- Each cycle: one line — `cycle=1234 item=quote/philosophy author="Marcus Aurelius" anim=diagonal_wipe polarity=normal`
- ERROR-level events also go to systemd journal — `journalctl -u quotatron`
  is always usable for debugging

## 17. Out of scope (this iteration)

- OTA updates beyond `git pull`
- Mobile app companion
- Multiple e-paper displays per Pi
- Cloud-hosted content backup
- User-supplied custom fonts (default DejaVu Sans is bundled; font selection
  is a future config addition)
- Web preview running on the Pi itself
- Quote/joke editing UI
