# Stock Prediction Tests

> 79 nodes · cohesion 0.07

## Key Concepts

- **ProductFactory** (61 connections) — `backend/tests/factories.py`
- **TestClient** (43 connections) — `backend/tests/api/routes/test_orcamentos.py`
- **test_orcamentos.py** (43 connections) — `backend/tests/api/routes/test_orcamentos.py`
- **_create_orcamento()** (34 connections) — `backend/tests/api/routes/test_orcamentos.py`
- **_add_item()** (16 connections) — `backend/tests/api/routes/test_orcamentos.py`
- **test_stock_prediction.py** (15 connections) — `backend/tests/crud/test_stock_prediction.py`
- **Session** (14 connections) — `backend/tests/crud/test_stock_prediction.py`
- **_add_items()** (13 connections) — `backend/tests/crud/test_stock_prediction.py`
- **UUID** (6 connections) — `backend/tests/crud/test_stock_prediction.py`
- **test_prediction_all_reserved_no_history()** (6 connections) — `backend/tests/crud/test_stock_prediction.py`
- **test_prediction_stock_available_no_history()** (6 connections) — `backend/tests/crud/test_stock_prediction.py`
- **test_delete_item_wrong_orcamento_returns_404()** (6 connections) — `backend/tests/api/routes/test_orcamentos.py`
- **test_update_item_wrong_orcamento_returns_404()** (6 connections) — `backend/tests/api/routes/test_orcamentos.py`
- **ProductItemStatus** (5 connections) — `backend/tests/crud/test_stock_prediction.py`
- **test_prediction_green_threshold()** (5 connections) — `backend/tests/crud/test_stock_prediction.py`
- **test_prediction_net_stock_zero_with_history()** (5 connections) — `backend/tests/crud/test_stock_prediction.py`
- **test_prediction_no_stock_no_history()** (5 connections) — `backend/tests/crud/test_stock_prediction.py`
- **test_prediction_parametrized()** (5 connections) — `backend/tests/crud/test_stock_prediction.py`
- **test_prediction_red_threshold()** (5 connections) — `backend/tests/crud/test_stock_prediction.py`
- **test_prediction_yellow_threshold()** (5 connections) — `backend/tests/crud/test_stock_prediction.py`
- **test_add_item_to_approved_returns_422()** (5 connections) — `backend/tests/api/routes/test_orcamentos.py`
- **test_add_item_to_orcamento()** (5 connections) — `backend/tests/api/routes/test_orcamentos.py`
- **test_approve_with_items()** (5 connections) — `backend/tests/api/routes/test_orcamentos.py`
- **test_backward_transition_aprovado_to_em_analise()** (5 connections) — `backend/tests/api/routes/test_orcamentos.py`
- **test_convert_approved_to_service()** (5 connections) — `backend/tests/api/routes/test_orcamentos.py`
- *... and 54 more nodes in this community*

## Relationships

- [[Backend CRUD Core]] (39 shared connections)
- [[Service Transition Unit Tests]] (10 shared connections)
- [[Transacoes API Tests]] (5 shared connections)
- [[API Core Tests]] (1 shared connections)

## Source Files

- `backend/tests/api/routes/test_orcamentos.py`
- `backend/tests/crud/test_stock_prediction.py`
- `backend/tests/factories.py`

## Audit Trail

- EXTRACTED: 414 (89%)
- INFERRED: 49 (11%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
