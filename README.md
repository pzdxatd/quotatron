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
