# prata-sys — CLAUDE.md

## Project Overview

**prata-sys** is a business management system for a **water well drilling company** in Brazil. It manages clients, service orders, suppliers, and internal operations.

The project is built on the [FastAPI Full-Stack Template](https://github.com/fastapi/full-stack-fastapi-template).

### Implemented
- **Cadastro** (registration) for Admins, Finance users, and Clients (CPF/CNPJ)
- **Serviços** (service orders): linked to a client with execution site address; full lifecycle enforcement in progress
- **RBAC**: role-based permissions (`admin`, `finance`, `client`) with per-user overrides
- **Financeiro**: transaction management (receitas/despesas), finance dashboard with KPI cards and 6-month chart

### Roadmap
- Service lifecycle: enforced status transitions with audit log and stock integration (Phase 5)
- Supplier ("fornecedores") management with contacts and bank account info (Phase 6)
- Inventory control — stock of materials (Phase 7)
- Client portal: clients monitor water well status and fill well data
- Materials and services catalog with unit prices (e.g., drilling price per diameter)
- Roles: field technician ("técnico de campo"), geologist ("geólogo"), supervisor

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
| Containers  | Docker Compose + Traefik                        |
| Pkg Mgmt    | uv (Python), Bun (JavaScript)                  |

---

## Domain Concepts

- **Cliente**: Can be a person (CPF) or company (CNPJ). Located in Brazil.
- **Serviço**: A service order linked to a client. Two top-level types:
  - `perfuração` (water well drilling)
  - `manutenção/reparo` (repair service)
  - Each service can have line items of type `material` or `serviço`
- **Endereço de execução**: The site where the service is performed — may differ from the client's address.
- **Fornecedor**: Supplier with contact info and bank account details for payment.
- **Roles**: `admin`, `finance`, `client` (implemented); `technician`, `geologist`, `supervisor` (planned)

---

## Key Development Commands

```bash
# Start full dev stack (hot-reload)
docker compose watch

# Backend only (from /backend)
fastapi dev app/main.py

# Frontend only (from /frontend)
bun run dev

# Generate OpenAPI client (after backend changes)
bash ./scripts/generate-client.sh

# Run backend tests
bash ./scripts/test.sh

# Run frontend E2E tests
cd frontend && bun run test

# DB migrations (from /backend)
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## Local Dev URLs

| Service      | URL                        |
|--------------|---------------------------|
| Frontend     | http://localhost:5173      |
| Backend API  | http://localhost:8000      |
| Swagger docs | http://localhost:8000/docs |
| DB Admin     | http://localhost:8080      |
| Email test   | http://localhost:1080      |

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
- **Always use conventional commits**: `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`
- **Before every commit**: run linter, typecheck, AND tests — on both backend and frontend if either was changed
  - Backend: `ruff check . && mypy . && bash ../scripts/test.sh`
  - Frontend: `bun run lint && bun run build && bun run test`
- **Never commit `htmlcov/` or any coverage HTML report files** — generated artifacts, already in `.gitignore`

### PR Labels (required by CI)
Every PR must have exactly one label from the list below — the `check-labels` CI job will fail otherwise.
Use the label that matches the conventional commit prefix of the primary change:

| Label | Use for |
|-------|---------|
| `feat` | New features (`feat:` commits) |
| `fix` | Bug fixes (`fix:` commits) |
| `chore` | Maintenance, tooling, config (`chore:` commits) |
| `refact` | Refactoring (`refactor:` commits) |
| `docs` | Documentation only (`docs:` commits) |
| `upgrade` | Dependency upgrades |
| `breaking` | Breaking changes |
| `security` | Security fixes |
| `bug` | Bug reports / confirmed bugs |
| `feature` | Feature requests |
| `internal` | Internal / CI / infra changes |
| `lang-all` | Translations / i18n |

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

**Docker: tests not found**
- The `backend/tests/` directory must be explicitly `COPY`-ed in `backend/Dockerfile` — it is not included by default and pytest will fail with "file or directory not found: tests/"

**Python 3.14: HTTP response header names must be valid (no trailing colon)**
- Python 3.14 tightened RFC 5322 validation in `email.message` — header field names with trailing colons (e.g. `"subject:"`) now raise `ValueError`
- This surfaces as a crash in `httpx` when processing HTTP responses containing such headers
- Always use valid header names without trailing colons: `{"subject": value}` not `{"subject:": value}`
