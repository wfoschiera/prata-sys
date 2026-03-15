# Tasks: Phase 8 — Stock Integration

## Backend — CRUD layer

- [x] 1.1 Add `_release_stock_items(session, service)` to `crud.py`: find all `ProductItem` with `status=reservado` and `service_id=service.id`, set `status=em_estoque`, clear `service_id`, set `updated_at=now()`
- [x] 1.2 Implement `_check_stock_for_service(session, service) -> list[StockWarning]` in `crud.py:311`: for each material `ServiceItem`, find `ProductItem` records with matching `product_id` and `status=em_estoque` ordered by `created_at ASC`; flip as many as needed to `reservado` (set `service_id`, `updated_at`); return `StockWarning` for any shortfall
- [x] 1.3 Implement `_deduct_stock_items(session, service, deduction_items)` in `crud.py:319`: find `ProductItem` records for this service with `status=reservado`, mark them `utilizado`, set `updated_at=now()`; remove the "Actual StockItem deduction added in Phase 7" comment
- [x] 1.4 Implement `deduct_stock(session, service, changed_by_id) -> list[dict]` in `crud.py:393`: call the deduction logic, return list of `{product_id, product_name, quantity_deducted}` summaries; remove the "Full deduction implemented in Phase 7" comment
- [x] 1.5 Add cancellation stock release in `transition_service_status` (crud.py:343): when `to_status == ServiceStatus.cancelled`, call `_release_stock_items(session, service)` before updating service status
- [x] 1.6 Fix stock prediction filter: in `get_stock_prediction` (crud.py:1011), change the 90-day filter from `ProductItem.created_at >= window_start` to `ProductItem.updated_at >= window_start` so consumption dates are accurate (only after T-02 is live)

## Backend — Route layer

- [x] 2.1 Update `POST /services/{id}/deduct-stock` response model: change from `list[dict]` (untyped) to `list[DeductionSummary]` (add `DeductionSummary` schema with `product_id: UUID`, `product_name: str`, `quantity_deducted: Decimal`)

## Backend — Tests

- [x] 3.1 Add `test_transition_to_scheduled_reserves_stock`: create service with material items, add matching ProductItems, transition to scheduled, assert ProductItems have status=reservado
- [x] 3.2 Add `test_transition_to_scheduled_with_insufficient_stock_warns`: add fewer ProductItems than needed, assert response contains stock_warnings
- [x] 3.3 Add `test_transition_to_completed_marks_stock_utilizado`: reserve stock, transition to completed, assert ProductItems have status=utilizado
- [x] 3.4 Add `test_transition_to_cancelled_releases_stock`: reserve stock, transition to cancelled, assert ProductItems have status=em_estoque and service_id=null
- [x] 3.5 Add `test_deduct_stock_endpoint_marks_utilizado`: put service in executing with reserved items, POST /deduct-stock, assert items utilizado
- [x] 3.6 Add `test_deduct_stock_on_non_executing_returns_422`: existing test (already present at test_services.py:651) — verify still passes after implementation

## Performance — deferred (see TODOS.md)

- [x] DEFER: Add `index=True` to `Service.client_id` and `Service.status` → TODOS.md T-04
- [x] DEFER: Remove status_logs from list endpoint → TODOS.md T-05
- [x] DEFER: Rate limiting on login → TODOS.md T-11
