"""Compose a ContentItem into a 1-bit framebuffer image."""
from __future__ import annotations
from typing import Literal, Union
from PIL import Image, ImageDraw, ImageFont
from quotatron.models import ContentItem, Polarity

CANVAS_W, CANVAS_H = 250, 122  # native landscape resolution
TEXT_MARGIN = 6
AUTHOR_MARGIN = 4
AUTHOR_FONT_SIZE = 11
AUTHOR_H = int(AUTHOR_FONT_SIZE * 1.15)  # = 12
BODY_FONT_SIZES: tuple[int, ...] = (16, 14, 12, 10)

_AnyFont = Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]
Rotation = Literal["landscape", "portrait"]


def _load_font(size: int) -> _AnyFont:
    """Pi OS canonical DejaVu path; on dev machines (Windows/macOS) we fall
    back to Pillow's bundled default font (Aileron in Pillow >=10)."""
    return (
        ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        if _dejavu_installed()
        else ImageFont.load_default()
    )


def _dejavu_installed() -> bool:
    from pathlib import Path
    return Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf").exists()


def _wrap(text: str, font: _AnyFont, max_w: int) -> list[str]:
    """Greedy word-wrap by pixel width. A single word wider than max_w is
    force-included on its own line (the `or not cur` clause)."""
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


def _truncate_to_width(text: str, font: _AnyFont, max_w: int) -> str:
    if font.getlength(text) <= max_w:
        return text
    while len(text) > 1 and font.getlength(text + "…") > max_w:
        text = text[:-1]
    return text + "…"


def compose(
    item: ContentItem,
    *,
    polarity: Polarity,
    rotation: Rotation = "landscape",
) -> Image.Image:
    """Render a ContentItem to a 1-bit Pillow Image of size CANVAS_W x CANVAS_H.

    The returned image is always landscape (250x122) regardless of the
    `rotation` argument. The display driver applies physical rotation when
    pushing to the panel; the parameter exists so callers don't have to know
    that detail.
    """
    img = Image.new("1", (CANVAS_W, CANVAS_H), polarity.bg)
    draw = ImageDraw.Draw(img)
    max_text_w = CANVAS_W - 2 * TEXT_MARGIN
    avail_h = CANVAS_H - 2 * TEXT_MARGIN - AUTHOR_H - AUTHOR_MARGIN

    body_lines: list[str] = []
    body_font: _AnyFont | None = None
    line_h = 0
    for size in BODY_FONT_SIZES:
        f = _load_font(size)
        lines = _wrap(item.text, f, max_text_w)
        lh = int(f.size * 1.15)
        if len(lines) * lh <= avail_h:
            body_lines = lines
            body_font = f
            line_h = lh
            break
    if body_font is None:
        body_font = _load_font(BODY_FONT_SIZES[-1])
        body_lines = _wrap(item.text, body_font, max_text_w)
        line_h = int(body_font.size * 1.15)
        max_lines = avail_h // line_h
        if len(body_lines) > max_lines:
            body_lines = body_lines[:max_lines]
            body_lines[-1] = (body_lines[-1][:-1] + "…") if body_lines[-1] else "…"

    y = TEXT_MARGIN
    for line in body_lines:
        draw.text((TEXT_MARGIN, y), line, fill=polarity.fg, font=body_font)
        y += line_h

    author_font = _load_font(AUTHOR_FONT_SIZE)
    author_text = _truncate_to_width(f"— {item.author}", author_font, max_text_w)
    aw = author_font.getlength(author_text)
    draw.text(
        (CANVAS_W - TEXT_MARGIN - aw, CANVAS_H - TEXT_MARGIN - AUTHOR_H),
        author_text,
        fill=polarity.fg,
        font=author_font,
    )

    return img
