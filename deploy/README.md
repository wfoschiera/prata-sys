# Deploy — Docker Compose host

prata-sys runs on a single deploy host as a Docker Compose stack (`compose.prod.yml`). Postgres is **external** to this stack — point at any reachable Postgres instance via the `.env` file.

## Topology

```
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

Pick a directory for the app (e.g. `/srv/prata-sys` or any path under your data volume) and make sure the SSH user used by the deploy workflow can write to it. The first GHA run rsyncs the repo into it.

After that first sync, populate `.env`:

```bash
cd <DEPLOY_PATH>
cp deploy/.env.example .env
$EDITOR .env  # fill the blanks (see "Required variables" below)
```

Then trigger a deploy by pushing to `main` (staging) — the workflow ships the code, builds the images on the host, runs migrations, and brings the stack up.

## Required variables

See [`.env.example`](.env.example) for the full template. The blanks you must fill (no good defaults):

| Variable | Notes |
|---|---|
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `FRONTEND_HOST` | Full public URL, e.g. `http://<host>:8080` |
| `BACKEND_CORS_ORIGINS` | Same origin as `FRONTEND_HOST` (comma-separated if multiple) |
| `VITE_API_URL` | Same origin as `FRONTEND_HOST` (build-time) |
| `POSTGRES_SERVER` | Hostname/IP of your Postgres instance |
| `POSTGRES_PORT` | Whatever port Postgres listens on (default 5432) |
| `POSTGRES_PASSWORD` | Password of `POSTGRES_USER` |
| `FIRST_SUPERUSER` | Email used for the initial admin login |
| `FIRST_SUPERUSER_PASSWORD` | Strong password for the first login |

`POSTGRES_DB=prata_sys` is the convention — create that database in your Postgres instance once before the first deploy.

## GitHub Secrets used by the deploy workflow

The workflow connects to the deploy host over a private mesh via Tailscale, then uses SSH. You'll need both Tailscale OAuth credentials and the usual SSH/path/URL secrets.

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

### Deploy SSH + targets

| Secret | Value |
|---|---|
| `DEPLOY_HOST_STAGING` | Tailscale hostname (MagicDNS) or IP of the staging host |
| `DEPLOY_HOST_PRODUCTION` | Tailscale hostname/IP of the prod host (can be the same machine) |
| `DEPLOY_USER` | SSH user on the deploy host |
| `DEPLOY_SSH_KEY` | Private key matching `~/.ssh/authorized_keys` of `DEPLOY_USER` |
| `DEPLOY_PATH_STAGING` | Absolute path on the host where staging code lives |
| `DEPLOY_PATH_PRODUCTION` | Absolute path on the host where production code lives |
| `VITE_API_URL_STAGING` | Build-time API URL for staging (matches staging `FRONTEND_HOST`) |
| `VITE_API_URL_PRODUCTION` | Build-time API URL for production |

## Common operations

Run on the deploy host (`cd <DEPLOY_PATH>`):

```bash
# Tail logs
docker compose -f compose.prod.yml logs -f

# Manual rebuild + restart
docker compose -f compose.prod.yml up -d --build

# Stop the stack
docker compose -f compose.prod.yml down

# Reset containers (Postgres data lives outside the compose so it's untouched)
docker compose -f compose.prod.yml down -v
docker compose -f compose.prod.yml up -d --build
```

## Backup

This stack is stateless except for the Caddy volumes (`caddy-data`, `caddy-config`). Application data lives in your external Postgres — back it up via your normal database backup policy.
