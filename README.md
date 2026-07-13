# prata-sys

**prata-sys** is a business management system for a **water well drilling company** in
Brazil. It manages clients, service orders (perfuração / manutenção), suppliers,
inventory, commercial quotes, and finances — with role-based access for admins,
finance users, and clients.

Built on the
[FastAPI Full-Stack Template](https://github.com/fastapi/full-stack-fastapi-template).

## What it does

- **Clientes** — register people (CPF) or companies (CNPJ) with structured Brazilian
  addresses.
- **Serviços** — service orders with a full lifecycle (requested → scheduled →
  executing → completed / cancelled) and automatic stock reservation and deduction.
- **Orçamentos** — commercial quotes linked to the product catalog, with company
  letterhead, price-visibility toggles, and one-time conversion into a service.
- **Estoque** — product types, products, and physical stock units with prediction
  (green/yellow/red) and concurrency-safe reservation.
- **Financeiro** — receitas/despesas transactions and a dashboard with KPIs and a
  6-month chart.
- **Fornecedores** — suppliers with contacts, categories, and bank details.
- **RBAC** — `admin`, `finance`, and `client` roles with per-user overrides.

For the full domain glossary, feature inventory, and roadmap, see
[`docs/domain-model.md`](docs/domain-model.md).

## Tech stack

| Layer       | Technology                                       |
|-------------|--------------------------------------------------|
| Backend     | Python 3.14+, FastAPI, SQLModel, PostgreSQL      |
| Migrations  | Alembic                                          |
| Auth        | JWT (PyJWT), Argon2/Bcrypt (pwdlib)              |
| Frontend    | React 19, TypeScript, Vite, TanStack Router/Query |
| UI          | Tailwind CSS v4, shadcn/ui, Radix UI             |
| API client  | Auto-generated from OpenAPI (openapi-ts), native fetch |
| Testing     | Pytest (backend), Playwright (E2E frontend)      |
| Linting     | Ruff + MyPy (backend), Biome (frontend)          |
| Deploy      | Docker Compose + Caddy (single host, GHCR images) |
| Pkg mgmt    | uv (Python), Bun (JavaScript)                    |

## Getting started

Local dev runs natively (backend and frontend on the host; only Postgres and Mailpit in
Docker). First-time setup:

```bash
bash scripts/dev-setup.sh
```

Then run the backend (`:8000`) and frontend (`:5173`). Full instructions — prerequisites,
daily workflow, database admin, client regeneration, tests — are in
[`development.md`](development.md).

## Documentation

| Doc | What it covers |
|---|---|
| [`ONBOARDING.md`](ONBOARDING.md) | New-developer walkthrough: architecture, repo map, data model, subsystems |
| [`development.md`](development.md) | Local development setup and daily workflow |
| [`docs/domain-model.md`](docs/domain-model.md) | Domain glossary, feature inventory, roadmap |
| [`docs/pitfalls.md`](docs/pitfalls.md) | Stack-specific gotchas (Zod v4, RHF, SQLModel, Python 3.14) |
| [`docs/git-worktrees.md`](docs/git-worktrees.md) | Working with git worktrees (`wt`) |
| [`docs/adr/`](docs/adr/) | Architecture Decision Records |
| [`backend/README.md`](backend/README.md) · [`frontend/README.md`](frontend/README.md) | Per-package setup |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Contribution guidelines |

## Deployment

prata-sys deploys as a Docker Compose stack behind Caddy on a single host: images are
built in CI and pushed to GHCR, and the host pulls on merge to `main` (over a Tailscale
mesh). Postgres is external to the stack. Full runbook, required variables, and secrets:
[`deploy/README.md`](deploy/README.md). Secret rotation: [`deploy/SECRET_ROTATION.md`](deploy/SECRET_ROTATION.md).

## License

Licensed under the terms of the MIT license.
