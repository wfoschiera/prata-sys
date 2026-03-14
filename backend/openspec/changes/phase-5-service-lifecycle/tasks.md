## 1. Database Models

- [x] 1.1 Add `cancelled` value to `ServiceStatus` enum in `backend/app/models.py`
- [x] 1.2 Add `description` optional Text column to the `Service` SQLModel table in `backend/app/models.py`
- [x] 1.3 Add `cancelled_reason` optional String column to the `Service` SQLModel table in `backend/app/models.py`
- [x] 1.4 Define `ServiceStatusLog` SQLModel table with fields: `id` (UUID PK), `service_id` (FK → `service.id`, not null), `from_status` (ServiceStatus, not null), `to_status` (ServiceStatus, not null), `changed_by` (UUID, FK → `user.id`, not null), `changed_at` (DateTime, default utcnow), `notes` (optional String)
- [x] 1.5 Add `status_logs` relationship on `Service` (one-to-many to `ServiceStatusLog`, ordered by `changed_at`, cascade="all, delete-orphan")
- [x] 1.6 Add `changed_by_user` relationship on `ServiceStatusLog` (many-to-one to `User`) for eager loading the actor name in responses

## 2. Alembic Migration

- [x] 2.1 Run `alembic revision --autogenerate -m "add service lifecycle fields and status log"` and review the generated file
- [x] 2.2 Verify the migration adds `description` (Text, nullable) and `cancelled_reason` (String, nullable) to the `service` table
- [x] 2.3 Verify the migration creates `service_status_log` with all columns and correct FK constraints (`service_id` → `service.id`, `changed_by` → `user.id`)
- [x] 2.4 Manually add `CREATE INDEX ix_service_status_log_service_id_changed_at ON service_status_log (service_id, changed_at)` to the migration if autogenerate does not produce it
- [x] 2.5 Run `alembic upgrade head` in the development environment and verify no errors
- [x] 2.6 Verify rollback: `alembic downgrade -1` removes the new table and columns without errors

## 3. Backend Schemas

- [x] 3.1 Add `ServiceTransitionRequest` schema with fields: `to_status` (ServiceStatus, required), `reason` (optional String — required when `to_status == cancelled`, validated via `model_validator`), `deduction_items` (optional list of `DeductionItem` — required when `to_status == completed`)
- [x] 3.2 Add `DeductionItem` schema with fields: `service_item_id` (UUID), `quantity` (float, > 0)
- [x] 3.3 Add `ServiceStatusLogRead` schema with fields: `id`, `from_status`, `to_status`, `changed_by`, `changed_at`, `notes`, and `changed_by_name` (resolved from the user relationship)
- [x] 3.4 Add `StockWarning` schema with fields: `service_item_id` (UUID), `description` (String), `required_quantity` (float), `available_quantity` (float), `shortfall` (float)
- [x] 3.5 Add `ServiceTransitionResponse` schema with fields: `service` (ServiceRead), `stock_warnings` (list of StockWarning, default empty list)
- [x] 3.6 Update `ServiceRead` schema to include `description`, `cancelled_reason`, `status_logs` (list of `ServiceStatusLogRead`), and `has_stock_warning` (bool, default False)
- [x] 3.7 Update `ServiceUpdate` schema to explicitly exclude the `status` field (mark it as a disallowed field or remove it from the model) so PATCH cannot accept status changes

## 4. Backend CRUD

- [x] 4.1 Add `VALID_TRANSITIONS: dict[ServiceStatus, list[ServiceStatus]]` constant mapping each state to its allowed next states, e.g. `{requested: [scheduled, cancelled], scheduled: [executing, cancelled], executing: [completed, cancelled], completed: [], cancelled: []}`
- [x] 4.2 Add `transition_service_status(db, service, to_status, changed_by_id, reason=None, deduction_items=None) -> tuple[Service, list[StockWarning]]` in `backend/app/crud.py` — validates transition, creates `ServiceStatusLog`, handles stock side-effects (reservation on scheduled, deduction on completed), returns updated service and any warnings
- [x] 4.3 Inside `transition_service_status`: when transitioning to `scheduled`, query `StockItem` for each material `ServiceItem`, compute shortfalls, increment `StockItem.reservado` for items with sufficient stock (using `SELECT ... FOR UPDATE` to prevent race conditions), and collect `StockWarning` objects for shortfalls
- [x] 4.4 Inside `transition_service_status`: when transitioning to `completed`, validate that `deduction_items` is provided, verify each `service_item_id` belongs to the service and is of type `material`, deduct quantities from `StockItem.quantity` and decrement `StockItem.reservado`, reject if a deduction would make `quantity` negative
- [x] 4.5 Inside `transition_service_status`: when transitioning to `cancelled`, persist `cancelled_reason` on the `Service` record and record `reason` in the `ServiceStatusLog.notes` column
- [x] 4.6 Add `deduct_stock(db, service, changed_by_id) -> list[DeductionSummary]` in `backend/app/crud.py` — validates service is in `executing`, deducts all material item quantities from `StockItem` (using `SELECT ... FOR UPDATE`), returns a summary list; guard: only valid when `service.status == executing`
- [x] 4.7 Add `get_service_status_logs(db, service_id) -> list[ServiceStatusLog]` with `selectinload(ServiceStatusLog.changed_by_user)` ordered by `changed_at` ascending
- [x] 4.8 Update `get_service` and `get_services` CRUD functions to also `selectinload(Service.status_logs)` so logs are always included in responses without N+1 queries
- [x] 4.9 Guard `update_service` in `crud.py`: if the incoming `ServiceUpdate` contains a `status` field (even if excluded from schema, add a belt-and-suspenders check), raise `ValueError("Use the /transition endpoint to change service status")`

## 5. Backend API Routes

- [x] 5.1 Add `POST /services/{id}/transition` route to `backend/app/api/routes/services.py`; require `admin` role via `require_role("admin")`; accepts `ServiceTransitionRequest`; calls `transition_service_status`; returns `ServiceTransitionResponse` with HTTP 200; returns 422 on invalid transition or missing required fields
- [x] 5.2 Add `POST /services/{id}/deduct-stock` route; require `admin` role; validates service is in `executing` status (return 422 if not); calls `deduct_stock`; returns HTTP 200 with deduction summary
- [x] 5.3 Update `PATCH /services/{id}` route: if request body contains a `status` key, return HTTP 422 with message `"Use POST /services/{id}/transition to change service status"`
- [x] 5.4 Update `GET /services/{id}` response to include `status_logs` and `has_stock_warning` fields from the updated `ServiceRead` schema
- [x] 5.5 Update `GET /services` response to include `has_stock_warning` on each service item in the list
- [x] 5.6 Ensure all new routes are covered by OpenAPI docstrings (summary + description) so the generated client has meaningful names

## 6. Frontend API Client Regeneration

- [x] 6.1 Regenerate the typed API client from the updated OpenAPI schema (`bash ./scripts/generate-client.sh`) so that `transition`, `deductStock`, `ServiceTransitionRequest`, `ServiceStatusLogRead`, and `StockWarning` types are available in the frontend

## 7. Frontend Status Timeline Component

- [x] 7.1 Create `frontend/src/components/StatusTimeline.tsx` — a presentational component that receives `currentStatus: ServiceStatus` and renders an ordered step indicator for `requested → scheduled → executing → completed`; completed steps are visually distinct from future steps; if `currentStatus === "cancelled"`, render the last reached step followed by a `cancelled` terminal node styled distinctly (e.g., red)
- [x] 7.2 The `StatusTimeline` component must accept an optional `cancelledReason` prop and render it below the cancelled node when present
- [x] 7.3 Import and render `StatusTimeline` in the service detail route (`frontend/src/routes/services/$serviceId.tsx`) below the service header

## 8. Frontend Transition Buttons

- [x] 8.1 Create `frontend/src/components/TransitionButtons.tsx` — a component that receives `currentStatus: ServiceStatus`, `serviceId: string`, and `userRole: string`; renders action buttons only for valid next states (using the same `VALID_TRANSITIONS` logic reflected in the frontend); renders nothing for `finance` users or on terminal states
- [x] 8.2 Each forward-transition button calls `POST /transition` directly (optimistic or with loading state); the "Cancelar" button opens the `CancelModal` instead of calling the API directly
- [x] 8.3 The "Concluir" button (to `completed`) opens the `CompleteConfirmModal` instead of calling the API directly
- [x] 8.4 Import and render `TransitionButtons` in the service detail route below the `StatusTimeline`

## 9. Frontend Cancellation Modal

- [x] 9.1 Create `frontend/src/components/CancelModal.tsx` — a modal dialog triggered by the "Cancelar serviço" button; contains a required textarea for the cancellation reason; the confirm button is disabled while the textarea is empty
- [x] 9.2 On confirm, call `POST /api/v1/services/{id}/transition` with `{to_status: "cancelled", reason: <text>}` using the generated client; on success, close the modal and invalidate the service detail query; on error, display the API error message inside the modal without closing it
- [x] 9.3 The modal must handle the loading state (disable both buttons while the API call is in flight)

## 10. Frontend Completion Confirmation Modal

- [x] 10.1 Create `frontend/src/components/CompleteConfirmModal.tsx` — a modal that receives the service's material `ServiceItem` list; renders each item with its description and a quantity input pre-filled with `ServiceItem.quantity`; allows the user to adjust quantities before confirming
- [x] 10.2 Validate inside the modal that all quantity inputs are positive numbers before enabling the confirm button
- [x] 10.3 On confirm, build the `deduction_items` array from the current input values and call `POST /api/v1/services/{id}/transition` with `{to_status: "completed", deduction_items: [...]}` using the generated client; on success, close the modal and invalidate the service detail query; on error, display the API error inside the modal
- [x] 10.4 The modal must handle the loading state (disable both buttons while the API call is in flight)

## 11. Frontend Stock Warning Badge

- [x] 11.1 Create `frontend/src/components/StockWarningBadge.tsx` — a small badge/alert component that renders a warning message (e.g., "Materiais insuficientes no estoque") when `hasStockWarning` prop is `true`; renders nothing when `false`
- [x] 11.2 Render `StockWarningBadge` in the service detail header when `service.has_stock_warning === true` and `service.status === "scheduled"`
- [x] 11.3 Render `StockWarningBadge` (compact variant) in the services list table row for scheduled services with `has_stock_warning === true`

## 12. Frontend "Baixar do Estoque" Button

- [x] 12.1 Add a "Baixar do estoque" button to the service detail page that is visible only when `service.status === "executing"` and the current user has the `admin` role
- [x] 12.2 The button calls `POST /api/v1/services/{id}/deduct-stock` using the generated client; on success, show a success toast and invalidate the service detail query; on error, display the API error in a toast
- [x] 12.3 Disable the button while the API call is in flight to prevent double-submission

## 13. Backend Tests

- [x] 13.1 Add unit tests for `VALID_TRANSITIONS` in `backend/tests/` verifying that all allowed transitions pass and all disallowed transitions raise `ValueError`
- [x] 13.2 Add integration test: `POST /transition` valid forward transition creates a `ServiceStatusLog` entry with correct fields
- [x] 13.3 Add integration test: `POST /transition` to `cancelled` without reason returns 422
- [x] 13.4 Add integration test: `POST /transition` to `cancelled` with reason persists `cancelled_reason` on service
- [x] 13.5 Add integration test: `POST /transition` from a terminal state returns 422
- [x] 13.6 Add integration test: `PATCH /services/{id}` with `status` in body returns 422 with redirect message
- [x] 13.7 Add integration test: `finance` user calling `POST /transition` returns 403
- [x] 13.8 Add integration test: `POST /deduct-stock` on non-executing service returns 422
- [x] 13.9 Add integration test: `GET /services/{id}` response includes `status_logs` array in correct chronological order
- [x] 13.10 Update any existing service tests that set `status` via `PATCH` to use the new `/transition` endpoint instead
