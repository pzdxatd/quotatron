"""Export an animation as a GIF for the docs gallery / README."""
from __future__ import annotations
from pathlib import Path
from PIL import Image
from quotatron.animations import fallback, registry
from quotatron.animations._base import AnimationContext
from quotatron.models import ContentItem, Polarity
from quotatron.render import compose


def export_gif(name: str, out_path: Path, duration_s: float = 10.0) -> Path:
    """Render `name` as a GIF written to `out_path`.

    Returns the output path. Uses simple "Hello, world." / "Goodbye, world."
    placeholder content so the gallery doesn't depend on the live corpus.
    Raises ValueError if `name` is not a registered animation.
    """
    cls = registry().get(name)
    if cls is None and name == "simple_fade":
        cls = fallback()
    if cls is None:
        raise ValueError(f"unknown animation: {name}")

    # Use opposite-polarity from/to so the wipe shows dramatic contrast
    # (otherwise both frames are ~95% white text-on-white-bg and the
    # animation looks like white-to-white). This also matches real device
    # behavior — polarity bounces every cycle, so alternating cycles ARE
    # visually inverted relative to each other.
    cur = ContentItem(
        kind="quote", text="Hello, world.", author="anon",
        category="philosophy", source="bundled",
    )
    nxt = ContentItem(
        kind="quote", text="Goodbye, world.", author="anon",
        category="philosophy", source="bundled",
    )
    from_img = compose(cur, polarity=Polarity.NORMAL, rotation="landscape")
    to_img = compose(nxt, polarity=Polarity.INVERTED, rotation="landscape")
    ctx = AnimationContext(
        from_image=from_img, to_image=to_img, polarity=Polarity.NORMAL,
        width=250, height=122,
    )
    frames = [f.convert("RGB") for f in cls().frames(ctx, duration_s)]
    if not frames:
        raise ValueError(f"animation {name!r} produced 0 frames")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    duration_ms_per_frame = int(1000 * duration_s / len(frames))
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms_per_frame,
        loop=0,
    )
    return out_path
