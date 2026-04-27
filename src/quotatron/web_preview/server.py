"""FastAPI web preview server. Dev-only — never deployed to the Pi.

The point: render animations through the EXACT same Python code path that
production uses, just writing to PNG bytes instead of SPI. So a plugin that
looks fine in JS but breaks the real renderer can't slip through.
"""
from __future__ import annotations
import asyncio
import base64
import io
import json
import logging
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image
from sse_starlette.sse import EventSourceResponse

from quotatron.animations import fallback, registry
from quotatron.animations._base import AnimationContext
from quotatron.content import ContentLibrary
from quotatron.models import ContentItem, Polarity
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
        {
            "name": cls.name,
            "duration_default": cls.duration_default,
            "target_fps": cls.target_fps,
        }
        for cls in registry(refresh=True).values()
    ]


@app.get("/api/content/sample")
def sample_content() -> dict:
    """Return one current and one next content item from the bundled corpus."""
    import quotatron
    repo_root = Path(quotatron.__file__).resolve().parents[2]
    lib = ContentLibrary.from_disk(repo_root / "content")
    weights_q = {"philosophy": 1.0, "science": 1.0, "literature": 1.0,
                 "leaders": 1.0, "humor": 1.0}
    weights_j = {"oneliner": 1.0, "dad": 1.0, "programming": 1.0, "observational": 1.0}
    cur = lib.next_item(
        quote_to_joke_ratio=0.7, quote_weights=weights_q, joke_weights=weights_j,
        no_repeat_window=0,
    )
    nxt = lib.next_item(
        quote_to_joke_ratio=0.7, quote_weights=weights_q, joke_weights=weights_j,
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
    duration: float = Query(5.0, ge=1.0, le=60.0),
):
    reg = registry()
    cls = reg.get(name)
    if cls is None and name == "simple_fade":
        cls = fallback()
    if cls is None:
        return Response(status_code=404, content=f"unknown animation: {name}")
    pol = Polarity.NORMAL if polarity == "normal" else Polarity.INVERTED

    samples = sample_content()
    cur_item = ContentItem(**samples["current"])
    nxt_item = ContentItem(**samples["next"])
    rot = "portrait" if rotation == "portrait" else "landscape"
    from_img = compose(cur_item, polarity=pol, rotation=rot)
    to_img = compose(nxt_item, polarity=pol.flipped(), rotation=rot)
    ctx = AnimationContext(
        from_image=from_img, to_image=to_img, polarity=pol,
        width=250, height=122,
    )

    async def gen():
        anim = cls()
        for i, frame in enumerate(anim.frames(ctx, duration)):
            yield {"event": "frame", "data": json.dumps(
                {"i": i, "png_b64": _img_to_b64png(frame)}
            )}
            await asyncio.sleep(0.0)
        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(gen())


def run_preview() -> int:
    import uvicorn
    from quotatron.config import load_config
    cfg = load_config("config/quotatron.yaml")
    uvicorn.run(
        "quotatron.web_preview.server:app",
        host=cfg.web_preview.host,
        port=cfg.web_preview.port,
        reload=True,
    )
    return 0
