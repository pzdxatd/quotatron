import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from PIL import Image
from quotatron.web_preview.gif_export import export_gif
from quotatron.web_preview.server import app


def test_animations_endpoint_lists_registered_animations() -> None:
    client = TestClient(app)
    r = client.get("/api/animations")
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list)
    # We have 30 plugin animations in the registry from Milestone 5.
    assert len(body) == 30
    for entry in body:
        assert {"name", "duration_default", "target_fps"}.issubset(entry.keys())


def test_export_gif_writes_multi_frame_gif(tmp_path: Path) -> None:
    out = tmp_path / "diagonal_wipe.gif"
    result = export_gif("diagonal_wipe", out, duration_s=2.0)
    assert result == out
    assert out.exists()
    img = Image.open(out)
    assert img.format == "GIF"
    # Multi-frame check: seek to the second frame should not raise.
    img.seek(1)


def test_export_gif_unknown_raises() -> None:
    with pytest.raises(ValueError, match="unknown animation"):
        export_gif("nonexistent_anim_xyz", Path("/tmp/nope.gif"))
