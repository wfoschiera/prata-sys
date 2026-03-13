# prata-sys — CLAUDE.md

## Project Overview

**prata-sys** is a business management system for a **water well drilling company** in Brazil. It manages clients, service orders, suppliers, and internal operations.

The project is built on the [FastAPI Full-Stack Template](https://github.com/fastapi/full-stack-fastapi-template) and is being developed as an MVP with planned expansion.

### Implemented (Done)
- **Phase 0**: Foundation cleanup — project structure, CI, pre-commit hooks
- **Phase 1**: Client cadastro — CPF/CNPJ, address, admin/finance CRUD
- **Phase 2**: Serviços — service orders with line items (material/labor), execution address, status field
- **Phase 3**: RBAC — two-tier permission system (role defaults + per-user overrides), permissions page

### Planned Phases (in order)

#### Phase 4 — Finance Flows
Simple financial tracking: income (receitas) and expenses (despesas). Categories include fuel, equipment/vehicle/office maintenance, materials purchase, CLT labor, day-laborer (diarista) payments, and admin costs. All in BRL. A `Transacao` table links optionally to a service, client, or fornecedor.
- `transacao.fornecedor_id` is added in this phase as a nullable UUID column **without a FK constraint** (the `fornecedor` table doesn't exist yet). Free-text `nome_contraparte` covers the gap until Phase 6.

#### Phase 5 — Service Lifecycle
Enforces valid status transitions (`requested → scheduled → executing → completed | cancelled`), adds `cancelled_reason` and `description` fields, and logs every transition with who changed it and when. Stock integration (reserving and deducting inventory) is **deferred to Phase 7** — Phase 5 delivers the full lifecycle UI without it.

#### Phase 6 — Fornecedores
Supplier cadastro: company name, CNPJ (optional), multiple contacts (name, telefone, WhatsApp, role description), and product categories (tubos, conexões, bombas, cabos, outros). Includes a second migration that adds the FK constraint from `transacao.fornecedor_id → fornecedor.id`, enabling the transaction form to pick a real supplier.

#### Phase 7 — Controle de Estoque
Product types (with category + unit of measure), products (linked to a product type and fornecedor), and stock entries with three statuses:
- `em_estoque` — available
- `reservado` — reserved for a scheduled service (set automatically on scheduling; shortage is a warning, not a blocker)
- `utilizado` — consumed (manual "Baixar do estoque" button while executing; automatic with review on completion)

Includes a **depletion prediction**: `(em_estoque qty − reservado qty) ÷ avg daily consumption = days until stockout`, color-coded green/yellow/red. If no consumption history exists yet, shows "—".

### Post-MVP
- Client portal: clients monitor well status and fill in well data
- Materials and services catalog with unit prices
- Roles: field technician, geologist, supervisor

---

## Tech Stack

| Layer       | Technology                                      |
|-------------|------------------------------------------------|
| Backend     | Python 3.13+, FastAPI, SQLModel, PostgreSQL    |
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
- **Fornecedor**: Supplier with company name, CNPJ (optional), multiple contacts (name, telefone, WhatsApp, role), and product categories they supply.
- **Transacao**: Financial transaction (income or expense). Links optionally to a service, client, or fornecedor. `fornecedor_id` FK is added in Phase 6 after the fornecedor table exists.
- **Estoque**: Inventory entries per product, with status `em_estoque | reservado | utilizado`. Reserved when a service is scheduled; deducted when executing/completed.
- **Roles**: `admin`, `finance`, `client` (implemented); `technician`, `geologist`, `supervisor` (future)

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

## Conventions & Rules

### Git
- **Always use conventional commits**: `feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `test:`
- **Before every commit**: run linter, typecheck, AND tests — on both backend and frontend if either was changed
  - Backend: `ruff check . && mypy . && bash ../scripts/test.sh`
  - Frontend: `bun run lint && bun run build && bun run test`
- **Never commit `htmlcov/` or any coverage HTML report files** — generated artifacts, already in `.gitignore`

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

**HTTP status testing**
- When testing HTTP status codes, always use constants from the `HTTPStatus` module instead of raw integers. Replace all occurrences of raw status codes like `200`, `201`, `400`, `403`, `404`, `422`, etc., with their corresponding `HTTPStatus` constants. For example:
  - Use `assert r.status_code == HTTPStatus.OK` instead of `assert r.status_code == 200`.
  - Use `assert r.status_code == HTTPStatus.CREATED` instead of `assert r.status_code == 201`.
  - Use `assert r.status_code == HTTPStatus.BAD_REQUEST` instead of `assert r.status_code == 400`.
  - Use `assert r.status_code == HTTPStatus.FORBIDDEN` instead of `assert r.status_code == 403`.
  - Use `assert r.status_code == HTTPStatus.NOT_FOUND` instead of `assert r.status_code == 404`.
  - Use `assert r.status_code == HTTPStatus.UNPROCESSABLE_ENTITY` instead of `assert r.status_code == 422`.

**pre-commit mypy hook**
- The `mirrors-mypy` pre-commit hook runs in an isolated environment; it must have `additional_dependencies` listing `sqlmodel`, `pydantic`, and `fastapi` to understand SQLModel table models (`table=True`)
- The hook must also pass `--python-version=3.13` to match the project's Python version

**Docker: tests not found**
- The `backend/tests/` directory must be explicitly `COPY`-ed in `backend/Dockerfile` — it is not included by default and pytest will fail with "file or directory not found: tests/"
