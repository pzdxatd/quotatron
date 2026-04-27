from fastapi.testclient import TestClient
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
