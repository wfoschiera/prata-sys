# Service Transition Unit Tests

> 38 nodes · cohesion 0.16

## Key Concepts

- **ServiceItemFactory** (52 connections) — `backend/tests/factories.py`
- **ProductItemFactory** (43 connections) — `backend/tests/factories.py`
- **UUID** (29 connections) — `backend/tests/crud/test_service_transitions.py`
- **Session** (28 connections) — `backend/tests/crud/test_service_transitions.py`
- **test_service_transitions.py** (24 connections) — `backend/tests/crud/test_service_transitions.py`
- **_transition()** (22 connections) — `backend/tests/crud/test_service_transitions.py`
- **factories.py** (22 connections) — `backend/tests/factories.py`
- **_setup_reserved_service()** (14 connections) — `backend/tests/crud/test_service_transitions.py`
- **Service** (11 connections) — `backend/tests/crud/test_service_transitions.py`
- **ProductItem** (10 connections) — `backend/tests/crud/test_service_transitions.py`
- **ServiceStatus** (10 connections) — `backend/tests/crud/test_service_transitions.py`
- **LogCaptureFixture** (10 connections) — `backend/tests/crud/test_service_transitions.py`
- **test_completion_over_request_consumes_all_reserved_and_logs()** (9 connections) — `backend/tests/crud/test_service_transitions.py`
- **test_completion_full_deduction_consumes_all()** (8 connections) — `backend/tests/crud/test_service_transitions.py`
- **test_completion_partial_deduction_releases_remainder()** (8 connections) — `backend/tests/crud/test_service_transitions.py`
- **test_invalid_deduction_item_id_raises()** (8 connections) — `backend/tests/crud/test_service_transitions.py`
- **_items_for_product()** (7 connections) — `backend/tests/crud/test_service_transitions.py`
- **test_executing_to_completed_with_deduction_items()** (7 connections) — `backend/tests/crud/test_service_transitions.py`
- **test_invalid_completed_to_anything_raises()** (7 connections) — `backend/tests/crud/test_service_transitions.py`
- **test_executing_to_cancelled()** (5 connections) — `backend/tests/crud/test_service_transitions.py`
- **test_invalid_cancelled_to_anything_raises()** (5 connections) — `backend/tests/crud/test_service_transitions.py`
- **test_invalid_requested_to_completed_raises()** (5 connections) — `backend/tests/crud/test_service_transitions.py`
- **test_invalid_requested_to_executing_raises()** (5 connections) — `backend/tests/crud/test_service_transitions.py`
- **test_multiple_transitions_create_ordered_logs()** (5 connections) — `backend/tests/crud/test_service_transitions.py`
- **test_requested_to_cancelled()** (5 connections) — `backend/tests/crud/test_service_transitions.py`
- *... and 13 more nodes in this community*

## Relationships

- [[Backend CRUD Core]] (96 shared connections)
- [[Services API Tests]] (34 shared connections)
- [[Stock Prediction Tests]] (10 shared connections)
- [[Service-Stock Integration Tests]] (10 shared connections)
- [[API Core Tests]] (3 shared connections)
- [[Transacoes API Tests]] (2 shared connections)
- [[Operational Dashboard Router]] (1 shared connections)
- [[Clients API Tests]] (1 shared connections)
- [[Operational Dashboard Tests]] (1 shared connections)

## Source Files

- `backend/tests/crud/test_service_transitions.py`
- `backend/tests/factories.py`

## Audit Trail

- EXTRACTED: 268 (69%)
- INFERRED: 120 (31%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
