# prata-sys — CLAUDE.md

**prata-sys** is a business management system for a **water well drilling company** in
Brazil — clients, service orders, suppliers, inventory (estoque), quotes (orçamentos),
and finances.

For the domain glossary, feature inventory, and roadmap, see
[`docs/domain-model.md`](docs/domain-model.md). For a full architecture walkthrough,
see [`ONBOARDING.md`](ONBOARDING.md).

## Tech Stack

| Layer       | Technology                                      |
|-------------|------------------------------------------------|
| Backend     | Python 3.14+, FastAPI, SQLModel, PostgreSQL    |
| Migrations  | Alembic                                         |
| Auth        | JWT (PyJWT), Argon2/Bcrypt (pwdlib)            |
| Frontend    | React 19, TypeScript, Vite, TanStack Router/Query |
| UI          | Tailwind CSS v4, shadcn/ui, Radix UI           |
| Forms       | React Hook Form                                 |
| API Client  | Auto-generated from OpenAPI (openapi-ts), native fetch |
| Testing     | Pytest (backend), Playwright (E2E frontend)    |
| Linting     | Ruff + MyPy (backend), Biome (frontend)        |
| Deploy      | Docker Compose + Caddy (single host, GHCR images) |
| Pkg Mgmt    | uv (Python), Bun (JavaScript)                  |

---

## Key Development Commands

Local dev runs natively (no Docker except Postgres + Mailpit). First-time setup:
`bash scripts/dev-setup.sh`. Full workflow in [`development.md`](development.md).

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

| Service        | URL                          |
|----------------|------------------------------|
| Frontend       | http://localhost:5173        |
| Backend API    | http://localhost:8000        |
| Swagger docs   | http://localhost:8000/docs   |
| Mailpit (opt.) | http://localhost:8025        |

---

## OpenSpec Workflow

This project uses [OpenSpec](https://openspec.dev) for spec-driven development. OpenSpec
structures changes through artifacts (proposal → specs → design → tasks) before
implementation. Config lives in `openspec/config.yaml`; changes under `openspec/changes/`.

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

Use OpenSpec for any non-trivial feature or fix. For small, obvious changes a direct
implementation is fine.

---

## Language Policy

- **UI / user-facing text**: always in **Brazilian Portuguese (PT-BR)** — labels,
  messages, toasts, error text, placeholders, page titles, everything the user sees
- **Code, comments, commit messages, PR descriptions, and documentation**: always in
  **plain English**

---

## Conventions & Rules

### Git
- **Always use conventional commits** — use `/git-commit` skill
- **Before every commit**: run linter, typecheck, and tests (see `/git-commit` skill for commands)
- **Never commit `htmlcov/`** — generated artifacts, already in `.gitignore`

### Bug Workflow (required)
Never start fixing a bug directly. For every bug, follow these steps in order:
1. **Open a GitHub issue first** — one issue per bug, describing the problem before any code changes.
2. **Create one branch per issue** — each issue gets its own dedicated branch; never fix multiple issues on the same branch.
3. **Name the branch** `wfoschiera/<type>/<description>`, where `<type>` is the conventional-commit type (`fix` for bugs) and `<description>` is a short kebab-case summary. Example: `wfoschiera/fix/stock-deduction-quantities`.

### Git Worktrees
Use [Worktrunk](https://worktrunk.dev) (`wt`) for creating and managing git worktrees — prefer worktrees over branch-switching in the same directory for parallel or isolated work. See [`docs/git-worktrees.md`](docs/git-worktrees.md) for full usage.
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
- Use the auto-generated client in `frontend/src/client/` — never hand-write API calls (the client wraps native `fetch`)
- Regenerate the client after any backend API change: `bash ./scripts/generate-client.sh`
- Use `bun` for all JavaScript package management

### Known pitfalls
Stack-specific gotchas (Zod v4, React Hook Form number fields, SQLModel CRUD imports,
mypy pre-commit hook, Python 3.14 HTTP headers) are logged in
[`docs/pitfalls.md`](docs/pitfalls.md). Read it before touching forms, CRUD, or the
mypy hook, and add new gotchas there as you hit them.

---

## gstack (Browser Automation)

Use `/browse` for all web browsing — **never use `mcp__claude-in-chrome__*` tools**.
Available skills: `/browse`, `/qa`, `/review`, `/ship`, `/plan-ceo-review`, `/plan-eng-review`, `/setup-browser-cookies`, `/retro`.
If skills aren't working: `cd .claude/skills/gstack && ./setup`
