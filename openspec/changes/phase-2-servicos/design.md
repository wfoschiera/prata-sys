## Context

The application already manages `User` accounts with role-based access (`admin`, `finance`, `client`). Phase 1 introduced the `Client` model. Phase 2 extends the system with `Service` (service orders) and `ServiceItem` (line items), following the existing CRUD + FastAPI routes pattern. The frontend uses auto-generated API clients from the OpenAPI schema.

## Goals / Non-Goals

**Goals:**
- Define `Service` and `ServiceItem` SQLModel models with correct relationships.
- Expose full CRUD under `/api/v1/services`, guarded by `require_role` for writes.
- Provide an Alembic migration for the new tables.
- Deliver a frontend list, creation form, and detail view for services.
- Prevent N+1 queries on the services list by eagerly loading related `client` and `items`.

**Non-Goals:**
- Invoice generation or PDF export of service orders.
- Real-time status push notifications.
- Client-facing portal access to service orders.
- Bulk import of services.

## Decisions

### 1. Single `Service` router module

All service endpoints live in a new `backend/app/api/routes/services.py` and are registered in `backend/app/api/main.py`. This mirrors the existing pattern used by `clients` and keeps each resource self-contained.

*Alternative considered:* nesting services under `/clients/{id}/services`. Rejected because services need to be listed and filtered globally without always knowing the client upfront.

### 2. `selectinload()` for N+1 prevention

The `GET /services` list endpoint MUST issue a single `selectinload(Service.client)` and `selectinload(Service.items)` so that N services do not generate N+1 queries. SQLModel/SQLAlchemy's lazy-load default would cause a query per service for client and items.

*Alternative considered:* `joinedload` with a JOIN. Rejected because it inflates result rows when `items` is a one-to-many collection; `selectinload` issues two extra queries instead of a Cartesian product.

### 3. Status as a string enum

`ServiceStatus` is implemented as a Python `Enum` stored as a VARCHAR in Postgres (not a native PG ENUM type). This makes Alembic migrations simpler (no `ALTER TYPE` operations when adding statuses) and is consistent with how `UserRole` is stored.

### 4. `execution_address` as a plain string

Addresses for job sites vary widely and do not need structured parsing at this stage. A single `String` column is sufficient. A structured address model can be introduced in a future phase.

### 5. Frontend auto-generated client

The frontend MUST NOT hand-write API calls. `openapi-typescript-codegen` (or equivalent) regenerates the typed client after backend changes. Route files consume the generated hooks/functions.

## Risks / Trade-offs

- **Status transition enforcement** → currently no server-side guard prevents arbitrary status jumps (e.g., `requested` → `completed`). Mitigation: document the valid lifecycle in specs; enforcement can be added in a future phase if needed.
- **Missing client guard** → if a `service` references a `client_id` that was deleted, the FK constraint will prevent deletion of the client while services exist. Mitigation: apply `ON DELETE RESTRICT` (default FK behavior) and surface clear error messages.
- **Large items lists** → `selectinload` for items loads all items in memory. Mitigation: acceptable for current scale; pagination of items can be added later.

## Migration Plan

1. Run `alembic revision --autogenerate -m "add service and service_item tables"` after models are defined.
2. Review generated migration; ensure `service_item.service_id` has FK to `service.id`.
3. Apply: `alembic upgrade head` in staging, then production.
4. Rollback: `alembic downgrade -1` drops `service_item` then `service` tables.

## Open Questions

- Should `ServiceItem` support a `unit` field (e.g., "m", "kg", "hr") for display purposes? Deferred to Phase 3.
- Should completed services be locked from edits? Needs product decision; not enforced in Phase 2.
