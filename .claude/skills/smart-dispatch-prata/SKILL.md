---
name: smart-dispatch
description: Automatically routes tasks to optimal Claude models
  (opus/sonnet/haiku) based on complexity. Use when implementing
  features, fixing bugs, or any multi-step development work.
---

# Smart Model Dispatch

## Routing Priority

Prefer the cheapest model that can reliably complete the task.
When uncertain, start with the lower model and escalate if needed.

## Complexity Signals

### High (use opus)
- Multiple files affected with cross-cutting concerns (backend + frontend + API client regen)
- Unclear or ambiguous requirements needing trade-off analysis
- Novel architecture decisions without established patterns
- Debugging issues with no obvious root cause across modules
- OpenSpec design decisions (proposals, specs, design artifacts)
- Complex query optimization with N+1 prevention across related models

### Medium (use sonnet)
- Clear scope within a single feature or module
- Known patterns with moderate logic (API routes, React pages, service transitions)
- Feature planning when requirements are mostly defined
- Refactoring with clear goals
- Tests with complex logic, mocking, or edge cases

### Low (use haiku)
- Single file, repetitive, or template-based changes
- Mechanical transformations (rename, reformat, extract)
- Simple boilerplate and scaffolding
- Generating Alembic migrations
- Writing simple CRUD functions in crud.py
- Creating OpenAPI schema models (SQLModel classes)
- Tailwind component scaffolding (layout, spacing, basic structure)

## Model Routing

### opus — Complex reasoning & architecture
- Architecture planning and OpenSpec design decisions
- Complex business logic with ambiguous requirements (e.g., service lifecycle state machines)
- Root cause analysis for non-obvious bugs across backend/frontend boundary
- Cross-module refactoring (backend models + API routes + frontend pages + API client regeneration)
- Complex query optimization with selectinload/joinedload and N+1 prevention
- RBAC and permission model changes that affect multiple layers

### sonnet — Standard implementation & moderate reasoning
- Implementing API routes with business logic (FastAPI endpoints in api/routes/)
- React pages with TanStack Query hooks and React Hook Form
- Service lifecycle transitions and status enforcement
- Financial dashboard components (KPI cards, charts, transaction tables)
- SQLModel CRUD operations with moderate query logic
- Unit/integration tests with mocking or complex assertions
- Code review and refactoring within clear scope

### haiku — Fast, mechanical tasks
- Generating Alembic migration files (alembic revision --autogenerate)
- Writing simple CRUD functions (single-model create/read/update/delete)
- Creating SQLModel schema classes and OpenAPI response models
- Tailwind component scaffolding (wrapper divs, grid layouts, basic styling)
- PT-BR label constants and enum display values in models
- Simple/mechanical unit tests (no complex logic)
- File reads, context gathering, and search
- Regenerating the OpenAPI client (bash ./scripts/generate-client.sh)

## Multi-Step Workflows

Chain models within a single task for efficiency.

### Bug Fix
1. haiku — Reproduce & gather context (read files, grep, understand scope)
2. opus — Root cause analysis (only if non-obvious after step 1)
3. sonnet — Implement the fix
4. haiku — Write/update tests (escalate to sonnet if complex)

### New Feature
1. opus — OpenSpec design & architecture (skip if pattern is well-established)
2. sonnet — Implement API routes, business logic, and React pages
3. haiku — Alembic migrations, SQLModel boilerplate, Tailwind scaffolding
4. sonnet — Integration tests and complex unit tests
5. haiku — Regenerate OpenAPI client, verify types

### Refactor
1. sonnet — Analyze current code and plan changes
2. sonnet — Implement refactor
3. haiku — Update simple tests, regenerate API client if needed

## Escalation Rules

- If haiku struggles or requires >2 attempts on a subtask, escalate to sonnet.
- If sonnet produces incorrect logic or misses edge cases, escalate to opus.
- After escalation, the higher model handles only the hard part — drop back down for remaining mechanical work.
