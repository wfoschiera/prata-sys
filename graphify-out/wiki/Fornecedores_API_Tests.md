# Fornecedores API Tests

> 32 nodes · cohesion 0.15

## Key Concepts

- **test_fornecedores.py** (26 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **TestClient** (25 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **_create_fornecedor()** (22 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_no_n_plus_one()** (6 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_create_fornecedor_duplicate_cnpj()** (4 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_superuser_bypass()** (4 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_update_fornecedor_duplicate_cnpj_returns_409()** (4 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_update_fornecedor_same_cnpj_is_ok()** (4 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_admin_full_access()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_contato_wrong_fornecedor()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_create_contato()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_create_fornecedor()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_create_fornecedor_invalid_cnpj()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_create_fornecedor_no_cnpj()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_create_fornecedor_with_categories()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_delete_contato()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_delete_fornecedor_cascades()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_finance_can_read()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_finance_cannot_write()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_get_fornecedores_category_filter()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_get_fornecedores_search()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_update_contato()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_update_fornecedor_no_categories_field()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_update_fornecedor_not_found()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- **test_update_fornecedor_replaces_categories()** (3 connections) — `backend/tests/api/routes/test_fornecedores.py`
- *... and 7 more nodes in this community*

## Relationships

- [[User CRUD Tests]] (5 shared connections)
- [[Backend CRUD Core]] (4 shared connections)

## Source Files

- `backend/tests/api/routes/test_fornecedores.py`

## Audit Trail

- EXTRACTED: 148 (95%)
- INFERRED: 7 (5%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
