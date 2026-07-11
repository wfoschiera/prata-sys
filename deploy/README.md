# Deploy — Docker Compose host

prata-sys runs on a single deploy host as a Docker Compose stack (`compose.prod.yml`). Images are **built in CI and pushed to GHCR** — the host only pulls. Postgres is **external** to this stack — point at any reachable Postgres instance via the `.env` file.

## Topology

```
GitHub (merge to main)
  └─ GHA: test → build images → push to ghcr.io/wfoschiera/prata-sys-{backend,frontend}
      └─ GHA: join tailnet → scp compose.prod.yml + Caddyfile → ssh: compose pull && up -d

                       client browser
                            │
                            ▼
                http://<host>:${HOST_PORT}    ← single port, public surface
                            │
                            ▼
                       ┌────────┐
                       │  Caddy │ (compose service, reverse proxy)
                       └───┬────┘
                           │
                ┌──────────┴────────────────┐
                ▼                           ▼
        /api, /docs, /redoc           everything else
                │                           │
            backend:8000             frontend:80 (nginx serving SPA)
                │
                ▼
         External Postgres
       (POSTGRES_SERVER from .env)
```

## First-time setup on the deploy host

Pick a directory for the stack (e.g. `/mnt/dados/apps/prata-sys`) and make sure the SSH user used by the deploy workflow can write to it and run docker.

Only three files live there — `compose.prod.yml` and `Caddyfile` (copied by every deploy) plus your hand-written `.env`:

```bash
mkdir -p <DEPLOY_PATH>
cd <DEPLOY_PATH>
# copy deploy/.env.example from the repo, then:
$EDITOR .env  # fill the blanks (see "Required variables" below)
```

Then trigger a deploy by pushing to `main` — the workflow builds and pushes the images, copies the stack config, pulls, runs migrations (prestart), and brings the stack up.

## Required variables

See [`.env.example`](.env.example) for the full template. The blanks you must fill (no good defaults):

| Variable | Notes |
|---|---|
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `FRONTEND_HOST` | Full public URL, e.g. `http://<host>:8080` |
| `BACKEND_CORS_ORIGINS` | Origins users access the app from (comma-separated) |
| `POSTGRES_SERVER` | Hostname/IP of your Postgres instance |
| `POSTGRES_PORT` | Whatever port Postgres listens on (default 5432) |
| `POSTGRES_PASSWORD` | Password of `POSTGRES_USER` |
| `FIRST_SUPERUSER` | Email used for the initial admin login (must be an email address) |
| `FIRST_SUPERUSER_PASSWORD` | Strong password for the first login |

`POSTGRES_DB=prata_sys` is the convention — create that database (and the `prata_sys` user) in your Postgres instance once before the first deploy.

The frontend bundle is built in CI with an **empty `VITE_API_URL`** (same-origin): the SPA calls `/api/*` relative to whatever host serves it, so the same image works on any IP or future domain — no rebuild needed.

## GitHub Secrets used by the deploy workflow

The workflow connects to the deploy host over a private mesh via Tailscale, then uses SSH. You'll need both Tailscale OAuth credentials and the usual SSH/path secrets. Images are pushed to GHCR with the automatic `GITHUB_TOKEN` — no extra registry secret.

### Tailscale (private mesh)

| Secret | Value |
|---|---|
| `TS_OAUTH_CLIENT_ID` | OAuth client ID generated at https://login.tailscale.com/admin/settings/oauth |
| `TS_OAUTH_SECRET` | OAuth client secret from the same place |

The runner joins the tailnet with the tag `tag:ci-prata-sys`. You must:

1. Declare the tag in your tailnet ACL under `tagOwners`, e.g.:
   ```jsonc
   "tagOwners": {
     "tag:ci-prata-sys": ["autogroup:admin"]
   }
   ```
2. Authorize the OAuth client to attach `tag:ci-prata-sys`.
3. Make sure your ACL allows the tagged node to reach the deploy host on port 22, e.g.:
   ```jsonc
   "acls": [
     { "action": "accept", "src": ["tag:ci-prata-sys"], "dst": ["<deploy-host>:22"] }
   ]
   ```

### Deploy SSH + target

| Secret | Value |
|---|---|
| `DEPLOY_HOST` | Tailscale hostname (MagicDNS) or IP of the deploy host |
| `DEPLOY_USER` | SSH user on the deploy host |
| `DEPLOY_SSH_KEY` | Private key matching `~/.ssh/authorized_keys` of `DEPLOY_USER` |
| `DEPLOY_PATH` | Absolute path on the host where the stack lives |

## Common operations

Run on the deploy host (`cd <DEPLOY_PATH>`):

```bash
# Tail logs
docker compose -f compose.prod.yml logs -f

# Redeploy the current images (e.g. after editing .env)
docker compose -f compose.prod.yml up -d

# Roll back to a specific version (any commit previously deployed)
TAG=sha-xxxxxxx docker compose -f compose.prod.yml pull
TAG=sha-xxxxxxx docker compose -f compose.prod.yml up -d

# Stop the stack
docker compose -f compose.prod.yml down
```

## Backup

This stack is stateless except for the Caddy volumes (`caddy-data`, `caddy-config`). Application data lives in your external Postgres — back it up via your normal database backup policy (for the TrueNAS setup: nightly `pg_dump` cron + ZFS snapshots on the data dataset).
