"""In-memory display backend for tests and the web preview."""
from __future__ import annotations
from typing import Literal
from PIL import Image

DisplayEvent = Literal[
    "full", "enter_partial", "partial", "exit_partial", "deep_clean", "shutdown"
]


class MockDisplay:
    def __init__(self, width: int = 250, height: int = 122) -> None:
        self.width = width
        self.height = height
        self.history: list[tuple[DisplayEvent, Image.Image | None]] = []
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
            self.history.append(("shutdown", farewell.copy()))
        else:
            self.history.append(("shutdown", None))

    def current_image(self) -> Image.Image | None:
        return self._current.copy() if self._current is not None else None
