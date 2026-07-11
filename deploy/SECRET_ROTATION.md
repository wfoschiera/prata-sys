# Secret rotation runbook

Every secret in the prata-sys deployment, where it lives, and exactly how to rotate it safely.

Rotate in this order (least → most likely to lock you out): app secrets → Postgres password → CI network credentials → deploy SSH key. Do the SSH key **last** and follow the add-verify-remove dance so you can't lock yourself out.

## Fill these in for your environment (kept out of the repo)

## A reliable way to re-check the container name any time (in case the number ever changes after a recreate):
```bash
ssh -i ~/.ssh/id_prata_sys gh-deploy@192.168.1.244 \
  'sudo docker ps --filter name=postgres --format "{{.Names}}"'
```

Set these once in your shell before running the commands below. Use your real values locally — **do not commit them**.

```bash
HOST=<deploy-host-or-ip>          # host the deploy workflow SSHes into
DEPLOY_USER=<deploy-user>         # SSH user the workflow uses
KEY=~/.ssh/<deploy-key>           # private key for DEPLOY_USER
DEPLOY_PATH=<deploy-path>         # app stack dir, e.g. /opt/prata-sys
PG_DIR=<postgres-stack-dir>       # Postgres stack dir (has its own compose.yml + .env)
PG_CONTAINER=<postgres-container> # from `docker ps` (e.g. postgres-postgres-1)
APP_URL=<http://host:8080>        # how you reach the app in a browser
SUPERUSER_EMAIL=<admin-email>     # the FIRST_SUPERUSER email
REPO=<owner>/<repo>               # GitHub repo, e.g. you/prata-sys

# Helper to run a command on the server. A function (not a variable) so it works
# in both bash and zsh — zsh does not word-split an unquoted "$SSH" variable.
dssh() { ssh -i "$KEY" "$DEPLOY_USER@$HOST" "$@"; }

# Generators:
python3 -c "import secrets; print(secrets.token_urlsafe(32))"   # for SECRET_KEY
openssl rand -base64 24                                          # for passwords
```

- Editing the server `.env` then re-running `up -d` recreates the affected containers with the new value.

---

## 1. `SECRET_KEY` — JWT signing key (server `.env`)

Rotating this **logs everyone out** (all existing tokens become invalid). No coordination needed otherwise.

```bash
NEW=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
dssh "sed -i 's|^SECRET_KEY=.*|SECRET_KEY=$NEW|' $DEPLOY_PATH/.env \
  && cd $DEPLOY_PATH \
  && sudo docker compose -f compose.prod.yml up -d backend"
# Verify:
curl -s -o /dev/null -w '%{http_code}\n' $APP_URL/api/v1/utils/health-check/   # expect 200
```

---

## 2. `POSTGRES_PASSWORD` — DB role password (Postgres role + both `.env` files)

The **running password lives in the database**, not the `.env`. The `.env` value only matters at first init (already past) and for keeping files consistent. So change the role first, then the app config.

```bash
NEW=$(openssl rand -base64 24)

# a) Change the role password in the live database (takes effect immediately):
dssh "sudo docker exec $PG_CONTAINER psql -U prata_sys -d prata_sys \
  -c \"ALTER USER prata_sys PASSWORD '$NEW';\""

# b) Update both .env files so they stay consistent with the DB:
dssh "sed -i 's|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$NEW|' $DEPLOY_PATH/.env \
  && sed -i 's|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$NEW|' $PG_DIR/.env"

# c) Recreate the backend so it reconnects with the new password:
dssh "cd $DEPLOY_PATH && sudo docker compose -f compose.prod.yml up -d backend"

# Verify:
dssh "sudo docker inspect --format '{{.State.Health.Status}}' \$(cd $DEPLOY_PATH && sudo docker compose -f compose.prod.yml ps -q backend)"   # expect healthy
```

> If a special character in the password ever breaks `sed`, edit the files by hand with `dssh -t "nano $DEPLOY_PATH/.env"` instead.

---

## 3. `FIRST_SUPERUSER_PASSWORD` — the admin login password

⚠️ **Important:** the seed script only sets this when the user is *first created*. It does **not** update an existing user on restart, so editing `.env` alone will **not** change your live login. Change the real password one of two ways:

**Option A — via the app (simplest):** log in at `$APP_URL` as the superuser → user settings → change password.

**Option B — via SQL** (if you're locked out). Generate the hash inside the backend container, then update the row:

```bash
NEW=$(openssl rand -base64 24)
BACKEND=$(dssh "cd $DEPLOY_PATH && sudo docker compose -f compose.prod.yml ps -q backend")
HASH=$(dssh "sudo docker exec $BACKEND python -c \
  \"from app.core.security import get_password_hash; print(get_password_hash('$NEW'))\"")
dssh "sudo docker exec $PG_CONTAINER psql -U prata_sys -d prata_sys \
  -c \"UPDATE \\\"user\\\" SET hashed_password='$HASH' WHERE email='$SUPERUSER_EMAIL';\""
echo "New superuser password: $NEW"
```

Then update `.env` for consistency (used only if the DB is ever wiped and re-seeded):

```bash
dssh "sed -i 's|^FIRST_SUPERUSER_PASSWORD=.*|FIRST_SUPERUSER_PASSWORD=$NEW|' $DEPLOY_PATH/.env"
```

---

## 4. CI network credentials — `TS_OAUTH_CLIENT_ID` / `TS_OAUTH_SECRET` (GitHub secrets)

These let the GitHub runner join your private network to reach the deploy host.

1. In your network provider's admin console, **create a new OAuth client** with the scope/tag the deploy workflow expects (see `deploy/README.md`). Copy the new **client ID** and **secret**.
2. Update the GitHub secrets from your laptop:
   ```bash
   printf 'NEW_CLIENT_ID'     | gh secret set TS_OAUTH_CLIENT_ID -R "$REPO"
   printf 'NEW_CLIENT_SECRET' | gh secret set TS_OAUTH_SECRET    -R "$REPO"
   ```
3. **Verify before revoking the old one**: re-run the latest deploy and confirm the network-connect step succeeds:
   ```bash
   gh run list --workflow=deploy.yml -R "$REPO" --limit 1   # note the run id
   gh run rerun <run-id> -R "$REPO"
   ```
4. Once green, **revoke the old OAuth client** in the admin console.

---

## 5. `DEPLOY_SSH_KEY` — deploy SSH key (GitHub secret + server `authorized_keys`)

Do this **last**. Use add → verify → remove so a mistake never locks you out (you keep the old key working until the new one is proven).

```bash
# a) Generate a fresh dedicated keypair:
ssh-keygen -t ed25519 -f ~/.ssh/deploy_new -C 'prata-sys-deploy' -N ''
cat ~/.ssh/deploy_new.pub
```

Add the **new public key** to `DEPLOY_USER`'s authorized keys **alongside** the old one (keep both for now). Use your host's user-management UI if it manages `authorized_keys` for you; otherwise append it directly:

```bash
# Only if your host does NOT manage authorized_keys through a UI:
dssh "printf '%s\n' \"$(cat ~/.ssh/deploy_new.pub)\" >> ~/.ssh/authorized_keys"
```

```bash
# c) Verify the NEW key works:
ssh -i ~/.ssh/deploy_new $DEPLOY_USER@$HOST 'echo NEW KEY OK'

# d) Point GitHub at the new private key:
gh secret set DEPLOY_SSH_KEY -R "$REPO" < ~/.ssh/deploy_new

# e) Confirm a real deploy still works (re-run latest, or push a trivial commit):
gh run rerun <latest-deploy-run-id> -R "$REPO"
```

Once the deploy is green with the new key:

```bash
# f) Remove the OLD public key from the server's authorized_keys (via the UI, or edit the file).
# g) Retire the old private key locally and promote the new one to your KEY path:
mv "${KEY/#\~/$HOME}" "${KEY/#\~/$HOME}.retired"
mv ~/.ssh/deploy_new "${KEY/#\~/$HOME}"
mv ~/.ssh/deploy_new.pub "${KEY/#\~/$HOME}.pub"
```

---

## 6. Cleanup / not currently set

- **`DEPLOY_HOST_IP`** — a stale, unused GitHub secret from an earlier attempt. Delete it:
  ```bash
  gh secret delete DEPLOY_HOST_IP -R "$REPO"
  ```
- **`SMTP_PASSWORD`, `SENTRY_DSN`** — empty unless you configure email/Sentry. They live only in the server `.env` and rotate like section 1.

---

## Final verification (after all rotations)

```bash
# App healthy and reachable:
curl -s -o /dev/null -w 'health: %{http_code}\n' $APP_URL/api/v1/utils/health-check/
# Login works with the new superuser password (replace PW):
curl -s -o /dev/null -w 'login: %{http_code}\n' -X POST \
  $APP_URL/api/v1/login/access-token \
  -d "username=$SUPERUSER_EMAIL&password=PW"
# CD still works end-to-end: push any trivial change to main and watch the deploy go green.
```
