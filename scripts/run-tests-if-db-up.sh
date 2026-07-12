#!/usr/bin/env bash
# Pre-commit helper: run pytest only if the dev DB (compose.dev.yml) is up.
# This avoids blocking commits when the dev infra is not running.
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if docker compose -f "$PROJECT_ROOT/compose.dev.yml" ps postgres 2>/dev/null | grep -qE "running|Up"; then
  cd "$PROJECT_ROOT/backend"
  uv run bash scripts/tests-start.sh
else
  echo "⚠️  Dev DB not running — skipping tests. Start with: docker compose -f compose.dev.yml up -d" >&2
  exit 0
fi
