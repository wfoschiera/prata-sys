# prata-sys — CLAUDE.md

## Project Overview

**prata-sys** is a business management system for a **water well drilling company** in Brazil. It manages clients, service orders, suppliers, and internal operations.

The project is built on the [FastAPI Full-Stack Template](https://github.com/fastapi/full-stack-fastapi-template).

### Implemented (Phases 1–9)
- **Cadastro** (registration) for Admins, Finance users, and Clients (CPF/CNPJ) with structured address fields (bairro, city, state, CEP)
- **Serviços** (service orders): full lifecycle (requested → scheduled → executing → completed / cancelled), stock reservation/deduction on transitions, status audit log, deletion/item mutation guards
- **RBAC**: role-based permissions (`admin`, `finance`, `client`) with per-user overrides, per-request caching
- **Financeiro**: transaction management (receitas/despesas), finance dashboard with KPI cards and 6-month chart
- **Fornecedores**: supplier management with contacts, categories, and bank account info
- **Estoque**: product types, products, product items (stock entries), stock prediction (green/yellow/red), reservation with `SELECT FOR UPDATE`, dashboard
- **Orçamentos** (quotes): full document lifecycle (rascunho ⇄ em_análise ⇄ aprovado → cancelado), items linked to product catalog, per-item price visibility toggle, convert-to-service (one-time), duplicate, browser print, company letterhead settings
- **Security**: login rate limiting (slowapi, 5/min), password reset token invalidation, readiness endpoint with DB probe
- **Frontend**: paginated lists (20 items/page), structured logging on service transitions

### Roadmap
- Orçamento edit form + inline item management (Phase 9 Wave D)
- Company settings admin page in frontend
- Client portal: clients monitor water well status and fill well data
- Roles: field technician ("técnico de campo"), geologist ("geólogo"), supervisor
- PDF generation for orçamentos (server-side)
- Billing from completed services

---

## Tech Stack

| Layer       | Technology                                      |
|-------------|------------------------------------------------|
| Backend     | Python 3.14+, FastAPI, SQLModel, PostgreSQL    |
| Migrations  | Alembic                                         |
| Auth        | JWT (PyJWT), Argon2/Bcrypt (pwdlib)            |
| Frontend    | React 19, TypeScript, Vite, TanStack Router/Query |
| UI          | Tailwind CSS v4, shadcn/ui, Radix UI           |
| Forms       | React Hook Form                                 |
| API Client  | Auto-generated from OpenAPI (openapi-ts)       |
| Testing     | Pytest (backend), Playwright (E2E frontend)    |
| Linting     | Ruff + MyPy (backend), Biome (frontend)        |
| Deploy      | Native (rsync + systemd + Caddy on VPS)        |
| Pkg Mgmt    | uv (Python), Bun (JavaScript)                  |

---

## Domain Concepts

- **Cliente**: Can be a person (CPF) or company (CNPJ). Located in Brazil. Has structured address fields (address, bairro, city, state, CEP).
- **Orçamento**: A commercial quote/proposal linked to a client. Status: `rascunho` ⇄ `em_análise` ⇄ `aprovado` → `cancelado`. Items linked to product catalog with per-item price visibility. Can be converted to a Serviço (one-time). Has company letterhead from CompanySettings.
- **Serviço**: A service order linked to a client. Two top-level types:
  - `perfuração` (water well drilling)
  - `manutenção/reparo` (repair service)
  - Each service can have line items of type `material` or `serviço`, optionally linked to a Product
  - Status lifecycle: `requested` → `scheduled` → `executing` → `completed` (or `cancelled` from any non-terminal)
  - Stock is reserved on `scheduled`, deducted on `completed`, released on `cancelled`
- **Endereço de execução**: The site where the service is performed — may differ from the client's address.
- **Fornecedor**: Supplier with contact info and bank account details for payment.
- **Estoque**: Product types → Products → ProductItems (physical stock units). Status: `em_estoque` → `reservado` → `utilizado`. Stock prediction with 90-day consumption window.
- **CompanySettings**: Singleton table for company letterhead (name, CNPJ, address, phone, email, logo) used in orçamento documents.
- **Roles**: `admin`, `finance`, `client` (implemented); `technician`, `geologist`, `supervisor` (planned)

---

## Key Development Commands

Local dev runs natively (no Docker). First-time setup: `bash scripts/dev-setup.sh` — see `development.md`.

```bash
# Backend (from /backend) — port 8000
uv run fastapi dev app/main.py

# Frontend (from /frontend) — port 5173
bun run dev

# Generate OpenAPI client (after backend changes)
bash ./scripts/generate-client.sh

# Run backend tests
cd backend && bash scripts/test.sh

# Run frontend E2E tests
cd frontend && bun run test

# DB migrations (from /backend)
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
```

## Local Dev URLs

| Service        | URL                          |
|----------------|------------------------------|
| Frontend       | http://localhost:5173        |
| Backend API    | http://localhost:8000        |
| Swagger docs   | http://localhost:8000/docs   |
| Mailpit (opt.) | http://localhost:8025        |

---

## OpenSpec Workflow

This project uses [OpenSpec](https://openspec.dev) for spec-driven development. OpenSpec structures changes through artifacts (proposal → specs → design → tasks) before implementation.

Config lives in `backend/openspec/config.yaml`. Changes are tracked under `backend/openspec/changes/`.

### Key `/opsx` commands (Claude slash commands)

| Command | Purpose |
|---|---|
| `/opsx:new` | Start a new change step-by-step |
| `/opsx:ff` | Fast-forward: create all artifacts at once |
| `/opsx:continue` | Resume an in-progress change |
| `/opsx:apply` | Implement tasks from a change |
| `/opsx:verify` | Verify implementation matches specs |
| `/opsx:archive` | Archive a completed change |
| `/opsx:explore` | Think through a problem before committing to an approach |
| `/opsx:onboard` | Guided walkthrough of the full OpenSpec cycle |

Use OpenSpec for any non-trivial feature or fix. For small, obvious changes a direct implementation is fine.

---

## Language Policy

- **UI / user-facing text**: always in **Brazilian Portuguese (PT-BR)** — labels, messages, toasts, error text, placeholders, page titles, everything the user sees
- **Code, comments, commit messages, PR descriptions, and documentation**: always in **plain English**

---

## Conventions & Rules

### Git
- **Always use conventional commits** — use `/git-commit` skill
- **Before every commit**: run linter, typecheck, and tests (see `/git-commit` skill for commands)
- **Never commit `htmlcov/`** — generated artifacts, already in `.gitignore`

### Git Worktrees
Use [Worktrunk](https://worktrunk.dev) (`wt`) for creating and managing git worktrees — prefer worktrees over branch-switching in the same directory for parallel or isolated work. See `docs/git-worktrees.md` for full usage.
- **Always use `wt`** — never raw `git worktree` commands
- Project hooks auto-run setup on new worktrees (no manual steps needed)

### PR Labels (required by CI)
Every PR must have at least one label matching `<type>` or `<type>(<scope>)`. Base types: `feat`, `fix`, `chore`, `refact`, `docs`, `upgrade`, `breaking`, `security`, `bug`, `feature`, `internal`, `lang-all`. Scope is optional, lowercase alphanumeric with dashes (e.g. `fix(backend)`, `chore(crud-api)`, `feat(frontend)`). Use `/create-pr` skill which handles this automatically.

### Backend
- Models go in `backend/app/models.py` (SQLModel)
- CRUD operations go in `backend/app/crud.py`
- API routes go in `backend/app/api/routes/`
- **Always check for N+1 queries** when writing or editing any database query — use `selectinload` or `joinedload` as appropriate
- Use `uv` for all Python package management

### Frontend
- Pages/routes go in `frontend/src/routes/`
- Reusable components go in `frontend/src/components/`
- Use the auto-generated client in `frontend/src/client/` — never hand-write API calls
- Regenerate the client after any backend API change: `bash ./scripts/generate-client.sh`
- Use `bun` for all JavaScript package management

### Known pitfalls

**Zod v4 API changes**
- Use `error:` instead of `required_error:` in schema params — `required_error` no longer exists in Zod v4
- Example: `z.enum(["a", "b"], { error: "Required" })` not `{ required_error: "Required" }`

**React Hook Form + Zod number fields**
- Never use `z.coerce.number()` for form fields — it makes the inferred input type `unknown`, causing a resolver type mismatch with `useForm<FormData>`
- Instead use `z.number()` and add `onChange={(e) => field.onChange(e.target.valueAsNumber)}` on the `<input type="number">` element

**SQLModel CRUD imports**
- Never use local (inline) imports inside CRUD functions with string annotations like `-> "Client"` — mypy cannot resolve forward references to models that are not imported at module level
- Always import all models at the top of `crud.py`

**pre-commit mypy hook**
- The `mirrors-mypy` pre-commit hook runs in an isolated environment; it must have `additional_dependencies` listing `sqlmodel`, `pydantic`, and `fastapi` to understand SQLModel table models (`table=True`)
- The hook must also pass `--python-version=3.14` to match the project's Python version

**Python 3.14: HTTP response header names must be valid (no trailing colon)**
- Python 3.14 tightened RFC 5322 validation in `email.message` — header field names with trailing colons (e.g. `"subject:"`) now raise `ValueError`
- This surfaces as a crash in `httpx` when processing HTTP responses containing such headers
- Always use valid header names without trailing colons: `{"subject": value}` not `{"subject:": value}`

---

## gstack (Browser Automation)

Use `/browse` for all web browsing — **never use `mcp__claude-in-chrome__*` tools**.
Available skills: `/browse`, `/qa`, `/review`, `/ship`, `/plan-ceo-review`, `/plan-eng-review`, `/setup-browser-cookies`, `/retro`.
If skills aren't working: `cd .claude/skills/gstack && ./setup`
