## Context

Phase 2 introduced `Service` and `ServiceItem` with a `status` string enum, but transitions were never guarded server-side — any caller could set any status at any time. Phase 3 added RBAC via `require_role`. Phase 5 closes the gap: it enforces valid transitions, restricts them to `admin`, adds a `cancelled` terminal state with a required reason, records every change in an immutable audit log, and wires material items to the stock system at the key lifecycle moments (scheduled → reserved, executing → manual deduction, completed → confirmed deduction).

## Goals / Non-Goals

**Goals:**
- Enforce the transition graph `requested → scheduled → executing → completed`; `cancelled` reachable from any non-terminal state.
- Restrict status transitions to the `admin` role; `finance` may read only.
- Persist an immutable `ServiceStatusLog` for every transition (actor + timestamp).
- Add `description` (free text) and `cancelled_reason` (required on cancellation) columns to `Service`.
- On `scheduled`: cross-reference material items against `StockItem`, increment `reservado`, and surface shortfalls as non-blocking warnings.
- On `executing`: expose a manual `POST /deduct-stock` endpoint for admin to deduct reserved stock.
- On `completed`: require a confirmed `deduction_items` list; deduct from stock and release remaining `reservado`.
- Frontend: status timeline, contextual transition buttons, cancellation modal, completion review modal, stock warning badge.

**Non-Goals:**
- Real-time push notifications on status change.
- Multi-approver workflows or approval queues.
- Rollback / undo of a completed service.
- Automatic stock deduction without any user confirmation.
- Client-facing visibility of status transitions.
- Inventory replenishment or purchase order generation.

## Decisions

### 1. Dedicated `/transition` endpoint instead of overloading PATCH

A new `POST /api/v1/services/{id}/transition` endpoint handles all status changes. The existing `PATCH` endpoint is modified to reject any payload containing a `status` field with an explanatory 422. This separation makes the intent explicit, allows the transition endpoint to carry richer payloads (e.g., `reason`, `deduction_items`), and keeps audit log creation co-located with the only code path that legally changes status.

*Alternative considered:* keep status in PATCH and detect it server-side. Rejected because it muddies the schema, makes validation logic awkward, and hides business logic inside a generic update handler.

### 2. ServiceStatusLog as a separate table (not a JSONB column)

Audit entries are stored as rows in a `service_status_log` table with FK to `service`. This allows indexed queries by service, actor, or time range, and is straightforward to migrate. `GET /services/{id}` eager-loads logs via `selectinload(Service.status_logs)`.

*Alternative considered:* append to a JSONB `status_history` column on `Service`. Rejected because JSONB history arrays are harder to query, sort, and enforce schema on; they also grow unboundedly on a single row.

### 3. Stock integration is non-blocking on scheduling

When a service moves to `scheduled`, missing stock does not block the transition. The API returns a `stock_warnings` array and the `has_stock_warning` flag but completes the transition. This matches the domain reality: the company may order materials after scheduling. The `reservado` increment still happens for items that do have sufficient stock.

*Alternative considered:* block scheduling if any item is short. Rejected by product requirement — the user explicitly stated "don't block, just show a warning."

### 4. Completion deduction requires an explicit confirmation payload

`POST /transition` with `to_status: completed` MUST include a `deduction_items` list. This forces the frontend to show the review modal and prevents accidental deductions. The backend validates that every referenced `service_item_id` belongs to the service and is of type `material`.

*Alternative considered:* auto-deduct all material items on completion. Rejected because field quantities sometimes differ from originally planned quantities and the user must be able to adjust before confirming.

### 5. Manual deduct-stock endpoint for the executing state

`POST /api/v1/services/{id}/deduct-stock` provides a mid-lifecycle deduction option without transitioning the service status. This supports the workflow where materials are consumed incrementally during execution rather than all at once at completion.

*Alternative considered:* only allow deduction at completion. Rejected by product requirement — the "Baixar do estoque" button is a first-class action on the executing state.

### 6. cancelled_reason stored on Service, not in the log

The cancellation reason is persisted as `Service.cancelled_reason` for easy retrieval on the detail view. The `ServiceStatusLog` entry for the `cancelled` transition also captures it in a `notes` column so the log is self-contained.

*Alternative considered:* store reason only in the log. Rejected because querying the reason for display requires joining to the log, which is an unnecessary join for the most common read path.

### 7. Admin-only transitions, finance read-only

`POST /transition` and `POST /deduct-stock` use `require_role("admin")`. All `GET` endpoints remain accessible to any authenticated user including `finance`. This matches the company's operational model where financial staff monitor jobs but field decisions are made by admins.

### 8. selectinload for status_logs on service detail

`GET /services/{id}` adds `selectinload(Service.status_logs)` to the existing `selectinload(Service.client)` and `selectinload(Service.items)` calls. This keeps the query count bounded at 4 regardless of log volume.

## Risks / Trade-offs

- **Stock model dependency:** the stock integration tasks depend on a `StockItem` model (and `StockItem.reservado` field) that may not yet exist. If the stock phase has not been implemented, the transition endpoint must still work but skip stock side-effects. The implementation uses a feature flag or a try-import guard; stock tasks in `tasks.md` are clearly marked as conditional.
- **Race condition on reservado:** two concurrent transitions of different services referencing the same `StockItem` could double-increment `reservado` without a row-level lock. Mitigation: use `SELECT ... FOR UPDATE` on `StockItem` rows inside the transition transaction. Acceptable risk for current single-server scale.
- **Audit log growth:** high-volume services will accumulate log entries over time. Mitigation: add a DB index on `(service_id, changed_at)`; archival strategy can be introduced in a later phase.
- **PATCH status guard is a breaking change:** any existing client (scripts, tests) that sets `status` via PATCH will receive 422 after this phase lands. Mitigation: update all existing tests in the same PR; document the change in the migration plan.

## Migration Plan

1. Add `cancelled_reason` (nullable String) and `description` (nullable Text) columns to the `service` table.
2. Add `ServiceStatus.cancelled` value — because the enum is stored as VARCHAR (not a native PG ENUM), no `ALTER TYPE` is needed; only application-level validation changes.
3. Create `service_status_log` table with columns `id`, `service_id` (FK), `from_status`, `to_status`, `changed_by` (FK → `user.id`), `changed_at`, `notes`.
4. Add index `ix_service_status_log_service_id_changed_at` on `(service_id, changed_at)`.
5. Run `alembic revision --autogenerate -m "add service lifecycle fields and status log"` and review the generated file.
6. Apply: `alembic upgrade head` in staging, then production.
7. Rollback: `alembic downgrade -1` drops `service_status_log` and removes the two new columns from `service`.
8. Deploy backend with the PATCH guard active; update or re-run all existing service tests.

## Open Questions

- Should `ServiceItem` records reference a `StockItem` by FK, or is the link resolved by matching on item description/SKU? A FK reference is cleaner but requires `StockItem` to exist before service items are created. Deferred pending the stock phase design.
- Should the `description` field on `Service` replace or coexist with `notes`? Currently both exist; a future cleanup pass may deprecate `notes`. Not resolved in this phase.
- Should `finance` users be able to trigger the "Baixar do estoque" action, or only `admin`? Currently scoped to `admin` per product requirement; revisit if finance staff manage inventory in practice.
- Should the completion modal allow adding new items that were not on the original order (e.g., extra materials used on site)? Out of scope for this phase; can be addressed when the materials catalog is introduced.
