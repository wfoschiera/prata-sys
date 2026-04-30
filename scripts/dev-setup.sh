#!/usr/bin/env bash
# Idempotent local development setup for prata-sys.
#
# What it does:
#   - Boots the dev infra (PostgreSQL + Mailpit) via compose.dev.yml.
#   - Syncs backend Python deps (uv) and frontend deps (bun).
#   - Runs DB migrations and seeds the first superuser.
#
# Re-run anytime — it skips work that's already done.
#
# Usage: bash scripts/dev-setup.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ ! -f .env ]]; then
    echo "ERROR: .env not found in $PROJECT_ROOT" >&2
    exit 1
fi
if [[ ! -f compose.dev.yml ]]; then
    echo "ERROR: compose.dev.yml not found in $PROJECT_ROOT" >&2
    exit 1
fi
if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: docker not found. Install Docker, or see development.md for the TrueNAS alternative." >&2
    exit 1
fi

echo "==> Booting dev infra (Postgres + Mailpit)"
docker compose -f compose.dev.yml up -d --wait

echo "==> Syncing backend deps (uv)"
(cd backend && uv sync --frozen)

echo "==> Running migrations + initial superuser seed"
(cd backend && uv run bash scripts/prestart.sh)

echo "==> Installing frontend deps (bun)"
(cd frontend && bun install --frozen-lockfile)

cat <<'EOF'

=================================================
 Setup complete.
=================================================

Run the app in 2 terminals:

  Terminal 1 — backend (port 8000):
      cd backend && uv run fastapi dev app/main.py

  Terminal 2 — frontend (port 5173):
      cd frontend && bun run dev

Open:
  - Frontend:        http://localhost:5173
  - Backend:         http://localhost:8000
  - API docs:        http://localhost:8000/docs
  - Mailpit (mail):  http://localhost:8025

Stop dev infra:  docker compose -f compose.dev.yml down
Reset DB:        docker compose -f compose.dev.yml down -v && bash scripts/dev-setup.sh
EOF
