# Security Audit — prata-sys
_Auditor: Staff Security Engineer (Fable) · Date: 2026-07-12 · Scope: full repo · Mode: audit-only_

## Summary

Overall posture is mostly sound at the plumbing level (parameterized queries throughout,
`SELECT FOR UPDATE` for stock, constant-time auth, single-use signed reset tokens, enumeration-aware
recovery message), but the **access-control model is broken at the top**. The single most urgent item
is **SEC-001**: `POST /api/v1/users/signup` is unauthenticated and creates users with the
default `role="admin"`, so anyone on the network can mint an admin account. Chained with **SEC-002**
(the `manage_users` permission can set `is_superuser` via mass assignment), an unauthenticated
attacker can escalate all the way to superuser and fully own the system, including all client PII
and financial records.

Findings by severity: **1 Critical, 2 High, 3 Medium, 5 Low/Hardening.**

## Resolution status

SEC-001 through SEC-006 have been fixed and are tracked in two PRs:

- **SEC-001, SEC-002, SEC-003** → PR #133 (branch `wfoschiera/security/user-access-control-hardening`), issues #121/#122/#123.
- **SEC-004, SEC-005, SEC-006** → PR #134 (branch `wfoschiera/security/auth-rate-limiting`), issues #124/#125/#126.

- **SEC-008, SEC-009, SEC-010, SEC-011** → hardening PR (branch `wfoschiera/security/hardening-headers-cors-secrets`), issues #137/#138/#139/#140.

SEC-007 remains open (deferred to its own migration effort; see `docs/adr/httponly-cookie-auth.md`).
Note: SEC-003's fix invalidates all live sessions on deploy (the JWT now carries a version claim
that is checked fail-closed).

---

## Critical

- [x] **[SEC-001] Unauthenticated signup grants `role=admin` (full account takeover)** — `backend/app/models.py:29`, `backend/app/api/routes/users.py:150-163`, `backend/app/crud.py:81-88`
  - **Actor / attack:** Any unauthenticated attacker who can reach the API. `POST /api/v1/users/signup` with `{email, password, full_name}`.
  - **Impact:** `UserBase.role` defaults to `UserRole.admin` (models.py:29). `UserRegister` (models.py:37-41) has no `role` field, so `register_user` does `UserCreate.model_validate(user_in)` (users.py:161) and `crud.create_user` persists every field via `User.model_validate(...)` (crud.py:82) — the new account is created as **admin**. `ROLE_PERMISSIONS[admin]` grants `manage_users`, `manage_clients`, `manage_services`, `manage_estoque`, `manage_orcamentos`, `manage_financeiro`, `manage_fornecedores`, etc. — effectively the whole business system, including all client CPF/CNPJ/address PII and financial transactions. With SEC-002 this escalates to superuser.
  - **Evidence:** `role: UserRole = UserRole.admin` (models.py:29); `user_create = UserCreate.model_validate(user_in)` (users.py:161); `db_obj = User.model_validate(user_create, ...)` (crud.py:82).
  - **OWASP:** A01:2021 Broken Access Control (privilege assignment).
  - **Remediation:** Signup must never confer a privileged role. Either (a) remove/guard `POST /users/signup` entirely (this is an internal B2B tool — user creation is already covered by the `manage_users`-guarded `POST /users/`), or (b) force `role=UserRole.client` and `is_superuser=False` when building `UserCreate` from `UserRegister`, and change the `UserBase.role` default to the least-privileged role (`client`) so no code path accidentally mints an admin. Do not rely on the default.
  - **Regression test:** In `backend/tests/api/routes/test_users.py`, POST `/users/signup`, then assert the created user's `role == "client"` and `is_superuser is False`; and assert the account cannot reach a `manage_*` endpoint (401/403).

---

## High

- [x] **[SEC-002] `manage_users` allows self-promotion to superuser via mass assignment** — `backend/app/models.py:33-46`, `backend/app/api/routes/users.py:52-68` & `~186-219`, `backend/app/crud.py:81-102`
  - **Actor / attack:** Any user with the `manage_users` permission (every `admin`, including a self-registered one from SEC-001). `PATCH /api/v1/users/{user_id}` (or `POST /users/`) with `{"is_superuser": true}` or `{"role": "admin"}`.
  - **Impact:** `UserCreate` and `UserUpdate` both inherit `is_superuser` and `role` from `UserBase` (models.py:33, 44). `crud.update_user` applies `user_in.model_dump(exclude_unset=True)` via `sqlmodel_update` (crud.py:92-98) with no allow-list, and `crud.create_user` copies all fields. So a non-superuser admin can set `is_superuser=True` on their own account and gain the global superuser bypass in `require_permission` (deps.py:76-77), defeating the entire permission system. `manage_users` is therefore equivalent to superuser.
  - **Evidence:** `class UserUpdate(UserBase)` (models.py:44) → inherits `is_superuser: bool` (models.py:27); `db_user.sqlmodel_update(user_data, ...)` (crud.py:98); superuser bypass at deps.py:76-77.
  - **OWASP:** A01:2021 Broken Access Control; A04:2021 Insecure Design (mass assignment).
  - **Remediation:** Split the API schema from the privilege fields: `is_superuser` (and arguably `role`) must only be settable by a superuser, not by `manage_users`. Introduce an admin-facing update schema without `is_superuser`, and gate any `is_superuser`/role-elevation change behind `get_current_active_superuser`. Reject unknown/privileged fields explicitly rather than relying on inheritance.
  - **Regression test:** As a `manage_users` (non-superuser) admin, `PATCH /users/{self}` with `{"is_superuser": true}` and assert it is rejected (403) and the DB value stays `False`; same for creating a superuser via `POST /users/`.

- [x] **[SEC-003] Password reset / deactivation does not revoke live access tokens (8-day JWTs, no jti)** — `backend/app/core/security.py:29-33`, `backend/app/core/config.py:36`, `backend/app/api/deps.py:30-46`, `backend/app/api/routes/login.py:83-106`
  - **Actor / attack:** An attacker holding a stolen/leaked access token (e.g. via the localStorage XSS surface in SEC-007). Victim or admin resets the password or deactivates the account to remediate.
  - **Impact:** Access tokens carry only `{exp, sub}` (security.py:31) — no `jti` and the `User` has no token-version/`password_changed_at`. `get_current_user` only checks the signature, `exp`, and `is_active` (deps.py:41-45). A password reset (login.py:100) does not invalidate previously issued tokens, and tokens live for **8 days** (config.py:36). So the standard "reset the password to kick out the attacker" response does not work — the stolen token keeps full access until it naturally expires.
  - **Evidence:** `to_encode = {"exp": expire, "sub": str(subject)}` (security.py:31); `ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 8` (config.py:36); no token invalidation in `reset_password` (login.py:83-106).
  - **OWASP:** A07:2021 Identification and Authentication Failures.
  - **Remediation:** Add a per-user token invalidation signal — e.g. a `token_version` (or `security_stamp`) column on `User`, embed it in the JWT, and compare in `get_current_user`; bump it on password change and deactivation. Consider shortening access-token lifetime and adding refresh-token rotation. At minimum, deactivating a user should immediately deny their tokens (already true via `is_active`), but password reset should bump the version too.
  - **Regression test:** Issue a token, reset the password, then call `/login/test-token` with the old token and assert 401/403.

---

## Medium

- [x] **[SEC-004] Login rate limit is a single global bucket and off outside production** — `backend/app/core/limiter.py:15-19`, `backend/app/api/routes/login.py:26-27`, `Caddyfile:12-15`, `compose.prod.yml:22`
  - **Actor / attack:** Any client. `get_remote_address` reads `request.client.host`, but the backend (`fastapi run`, compose.prod.yml:22) sits behind Caddy (`reverse_proxy backend:8000`) with no trusted-proxy / forwarded-IP handling.
  - **Impact:** Every request appears to originate from Caddy's container IP, so the `@limiter.limit("5/minute")` on login (login.py:27) is one **shared** bucket for all users, not per-client. Two consequences: (1) an attacker distributed across IPs is throttled as a whole but so is everyone — the control gives no per-attacker isolation; (2) any single actor can consume the 5/min and **deny login to all legitimate users** (auth DoS). Additionally, `enabled = settings.ENVIRONMENT == "production"` (limiter.py:18) means rate limiting is entirely off in `staging`.
  - **Evidence:** `key_func=get_remote_address` (limiter.py:16); Caddy `reverse_proxy backend:8000` (Caddyfile:14); no `--forwarded-allow-ips`/ProxyHeaders on the uvicorn/fastapi run command (compose.prod.yml:22).
  - **OWASP:** A04:2021 Insecure Design; A07:2021.
  - **Remediation:** Trust the proxy and key on the real client IP — configure uvicorn/`fastapi run` proxy headers (`--forwarded-allow-ips`) and have Caddy set `X-Forwarded-For`, then use a `key_func` that reads the forwarded client IP. Enable limiting in `staging` too. Add limits to the endpoints in SEC-005.
  - **Regression test:** Behind the proxy config, assert distinct client IPs get independent buckets (integration test with spoofed/forwarded IPs), and that exhausting one IP does not 429 another.

- [x] **[SEC-005] Sensitive auth endpoints are unthrottled** — `backend/app/api/routes/login.py:59-106`, `backend/app/api/routes/users.py:150-163`, `backend/app/core/limiter.py:17`
  - **Actor / attack:** Unauthenticated attacker hitting `POST /password-recovery/{email}`, `POST /reset-password/`, and `POST /users/signup` — none carry a `@limiter.limit`, and `default_limits=[]` (limiter.py:17) means no global fallback.
  - **Impact:** `/password-recovery` → email-bombing a victim's inbox and SMTP-cost abuse. `/signup` → unlimited automated account creation which, per SEC-001, means **unlimited unauthenticated admin accounts**. `/reset-password` → unbounded token-submission attempts (mitigated by the tokens being signed JWTs, so not brute-forceable, but still abusable).
  - **Evidence:** only `/login/access-token` is decorated (login.py:26-27); recovery/reset/signup have no limiter; `default_limits=[]` (limiter.py:17).
  - **OWASP:** A04:2021 Insecure Design.
  - **Remediation:** Add `@limiter.limit(...)` to `/password-recovery/{email}`, `/reset-password/`, and `/users/signup` (once SEC-001 is fixed), keyed on the real client IP (see SEC-004) and/or the target email. Set a conservative `default_limits` fallback.
  - **Regression test:** Hammer each endpoint past the limit and assert 429.

- [x] **[SEC-006] User-enumeration timing oracle on password recovery** — `backend/app/api/routes/login.py:59-80`, `backend/app/utils.py:33-55`
  - **Actor / attack:** Unauthenticated attacker probing `POST /password-recovery/{email}` and measuring response latency.
  - **Impact:** The endpoint correctly returns a constant message, but it only does work — `generate_password_reset_token` + the **synchronous** `send_email` (utils.py:54, blocking SMTP round-trip) — when the user exists (login.py:68-77). The latency difference between "email sent" and "no-op" is easily measurable, defeating the anti-enumeration intent and leaking which emails are registered.
  - **Evidence:** `if user:` guards the send (login.py:68); `response = message.send(...)` is synchronous (utils.py:54).
  - **OWASP:** A07:2021 Identification and Authentication Failures.
  - **Remediation:** Make the work uniform: send email out-of-band (background task/queue) so the request returns immediately regardless of user existence, and/or normalize response timing. Combine with SEC-005 rate limiting.
  - **Regression test:** Statistical timing test asserting the latency distributions for known-existing vs known-absent emails overlap (or that email dispatch is enqueued, not awaited, in the request path).

---

## Low / Hardening

- [ ] **[SEC-007] JWT stored in `localStorage` (XSS → token theft)** — `frontend/src/main.tsx:19-20`, `frontend/src/hooks/useAuth.ts`, `docs/adr/httponly-cookie-auth.md`
  - **Actor / attack:** An attacker with any XSS foothold in the SPA reads `localStorage.getItem("access_token")`.
  - **Impact:** Full account impersonation; amplified by SEC-003 (the stolen token can't be revoked and lasts 8 days). **Already documented and intentionally deferred** in `docs/adr/httponly-cookie-auth.md` (migration to httpOnly SameSite=Strict cookies). Listed here so the risk stays visible and is re-prioritized alongside SEC-003.
  - **OWASP:** A07:2021; A05:2021.
  - **Remediation:** Execute the deferred ADR (httpOnly cookie auth), or at minimum ship a strict CSP and shorten token lifetime while the ADR is pending.
  - **Regression test:** Covered by the ADR's plan; add a Playwright test asserting the token is not readable from `document`/`localStorage` after the migration.

- [x] **[SEC-008] TOCTOU in single-use reset-token consumption** — `backend/app/api/routes/login.py:88-105`, `backend/app/utils.py:138-161`
  - **Actor / attack:** Concurrent requests replaying the same valid reset token before it is marked used.
  - **Impact:** `is_token_used` (utils.py:138) is checked, then `consume_password_reset_token` (utils.py:155) inserts the used-hash only after the password is already updated (login.py:100 then 105). Two racing requests can both pass the check and both reset the password; the second `consume` then fails on the unique `token_hash` (500) after the write already happened. Low impact but it breaks the single-use guarantee under concurrency.
  - **OWASP:** A04:2021 Insecure Design.
  - **Remediation:** Make consumption atomic and first: insert the used-token row (relying on the unique constraint) inside the same transaction *before* updating the password, and treat an IntegrityError as "token already used" → 400.
  - **Regression test:** Fire two concurrent `/reset-password` calls with the same token and assert exactly one succeeds.

- [x] **[SEC-009] Permissive CORS (`allow_credentials=True` + wildcard methods/headers)** — `backend/app/main.py:32-39`
  - **Actor / attack:** Malicious web origin. Impact is limited today because origins are an explicit allow-list (config.py `all_cors_origins`) and auth uses a bearer token in localStorage, not cookies — so credentialed cross-origin requests don't carry ambient auth.
  - **Impact:** `allow_methods=["*"]` and `allow_headers=["*"]` with `allow_credentials=True` is broader than needed and becomes dangerous if auth ever moves to cookies (see SEC-007 ADR) or if the origin list is loosened.
  - **OWASP:** A05:2021 Security Misconfiguration.
  - **Remediation:** Restrict `allow_methods`/`allow_headers` to those actually used; keep the explicit origin allow-list; re-audit CORS as part of the cookie-auth migration.
  - **Regression test:** Assert a disallowed origin/method is rejected by the CORS preflight.

- [x] **[SEC-010] `SECRET_KEY` silently falls back to a random per-process value if unset in production** — `backend/app/core/config.py:34, 97-116`
  - **Actor / attack:** Operational misconfiguration (SECRET_KEY not provided), not a direct attacker.
  - **Impact:** `SECRET_KEY: str = secrets.token_urlsafe(32)` (config.py:34) means an unset key yields a different secret per worker/restart. The guard only rejects the literal `"changethis"` (config.py:98), not "unset". With 2 workers (compose.prod.yml:22), tokens signed by one worker fail on another; every restart invalidates all sessions. This is availability/consistency rather than confidentiality (it fails closed), but a missing prod secret should be a hard error. Note: prod compose does pass `SECRET_KEY=${SECRET_KEY?Variable not set}` (compose.prod.yml:38), which mitigates this in the documented deploy path.
  - **OWASP:** A05:2021 Security Misconfiguration.
  - **Remediation:** In non-local environments, require `SECRET_KEY` to be explicitly set (raise if it fell back to the generated default), mirroring the `changethis` guard.
  - **Regression test:** Instantiate `Settings(ENVIRONMENT="production")` with no `SECRET_KEY` and assert it raises.

- [x] **[SEC-011] Missing HTTP security headers** — `Caddyfile:9-20`, `backend/app/main.py`
  - **Actor / attack:** Network/browser-side attacks (clickjacking, MIME sniffing, downgrade).
  - **Impact:** No `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`/frame-ancestors CSP, or `Content-Security-Policy` are set at the Caddy or app layer. A CSP in particular is the main defense-in-depth mitigation for the localStorage-token XSS risk (SEC-007).
  - **OWASP:** A05:2021 Security Misconfiguration.
  - **Remediation:** Add a `header` block in the Caddyfile (HSTS, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`/`frame-ancestors 'none'`, and a tuned `Content-Security-Policy`). Note TLS is terminated upstream in this topology, so scope HSTS accordingly.
  - **Regression test:** Assert the security headers are present on a proxied response.

---

## Verified-safe / Out of scope

Examined and found NOT vulnerable (or intentionally deferred), so a reader knows they were checked:

- **SQL injection:** No raw SQL, `text()`, f-string, or `.format()` queries in `app/api`, `crud.py`, or `utils.py`; all use SQLModel/SQLAlchemy `select()`. Raw SQL exists only in Alembic migrations as static strings (e.g. `sa.text('cnpj IS NOT NULL')` partial-index predicate) — no interpolation. (A03:2021 — not present.)
- **Stock concurrency:** `reserve_stock_for_service` and deduction paths use `.with_for_update()` with FIFO ordering (`backend/app/crud.py:393, 1113`) — correct row-level locking against double-spend/negative stock.
- **Credential verification:** `crud.authenticate` (crud.py:116-131) runs a constant `DUMMY_HASH` verify when the user is absent to blunt timing attacks, and uses `verify_and_update` for transparent rehashing. Argon2 (pwdlib) with secure prod params; weakened params are gated to non-production for test speed only (security.py:13-16).
- **Password reset tokens:** Signed JWTs (`nbf`/`exp`, sub=email) — not brute-forceable — plus a SHA-256 single-use blocklist (`UsedPasswordResetToken`) and an enumeration-resistant recovery message. (Residual issues tracked as SEC-005/006/008.)
- **Stored XSS via company letterhead:** No `dangerouslySetInnerHTML`/`innerHTML` anywhere in `frontend/src`; `company_name`/`logo_url` render through React's automatic escaping. Setting them is superuser-only (`settings.py:24-27`).
- **`/private/users/`:** Unauthenticated user-creation route is mounted only when `ENVIRONMENT == "local"` (`api/main.py:43-44`) — not exposed in production.
- **CI default secrets:** `SECRET_KEY: changethis` / `POSTGRES_PASSWORD: changethis` in `.github/workflows/deploy.yml` and `test-backend.yml` are confined to the ephemeral test job (`ENVIRONMENT: local`, throwaway Postgres). They are not build args and never enter the images; prod requires real secrets via `?Variable not set` (compose.prod.yml:38-40) and the config guard rejects `changethis` in non-local. Acceptable.
- **Object-level authz (IDOR):** Resource routes are guarded by `manage_*`/`view_*` permissions; the `client` role has an empty permission set (`permissions.py`) and there is no client portal yet, so non-staff cannot reach client/service/financial data. Coarse but adequate for the current internal-staff-only model — revisit when the client portal ships.
- **Readiness probe:** `/utils/readiness/` returns a generic `"database unavailable"` (utils.py:47-54) — no DB/connection detail leakage.

---

_Mode reminder: this pass made no code, config, migration, or dependency changes — this file is the only artifact. Fix order: **SEC-001 → SEC-002 → SEC-003**, then the Medium rate-limiting cluster (SEC-004/005/006)._
