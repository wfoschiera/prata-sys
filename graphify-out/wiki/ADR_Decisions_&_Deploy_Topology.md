# ADR Decisions & Deploy Topology

> 29 nodes · cohesion 0.09

## Key Concepts

- **Production Deploy Topology (single Docker Compose host)** (5 connections) — `deploy/README.md`
- **Playwright E2E Workflow (2 shards)** (5 connections) — `.github/workflows/playwright.yml`
- **Frontend App Guide (Vite/React19/TanStack/Tailwind/shadcn)** (4 connections) — `frontend/README.md`
- **CI Build Job (Docker Images)** (4 connections) — `.github/workflows/deploy.yml`
- **Deploy Job (Tailscale + SSH + Compose)** (4 connections) — `.github/workflows/deploy.yml`
- **Test Backend Workflow (pytest, coverage >= 95%)** (4 connections) — `.github/workflows/test-backend.yml`
- **ADR Decision: localStorage -> httpOnly cookies (DEFERRED)** (3 connections) — `docs/adr/httponly-cookie-auth.md`
- **Auto-generated OpenAPI Client Rule (never hand-write API calls)** (3 connections) — `frontend/CLAUDE.md`
- **VITE_API_URL Environment Variable** (3 connections) — `frontend/README.md`
- **GHCR Images (prata-sys-backend / prata-sys-frontend)** (3 connections) — `.github/workflows/deploy.yml`
- **Deploy Workflow (push to main)** (3 connections) — `.github/workflows/deploy.yml`
- **dorny/paths-filter Change Detection Pattern** (3 connections) — `.github/workflows/lint-frontend.yml`
- **Current State: JWT in localStorage (XSS-readable)** (2 connections) — `docs/adr/httponly-cookie-auth.md`
- **Standalone Postgres Compose Example** (2 connections) — `deploy/postgres.compose.example.yml`
- **Caddy Reverse Proxy (single public port)** (2 connections) — `deploy/README.md`
- **External Postgres (outside app stack)** (2 connections) — `deploy/README.md`
- **Same-Origin SPA Deployment (empty VITE_API_URL)** (2 connections) — `deploy/README.md`
- **src/main.tsx (app bootstrap, OpenAPI.TOKEN wiring)** (2 connections) — `frontend/index.html`
- **Tailscale Deploy Mesh (tag:ci-prata-sys)** (2 connections) — `.github/workflows/deploy.yml`
- **Lint Frontend Workflow** (2 connections) — `.github/workflows/lint-frontend.yml`
- **scripts/generate-client.sh** (2 connections) — `.github/workflows/playwright.yml`
- **coverage-html Artifact (backend/htmlcov)** (2 connections) — `.github/workflows/smokeshow.yml`
- **Smokeshow Coverage Upload Workflow** (2 connections) — `.github/workflows/smokeshow.yml`
- **prata-net External Docker Network** (1 connections) — `deploy/postgres.compose.example.yml`
- **Biome Lint/Format** (1 connections) — `frontend/CLAUDE.md`
- *... and 4 more nodes in this community*

## Relationships

- No strong cross-community connections detected

## Source Files

- `.github/workflows/deploy.yml`
- `.github/workflows/lint-frontend.yml`
- `.github/workflows/playwright.yml`
- `.github/workflows/smokeshow.yml`
- `.github/workflows/test-backend.yml`
- `deploy/README.md`
- `deploy/postgres.compose.example.yml`
- `docs/adr/httponly-cookie-auth.md`
- `frontend/CLAUDE.md`
- `frontend/README.md`
- `frontend/index.html`

## Audit Trail

- EXTRACTED: 58 (81%)
- INFERRED: 14 (19%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
