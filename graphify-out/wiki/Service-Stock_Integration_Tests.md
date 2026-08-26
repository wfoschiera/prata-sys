# Service-Stock Integration Tests

> 14 nodes · cohesion 0.16

## Key Concepts

- **test_cancel_executing_service_releases_stock()** (10 connections) — `backend/tests/api/routes/test_services.py`
- **test_deduct_stock_marks_reserved_items_utilizado()** (10 connections) — `backend/tests/api/routes/test_services.py`
- **test_transition_to_completed_marks_stock_utilizado()** (10 connections) — `backend/tests/api/routes/test_services.py`
- **test_transition_to_cancelled_releases_reserved_stock()** (9 connections) — `backend/tests/api/routes/test_services.py`
- **test_transition_to_scheduled_reserves_stock()** (9 connections) — `backend/tests/api/routes/test_services.py`
- **_reserved_for_service()** (8 connections) — `backend/tests/api/routes/test_services.py`
- **_utilizado_for_service()** (6 connections) — `backend/tests/api/routes/test_services.py`
- **Cancelling from executing state releases all reserved stock back to em_estoque.** (1 connections) — `backend/tests/api/routes/test_services.py`
- **Return all ProductItems currently reserved for a service.** (1 connections) — `backend/tests/api/routes/test_services.py`
- **Return all ProductItems marked utilizado that were reserved for a service.** (1 connections) — `backend/tests/api/routes/test_services.py`
- **Transitioning to scheduled reserves em_estoque ProductItems for the service.** (1 connections) — `backend/tests/api/routes/test_services.py`
- **Cancelling a service releases all reserved ProductItems back to em_estoque.** (1 connections) — `backend/tests/api/routes/test_services.py`
- **Completing a service marks reserved ProductItems as utilizado.** (1 connections) — `backend/tests/api/routes/test_services.py`
- **POST /deduct-stock on an executing service marks reserved items utilizado.** (1 connections) — `backend/tests/api/routes/test_services.py`

## Relationships

- [[Services API Tests]] (24 shared connections)
- [[Service Transition Unit Tests]] (10 shared connections)
- [[Transacoes API Tests]] (5 shared connections)

## Source Files

- `backend/tests/api/routes/test_services.py`

## Audit Trail

- EXTRACTED: 69 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
