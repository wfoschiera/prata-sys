## Context

The project is built on the FastAPI full-stack template which ships with a generic `Item` model as a demo resource. The `User` model has `is_superuser: bool` for access control, which is kept for dev/system access but is insufficient for business-level role differentiation (`admin`, `finance`, `client`).

The codebase has no production data yet — this is a greenfield cleanup before domain features are built.

## Goals / Non-Goals

**Goals:**
- Remove all `Item` code (model, CRUD, routes, frontend) to reduce noise
- Add a `role` enum field to `User` for business-level access control
- Add `require_role` dependency for protecting routes by role
- Keep `is_superuser` untouched — used for developer/system-level access

**Non-Goals:**
- Implementing any domain feature (clients, services, suppliers)
- Changing authentication flow or JWT structure
- Building the client portal or role-specific UIs

## Decisions

### Decision 1: `role` as a string enum column, not a separate table

A separate `roles` table with a join is more flexible for future permission systems, but adds unnecessary complexity for an MVP with only 3 static roles. A simple `role: str` column with a Python `Enum` for validation is the right trade-off now. Can be migrated later if needed.

### Decision 2: Keep `is_superuser`, add `role` as an independent field

`is_superuser` grants unrestricted access and is used by existing dev tooling and the template's admin endpoints. The new `role` field adds a separate business-level concern. A superuser can have any role; role checks are enforced independently from superuser checks.

### Decision 3: Default role for existing users

New `role` column defaults to `"admin"` so existing dev/test users retain full access after the migration runs without manual intervention.

## Risks / Trade-offs

- **Risk**: Frontend components tied to `Item` routes may cause build errors after deletion → Mitigation: delete all Item-related components and route files together, then regenerate client before building.
- **Risk**: Alembic migration could fail on a non-empty DB → Mitigation: greenfield project, no production data; migration is safe.

## Migration Plan

1. Update backend model and CRUD
2. Generate Alembic migration (`alembic revision --autogenerate`)
3. Apply migration (`alembic upgrade head`)
4. Delete Item routes and frontend files
5. Regenerate OpenAPI client (`bash scripts/generate-client.sh`)
6. Run tests
