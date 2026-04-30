# prata-sys — Local Development

Local dev runs the **backend** and **frontend** natively (no Docker), and uses a tiny Docker Compose stack only for the **infrastructure** (PostgreSQL + Mailpit). This keeps the development loop fast and frictionless while ensuring the database matches production.

The full Docker stack (Traefik, prod-style backend/frontend containers, etc.) lives on the [`docker-stack`](https://github.com/wfoschiera/prata-sys/tree/docker-stack) branch and is intended for FastAPI Cloud or other container-based deploys.

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

# Frontend E2E (Playwright) — currently lives on the docker-stack branch
# (depends on the full Docker stack); being refactored to run natively.
```

---

## Alternative: dev against TrueNAS PostgreSQL

If you'd rather not run a local Postgres at all, you can point dev at the **Postgres app on the TrueNAS homelab** using a separate database (`dev`) — keeping prod data untouched.

### One-time setup on the TrueNAS

Connect to the TrueNAS Postgres app (e.g. via Adminer or `psql`) and create a dev database:

```sql
CREATE DATABASE dev OWNER postgres;
```

Make sure the Postgres app accepts connections from your LAN (check `pg_hba.conf` / app port mapping — exposed on `192.168.1.244:<port>`).

### Switch your `.env`

```dotenv
POSTGRES_SERVER=192.168.1.244
POSTGRES_PORT=<the-port-the-app-exposes>
POSTGRES_DB=dev
POSTGRES_USER=postgres
POSTGRES_PASSWORD=<your-prod-postgres-password>
```

Then run only the backend init bits (skip Docker):

```bash
cd backend && uv sync --frozen && uv run bash scripts/prestart.sh
cd ../frontend && bun install --frozen-lockfile
```

### Tradeoffs

| Choice                 | When it's better                                                      |
|------------------------|----------------------------------------------------------------------|
| Local Docker Postgres  | Default. Offline work, fast resets, isolation, matches prod version. |
| TrueNAS `dev` DB       | No infra on laptop, share state across machines, low traffic.        |

⚠️ Risks of pointing at TrueNAS:
- Always double-check `POSTGRES_DB=dev` before running migrations — pointing at the prod DB by mistake will rewrite schema.
- Offline = dev breaks.
- Mixing prod and dev on the same server makes a slow DB query in dev visible to the prod app.
