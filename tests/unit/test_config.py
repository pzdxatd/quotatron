import pytest
from pathlib import Path
from quotatron.config import Config, load_config


def test_loads_default_config_from_yaml(tmp_path: Path) -> None:
    yaml = """
display:
  rotation: landscape
  driver: waveshare_2in13_v3
  full_refresh_every: 1
cycle:
  quote_seconds: 50
  animation_seconds: 10
  invert_polarity_every: 1
content:
  quote_to_joke_ratio: 0.7
  no_repeat_window: 200
  weights:
    quotes: {philosophy: 1.0, science: 1.0}
    jokes: {oneliner: 1.0}
api_refresh:
  enabled: true
  interval_minutes: 60
  fail_silently: true
  per_source_timeout_seconds: 5
  max_items_per_refresh: 50
  sources: []
animations:
  enabled: true
  shuffle: random
  blocklist: []
  per_animation_overrides: {}
logging:
  level: INFO
  path: /var/log/quotatron.log
web_preview:
  enabled_in_dev: true
  host: 127.0.0.1
  port: 8080
"""
    p = tmp_path / "c.yaml"
    p.write_text(yaml)
    cfg = load_config(p)
    assert isinstance(cfg, Config)
    assert cfg.display.rotation == "landscape"
    assert cfg.cycle.quote_seconds == 50
    assert cfg.content.quote_to_joke_ratio == 0.7


def test_invalid_rotation_rejected(tmp_path: Path) -> None:
    yaml = "display:\n  rotation: sideways\n"
    p = tmp_path / "c.yaml"
    p.write_text(yaml)
    with pytest.raises(ValueError):
        load_config(p)


def test_quote_to_joke_ratio_must_be_in_range(tmp_path: Path) -> None:
    yaml = "content:\n  quote_to_joke_ratio: 1.5\n"
    p = tmp_path / "c.yaml"
    p.write_text(yaml)
    with pytest.raises(ValueError):
        load_config(p)


def test_negative_quote_to_joke_ratio_rejected(tmp_path: Path) -> None:
    yaml = "content:\n  quote_to_joke_ratio: -0.1\n"
    p = tmp_path / "c.yaml"
    p.write_text(yaml)
    with pytest.raises(ValueError):
        load_config(p)


def test_unknown_top_level_key_rejected(tmp_path: Path) -> None:
    yaml = "made_up_section:\n  whatever: 1\n"
    p = tmp_path / "c.yaml"
    p.write_text(yaml)
    with pytest.raises(ValueError):
        load_config(p)


def test_unknown_display_key_rejected(tmp_path: Path) -> None:
    yaml = "display:\n  rotation: landscape\n  unknown_field: 42\n"
    p = tmp_path / "c.yaml"
    p.write_text(yaml)
    with pytest.raises(ValueError):
        load_config(p)


def test_empty_yaml_uses_all_defaults(tmp_path: Path) -> None:
    p = tmp_path / "c.yaml"
    p.write_text("")
    cfg = load_config(p)
    assert cfg.cycle.quote_seconds == 50
    assert cfg.display.rotation == "landscape"
    assert cfg.content.quote_to_joke_ratio == 0.7


def test_default_config_file_loads() -> None:
    from quotatron.config import load_config
    cfg = load_config("config/quotatron.yaml")
    assert cfg.display.rotation == "landscape"
    assert len(cfg.api_refresh.sources) == 11
    assert cfg.cycle.quote_seconds + cfg.cycle.animation_seconds == 60
