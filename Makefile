.PHONY: install preview test test-unit verify-sources update-goldens lint format clean smoke-on-device gallery deploy-pi

PI_HOST ?= pi@quotatron.local
PI_PASS ?=

install:
	uv sync --extra preview

preview:
	uv run quotatron preview

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit/

verify-sources:
	uv run pytest -m live tests/sources/ -v --tb=short

update-goldens:
	@echo "Per-animation; see Task 5.x in plan for the regeneration snippet."

lint:
	uv run ruff check src/ tests/ scripts/

format:
	uv run ruff format src/ tests/ scripts/

clean:
	rm -rf .venv build dist *.egg-info .pytest_cache .coverage htmlcov .ruff_cache

smoke-on-device:
	uv run quotatron run

deploy-pi:
	@bash scripts/deploy_pi.sh $(PI_HOST) $(PI_PASS)

gallery:
	@echo "Regenerating animation gallery GIFs under docs/animations/..."
	uv run python -c "from quotatron.web_preview.gif_export import export_gif; \
	from quotatron.animations import registry; \
	from pathlib import Path; \
	[export_gif(name, Path(f'docs/animations/{name}.gif'), duration_s=5.0) for name in registry(refresh=True)]; \
	print('Done.')"
