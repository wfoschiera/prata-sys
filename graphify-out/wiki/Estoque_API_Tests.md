# Estoque API Tests

> 54 nodes · cohesion 0.11

## Key Concepts

- **TestClient** (52 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_estoque.py** (49 connections) — `backend/tests/api/routes/test_estoque.py`
- **_create_product_type()** (33 connections) — `backend/tests/api/routes/test_estoque.py`
- **_create_product()** (25 connections) — `backend/tests/api/routes/test_estoque.py`
- **Session** (15 connections) — `backend/tests/api/routes/test_estoque.py`
- **_create_product_item()** (12 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_baixar_estoque_on_executing_service()** (9 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_reserve_stock_insufficient()** (9 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_reserve_stock_sufficient()** (9 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_utilize_reserved_items()** (9 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_list_products_filter_by_fornecedor_id()** (7 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_baixar_estoque_non_executing_service()** (5 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_create_product_item()** (5 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_delete_product_with_items_conflict()** (5 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_get_product_items_list()** (5 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_get_product_prediction_with_stock()** (5 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_list_product_items()** (5 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_update_product_invalid_product_type_id()** (5 connections) — `backend/tests/api/routes/test_estoque.py`
- **validate_product_item_transition()** (4 connections) — `backend/app/crud.py`
- **test_create_product()** (4 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_create_product_finance_forbidden()** (4 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_create_product_item_finance_forbidden()** (4 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_create_product_item_zero_quantity()** (4 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_create_product_negative_unit_price()** (4 connections) — `backend/tests/api/routes/test_estoque.py`
- **test_create_product_type_duplicate_conflict()** (4 connections) — `backend/tests/api/routes/test_estoque.py`
- *... and 29 more nodes in this community*

## Relationships

- [[Backend CRUD Core]] (29 shared connections)
- [[User CRUD Tests]] (13 shared connections)
- [[Transacoes API Tests]] (4 shared connections)

## Source Files

- `backend/app/crud.py`
- `backend/tests/api/routes/test_estoque.py`

## Audit Trail

- EXTRACTED: 337 (91%)
- INFERRED: 33 (9%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
