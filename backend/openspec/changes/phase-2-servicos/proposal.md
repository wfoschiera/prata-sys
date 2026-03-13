## Why

The system needs to track service orders (ordens de serviço) for well drilling and repair jobs. Without this, the company cannot manage job scheduling, execution status, or the materials and labor items associated with each job.

## What Changes

- New `Service` model representing a service order linked to a client, with type (perfuração | reparo), status lifecycle (requested → scheduled → executing → completed), execution address, and optional notes.
- New `ServiceItem` model representing line items on a service (materials or labor), each with description, quantity, and unit price.
- New REST API routes under `/api/v1/services` with full CRUD; write operations restricted to `admin` and `finance` roles.
- Alembic migration adding `service` and `service_item` tables.
- Frontend: services list page, new service form (client selector + line items), and service detail view.
- Sidebar navigation link for Services.

## Capabilities

### New Capabilities

- `servicos`: Service order management — create, list, view, and update service orders with associated line items and client linkage.

### Modified Capabilities

<!-- No existing spec-level behavior changes. -->

## Impact

- **Backend:** `backend/app/models.py` (new models), `backend/app/crud.py` (new CRUD functions), `backend/app/api/routes/services.py` (new router), `backend/app/api/main.py` (router registration), new Alembic migration.
- **Frontend:** new route files under `frontend/src/routes/services/`, updated sidebar component.
- **Dependencies:** assumes Phase 1 (`Client` model) is merged; `require_role` dependency from `backend/app/api/deps.py` reused.
- **N+1 risk:** services list query must eagerly load `client` and `items` relationships via `selectinload()`.
