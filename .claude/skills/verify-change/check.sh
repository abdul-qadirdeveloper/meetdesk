#!/usr/bin/env bash
set -u
status=0
echo "== ruff ==";   uv run ruff check .  || status=1
echo "== mypy ==";   uv run mypy src      || status=1
echo "== pytest =="; uv run pytest -q     || status=1
exit $status