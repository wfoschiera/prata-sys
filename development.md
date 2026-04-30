# prata-sys — Local Development

Local dev runs the **backend** and **frontend** natively (no Docker), and uses a tiny Docker Compose stack only for the **infrastructure** (PostgreSQL + Mailpit). This keeps the development loop fast and frictionless while ensuring the database matches production.

Production deploys to a single Docker Compose host via `compose.prod.yml` — see [`deploy/README.md`](deploy/README.md). The historical Traefik-based stack lives on the [`docker-stack`](https://github.com/wfoschiera/prata-sys/tree/docker-stack) branch and is intended for FastAPI Cloud or any other container-based managed deploy.

## Prerequisites

| Tool          | Why                                  |
|---------------|--------------------------------------|
| Python 3.14+  | Backend runtime                      |
| `uv`          | Python package manager               |
| Bun           | Frontend package manager + Vite      |
| Docker        | Runs Postgres + Mailpit only         |

## First-time setup

```bash
bash scripts/dev-setup.sh
```

The script is idempotent and:

1. Boots `compose.dev.yml` (Postgres + Mailpit), waits for the DB healthcheck.
2. Syncs backend deps (`uv sync --frozen`) and frontend deps (`bun install --frozen-lockfile`).
3. Runs migrations (`alembic upgrade head`) and seeds the first superuser.

## Daily workflow

Two terminals (the dev infra runs in the background via Docker):

```bash
# Terminal 1 — backend (hot-reload on http://localhost:8000)
cd backend && uv run fastapi dev app/main.py

# Terminal 2 — frontend (hot-reload on http://localhost:5173)
cd frontend && bun run dev
```

Stop / start the infra:

```bash
docker compose -f compose.dev.yml up -d        # start
docker compose -f compose.dev.yml down         # stop (keeps data)
docker compose -f compose.dev.yml down -v      # stop + wipe DB volume
```

## Local dev URLs

| Service        | URL                          |
|----------------|------------------------------|
| Frontend       | http://localhost:5173        |
| Backend API    | http://localhost:8000        |
| Swagger docs   | http://localhost:8000/docs   |
| ReDoc          | http://localhost:8000/redoc  |
| Mailpit        | http://localhost:8025        |

## Database admin

Use `psql`, [DBeaver](https://dbeaver.io/), or [pgcli](https://www.pgcli.com/):

```bash
psql "postgresql://postgres:changethis@localhost:5432/app"
```

## Resetting the database

```bash
docker compose -f compose.dev.yml down -v
bash scripts/dev-setup.sh
```

## Email testing (Mailpit)

Mailpit is up automatically by `compose.dev.yml`. To route the backend's outgoing emails into it, set in `.env`:

```dotenv
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_TLS=False
EMAILS_FROM_EMAIL=dev@localhost
```

Captured emails: http://localhost:8025

## OpenAPI client regeneration

After changing backend routes/schemas:

```bash
bash scripts/generate-client.sh
```

## Pre-commit hooks (`prek`)

We use [prek](https://prek.j178.dev/) (a faster pre-commit replacement). It runs on every commit.

```bash
# Install hook (run once after clone)
cd backend && uv run prek install -f

# Run on all files manually
cd backend && uv run prek run --all-files
```

## Tests

```bash
# Backend
cd backend && bash scripts/test.sh

# Frontend E2E (Playwright) — needs backend with SMTP pointing at Mailpit:
#   cd backend && SMTP_HOST=localhost SMTP_PORT=1025 SMTP_TLS=False \
#     EMAILS_FROM_EMAIL=dev@example.com uv run fastapi run app/main.py --port 8000
#   cd frontend && MAILPIT_HOST=http://localhost:8025 bunx playwright test
```

---

## Alternative: dev against an external Postgres

If you'd rather not run a local Postgres at all, you can point dev at any reachable Postgres instance using a separate database (`dev`) — keeping prod data untouched.

### One-time setup on the Postgres host

Create a dev database:

```sql
CREATE DATABASE dev OWNER postgres;
```

Make sure the Postgres instance accepts connections from your machine (`pg_hba.conf` / firewall / port mapping).

### Switch your `.env`

```dotenv
POSTGRES_SERVER=<host-or-ip>
POSTGRES_PORT=<port>
POSTGRES_DB=dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<password>
```

Then run only the backend init bits (skip Docker):

```bash
cd backend && uv sync --frozen && uv run bash scripts/prestart.sh
cd ../frontend && bun install --frozen-lockfile
```

### Tradeoffs

| Choice                | When it's better                                                      |
|-----------------------|----------------------------------------------------------------------|
| Local Docker Postgres | Default. Offline work, fast resets, isolation, matches prod version. |
| External `dev` DB     | No infra on laptop, share state across machines, low traffic.        |

⚠️ Risks of pointing at an external DB:
- Always double-check `POSTGRES_DB=dev` before running migrations — pointing at the prod DB by mistake will rewrite schema.
- Offline = dev breaks.
- Mixing prod and dev on the same server makes a slow DB query in dev visible to the prod app.
