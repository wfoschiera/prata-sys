# Services API Tests

> 82 nodes · cohesion 0.06

## Key Concepts

- **ServiceFactory** (106 connections) — `backend/tests/factories.py`
- **TestClient** (70 connections) — `backend/tests/api/routes/test_services.py`
- **test_services.py** (64 connections) — `backend/tests/api/routes/test_services.py`
- **Session** (61 connections) — `backend/tests/api/routes/test_services.py`
- **test_transition_to_scheduled_with_insufficient_stock_returns_warning()** (8 connections) — `backend/tests/api/routes/test_services.py`
- **_advance_service_to()** (7 connections) — `backend/tests/api/routes/test_services.py`
- **test_deduct_stock_items_rejects_non_material()** (7 connections) — `backend/tests/api/routes/test_services.py`
- **test_delete_item_from_executing_service_returns_422()** (7 connections) — `backend/tests/api/routes/test_services.py`
- **test_add_item_to_completed_service_returns_422()** (6 connections) — `backend/tests/api/routes/test_services.py`
- **test_add_item_to_executing_service_returns_422()** (6 connections) — `backend/tests/api/routes/test_services.py`
- **test_delete_executing_service_returns_422()** (6 connections) — `backend/tests/api/routes/test_services.py`
- **test_delete_scheduled_service_returns_422()** (6 connections) — `backend/tests/api/routes/test_services.py`
- **test_delete_service_item_wrong_service()** (6 connections) — `backend/tests/api/routes/test_services.py`
- **test_deduct_stock_on_non_executing_service_returns_422()** (5 connections) — `backend/tests/api/routes/test_services.py`
- **test_delete_requested_service_succeeds()** (5 connections) — `backend/tests/api/routes/test_services.py`
- **test_delete_service_cascades_items()** (5 connections) — `backend/tests/api/routes/test_services.py`
- **test_delete_service_item()** (5 connections) — `backend/tests/api/routes/test_services.py`
- **test_delete_service_item_unauthenticated()** (5 connections) — `backend/tests/api/routes/test_services.py`
- **test_get_service_includes_status_logs()** (5 connections) — `backend/tests/api/routes/test_services.py`
- **test_get_service_status_logs_crud()** (5 connections) — `backend/tests/api/routes/test_services.py`
- **test_patch_with_status_field_returns_422()** (5 connections) — `backend/tests/api/routes/test_services.py`
- **test_read_service_includes_items()** (5 connections) — `backend/tests/api/routes/test_services.py`
- **test_transition_finance_user_forbidden()** (5 connections) — `backend/tests/api/routes/test_services.py`
- **test_transition_from_terminal_state_returns_422()** (5 connections) — `backend/tests/api/routes/test_services.py`
- **test_transition_to_cancelled_with_reason_persists()** (5 connections) — `backend/tests/api/routes/test_services.py`
- *... and 57 more nodes in this community*

## Relationships

- [[Backend CRUD Core]] (59 shared connections)
- [[Service Transition Unit Tests]] (34 shared connections)
- [[Service-Stock Integration Tests]] (24 shared connections)
- [[Transacoes API Tests]] (6 shared connections)
- [[Operational Dashboard Tests]] (5 shared connections)
- [[Transition Map Test]] (1 shared connections)
- [[API Core Tests]] (1 shared connections)

## Source Files

- `backend/tests/api/routes/test_services.py`
- `backend/tests/factories.py`

## Audit Trail

- EXTRACTED: 489 (88%)
- INFERRED: 69 (12%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
