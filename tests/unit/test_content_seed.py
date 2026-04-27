import json
from pathlib import Path

import pytest
import quotatron

REPO_ROOT = Path(quotatron.__file__).resolve().parents[2]
CONTENT_FILES = sorted((REPO_ROOT / "content").rglob("*.json"))

assert CONTENT_FILES, "no seed JSON files found under content/ — has the corpus been deleted?"


@pytest.mark.parametrize(
    "path", CONTENT_FILES, ids=lambda p: p.relative_to(REPO_ROOT).as_posix()
)
def test_seed_json_files_parse_and_have_required_fields(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) >= 10
    for item in data:
        assert set(["text", "author", "category"]).issubset(item.keys())
        assert 1 <= len(item["text"]) <= 800
        # Spec: every item's category field must match its filename stem.
        assert item["category"] == path.stem, (
            f"{path.name}: item category {item['category']!r} != filename stem {path.stem!r}"
        )
