import json
from pathlib import Path
import pytest


@pytest.mark.parametrize("path", list(Path("content").rglob("*.json")))
def test_seed_json_files_parse_and_have_required_fields(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 10
    for item in data:
        assert set(["text", "author", "category"]).issubset(item.keys())
        assert 1 <= len(item["text"]) <= 800
