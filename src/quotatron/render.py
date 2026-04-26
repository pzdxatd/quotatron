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
