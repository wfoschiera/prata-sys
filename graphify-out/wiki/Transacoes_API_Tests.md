# Transacoes API Tests

> 53 nodes · cohesion 0.08

## Key Concepts

- **test_transacoes.py** (46 connections) — `backend/tests/api/routes/test_transacoes.py`
- **Decimal** (32 connections) — `backend/app/models.py`
- **TestClient** (29 connections) — `backend/tests/api/routes/test_transacoes.py`
- **Session** (18 connections) — `backend/tests/api/routes/test_transacoes.py`
- **Transacao** (9 connections) — `backend/tests/api/routes/test_transacoes.py`
- **_make_despesa()** (9 connections) — `backend/tests/api/routes/test_transacoes.py`
- **_make_transacao_db()** (8 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_list_transacoes_filter_by_service_id_via_api()** (6 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_update_transacao_with_invalid_service_raises()** (5 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_create_despesa_crud()** (4 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_create_receita_crud()** (4 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_create_transacao_unauthorized()** (4 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_get_transacoes_filter_by_service_id()** (4 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_get_transacoes_filter_by_tipo()** (4 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_list_transacoes_combined_all_filters()** (4 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_list_transacoes_filter_by_date_range_via_api()** (4 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_list_transacoes_filter_combined_tipo_and_categoria()** (4 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_resumo_mensal_with_data()** (4 connections) — `backend/tests/api/routes/test_transacoes.py`
- **_make_receita()** (3 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_create_despesa_invalid_categoria_raises()** (3 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_create_despesa_with_client_id_raises()** (3 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_create_receita_invalid_categoria_raises()** (3 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_create_transacao_finance_user()** (3 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_create_valor_zero_raises()** (3 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_delete_transacao()** (3 connections) — `backend/tests/api/routes/test_transacoes.py`
- *... and 28 more nodes in this community*

## Relationships

- [[Backend CRUD Core]] (30 shared connections)
- [[Services API Tests]] (6 shared connections)
- [[Stock Prediction Tests]] (5 shared connections)
- [[Service-Stock Integration Tests]] (5 shared connections)
- [[Estoque API Tests]] (4 shared connections)
- [[Document Validators (CNPJ)]] (3 shared connections)
- [[Operational Dashboard Tests]] (3 shared connections)
- [[Role Defaults Logic]] (3 shared connections)
- [[Service Transition Unit Tests]] (2 shared connections)
- [[Operational Dashboard Router]] (1 shared connections)
- [[User CRUD Tests]] (1 shared connections)

## Source Files

- `backend/app/models.py`
- `backend/tests/api/routes/test_transacoes.py`

## Audit Trail

- EXTRACTED: 249 (92%)
- INFERRED: 22 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
