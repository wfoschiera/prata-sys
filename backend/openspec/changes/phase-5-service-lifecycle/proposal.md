## Why

Service orders already exist in the system with a `status` field, but transitions are not enforced: any status value can be set at any time, no audit trail is kept, and the `cancelled` state does not exist at all. As field operations scale, the company needs reliable control over who can advance a job, a history of when each status change occurred, and coordination with the stock system so that materials reserved for a job are automatically accounted for when work begins or finishes.

## What Changes

- Add `cancelled` to `ServiceStatus` enum; add nullable `cancelled_reason` String column and `description` Text column to the `Service` model.
- Enforce server-side status transition rules: only `admin` users may trigger transitions; `finance` users may view but not advance status.
- New `ServiceStatusLog` table records each transition with `service_id`, `from_status`, `to_status`, `changed_by` (user id), and `changed_at` timestamp.
- New dedicated `POST /api/v1/services/{id}/transition` endpoint for advancing or cancelling a service; the general `PATCH` endpoint continues to handle non-status field edits but rejects direct `status` changes.
- Stock integration: when a service moves to `scheduled`, `ServiceItem` records of type `material` are cross-referenced against `StockItem` quantities and any shortfall is surfaced as a warning (non-blocking). When moving to `executing`, a manual "Baixar do estoque" action deducts reserved quantities. When moving to `completed`, a confirmation step lists all material items for review before final deduction.
- Alembic migration adding `cancelled_reason`, `description` columns to `service`, and creating the `service_status_log` table.
- Frontend: service detail page gains a status timeline/progress indicator; contextual transition buttons appear for valid next states only; dedicated modals for cancellation (with required reason) and for completion (with product deduction review); a warning badge on scheduled services that have material items with insufficient stock.

## Capabilities

### New Capabilities

- `service-lifecycle`: Enforced, role-gated service status transitions with an immutable audit log of every change.
- `service-status-log`: Per-service history of all status transitions including actor and timestamp.
- `stock-reservation`: Material items on a scheduled service are marked `reservado` in the stock system; quantities are deducted on execution or completion with user confirmation.

### Modified Capabilities

- `servicos`: The `Service` model gains `description` and `cancelled_reason` fields; the `ServiceStatus` enum gains the `cancelled` state; the existing `PATCH /services/{id}` endpoint no longer accepts direct `status` changes — use the new `transition` endpoint instead.

## Impact

- **Backend:** `backend/app/models.py` (new enum value, new columns, new `ServiceStatusLog` model), `backend/app/crud.py` (new `transition_service_status`, `get_status_log` functions), `backend/app/api/routes/services.py` (new `POST /{id}/transition` route; guard `PATCH` from `status` field), new Alembic migration.
- **Frontend:** updated service detail route (`frontend/src/routes/services/$serviceId.tsx`), new `StatusTimeline` component, `TransitionButton` component, `CancelModal` component, `CompleteConfirmModal` component, `StockWarningBadge` component.
- **Dependencies:** requires Phase 2 (`Service` model, services routes) and Phase 3 (RBAC `require_role` dependency). Stock integration assumes a `StockItem` model exists or will be introduced alongside this phase; if not yet available, stock-related steps are gated and can be applied once stock is in place.
- **N+1 risk:** `GET /services/{id}` must also eagerly load `status_logs` via `selectinload(Service.status_logs)` to avoid per-log lazy queries.
