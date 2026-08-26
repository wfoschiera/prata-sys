# Production Deploy Topology

> 10 nodes · cohesion 0.27

## Key Concepts

- **Prod Backend Service (fastapi run, 2 workers)** (5 connections) — `compose.prod.yml`
- **Caddy Service (only published host port)** (4 connections) — `compose.prod.yml`
- **Pull-based Deploy Model** (3 connections) — `compose.prod.yml`
- **GitHub Actions CI/CD Deploy Pipeline (GHCR + Tailscale)** (3 connections) — `ONBOARDING.md`
- **Prod Frontend Service (nginx SPA)** (2 connections) — `compose.prod.yml`
- **Copier Project Template Config** (2 connections) — `copier.yml`
- **prata-sys** (2 connections) — `README.md`
- **prata-net External Docker Network** (1 connections) — `compose.prod.yml`
- **Dependabot Daily Dependency Updates (npm + python)** (1 connections) — `dependabot.yml`
- **Caddy Reverse Proxy** (1 connections) — `ONBOARDING.md`

## Relationships

- No strong cross-community connections detected

## Source Files

- `ONBOARDING.md`
- `README.md`
- `compose.prod.yml`
- `copier.yml`
- `dependabot.yml`

## Audit Trail

- EXTRACTED: 18 (75%)
- INFERRED: 6 (25%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
