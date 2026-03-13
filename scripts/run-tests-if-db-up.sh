#!/usr/bin/env bash
# Pre-commit helper: run pytest only if the DB container is already running.
# This avoids blocking commits when the dev stack is not up.
set -e

if docker compose ps db 2>/dev/null | grep -qE "running|Up"; then
  cd backend
  uv run bash scripts/tests-start.sh
else
  echo "⚠️  DB container not running — skipping tests. Start with: docker compose up -d db mailcatcher" >&2
  exit 0
fi
