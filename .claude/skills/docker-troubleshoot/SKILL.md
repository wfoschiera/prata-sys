---
name: docker-troubleshoot
description: Investigate and troubleshoot Docker Compose issues in the prata-sys project. Trigger when the user mentions containers not starting, port conflicts, DB connection errors, migration failures, build errors, hot-reload not working, volume/permission issues, or any Docker-related problem.
allowed-tools: Bash, Read, Grep
---

# Docker Compose Troubleshoot — prata-sys

Help the user investigate and fix issues with the local Docker Compose dev environment.

## Project Services

| Service      | Port  | Purpose                    |
|--------------|-------|----------------------------|
| backend      | 8000  | FastAPI API server          |
| frontend     | 5173  | React/Vite dev server       |
| db           | 5432  | PostgreSQL database          |
| adminer      | 8080  | DB admin UI                  |
| mailcatcher  | 1080  | Email testing (SMTP on 1025) |
| traefik      | 80    | Reverse proxy                |

## Investigation Workflow

Follow these steps in order, stopping when the root cause is found:

### Step 1: Check container status

```bash
docker compose ps -a
```

Look for:
- **State**: `running`, `exited`, `restarting`, `created` (stuck)
- **Exit code**: non-zero means a crash
- **Ports**: confirm expected port mappings are present

### Step 2: Check logs of the failing service

```bash
docker compose logs --tail=100 <service>
```

Replace `<service>` with `backend`, `frontend`, `db`, etc. Use `--follow` only if needed interactively.

To check all services at once:
```bash
docker compose logs --tail=50
```

### Step 3: Check DB connectivity (if backend fails)

```bash
docker compose exec db pg_isready -U app
```

If DB is not ready, check its logs:
```bash
docker compose logs --tail=50 db
```

### Step 4: Check migration status

```bash
docker compose exec backend alembic -c /app/alembic.ini current
docker compose exec backend alembic -c /app/alembic.ini heads
```

If migrations are out of sync:
```bash
docker compose exec backend alembic -c /app/alembic.ini upgrade head
```

### Step 5: Check environment variables

```bash
docker compose exec backend env | sort
```

Verify critical vars: `DATABASE_URL`, `SECRET_KEY`, `FIRST_SUPERUSER`, `FIRST_SUPERUSER_PASSWORD`.

### Step 6: Check resource usage

```bash
docker stats --no-stream
```

### Step 7: Rebuild if needed

```bash
docker compose build --no-cache <service>
docker compose up -d <service>
```

Or full rebuild:
```bash
docker compose down && docker compose build --no-cache && docker compose up -d
```

## Common Issues and Diagnosis

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Port already in use (`bind: address already in use`) | Another process on the same port | `lsof -i :<port>` to find it, kill or change port |
| Backend exits immediately | Missing env vars, bad DB URL, Python import error | Check backend logs, verify `.env` file |
| DB connection refused | DB container not ready yet or wrong credentials | Check DB logs, ensure `pg_isready` passes, verify `DATABASE_URL` |
| Migration error (`alembic.util.exc.CommandError`) | Schema out of sync, missing migration | Run `alembic upgrade head`, or generate new migration |
| Frontend build fails | Node/Bun dependency issue, TS error | Check frontend logs, try `docker compose exec frontend bun install` |
| Hot-reload not working | `docker compose watch` not used, or volume mount issue | Use `docker compose watch` instead of `docker compose up` |
| Volume permission denied | Host/container UID mismatch | Check volume mounts in `compose.yaml`, fix ownership |
| `no space left on device` | Docker disk full | `docker system prune -f` to reclaim space |
| Traefik 502 Bad Gateway | Backend not reachable from Traefik network | Check service is on correct Docker network, check Traefik labels |
| Tests fail with "connection refused" | Test DB not running or wrong test DB URL | Ensure test containers are up, check `scripts/test.sh` |

## Useful Recovery Commands

```bash
# Full reset: stop everything, remove volumes, rebuild
docker compose down -v && docker compose build && docker compose up -d

# View real-time logs for a service
docker compose logs -f backend

# Shell into a container
docker compose exec backend bash
docker compose exec frontend sh

# Check Docker disk usage
docker system df
```

## Output Guidelines

- Summarize findings clearly: what is wrong, why, and the suggested fix
- Quote relevant log lines
- If the issue is in application code, point to the file/line that needs to change
- If the issue is configuration, suggest the specific compose/env change
