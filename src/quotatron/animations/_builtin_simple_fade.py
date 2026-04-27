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
        # Crossfade in 'L' (grayscale) space, then quantize to 1-bit
        # (PIL's default convert("1") applies Floyd-Steinberg dithering).
        from PIL import ImageChops
        if t <= 0.0:
            return ctx.from_image.copy()
        if t >= 1.0:
            return ctx.to_image.copy()
        a = ctx.from_image.convert("L")
        b = ctx.to_image.convert("L")
        blended = ImageChops.blend(a, b, t).convert("1")
        return blended
