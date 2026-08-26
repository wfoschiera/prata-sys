# API Core Tests

> 51 nodes · cohesion 0.05

## Key Concepts

- **conftest.py** (26 connections) — `backend/tests/conftest.py`
- **test_utils.py** (7 connections) — `backend/tests/api/routes/test_utils.py`
- **_login_for_token()** (7 connections) — `backend/tests/conftest.py`
- **_session_scoped_test_client()** (7 connections) — `backend/tests/conftest.py`
- **TestClient** (6 connections) — `backend/tests/api/routes/test_utils.py`
- **client()** (5 connections) — `backend/tests/conftest.py`
- **admin_token_headers()** (4 connections) — `backend/tests/conftest.py`
- **client_token_headers()** (4 connections) — `backend/tests/conftest.py`
- **finance_token_headers()** (4 connections) — `backend/tests/conftest.py`
- **product_item()** (4 connections) — `backend/tests/conftest.py`
- **product_type()** (4 connections) — `backend/tests/conftest.py`
- **random_client()** (4 connections) — `backend/tests/conftest.py`
- **service_item()** (4 connections) — `backend/tests/conftest.py`
- **superuser_id()** (4 connections) — `backend/tests/conftest.py`
- **superuser_token_headers()** (4 connections) — `backend/tests/conftest.py`
- **main.py** (3 connections) — `backend/app/main.py`
- **test_test_email()** (3 connections) — `backend/tests/api/routes/test_utils.py`
- **_bind_factory_session()** (3 connections) — `backend/tests/conftest.py`
- **db()** (3 connections) — `backend/tests/conftest.py`
- **fornecedor()** (3 connections) — `backend/tests/conftest.py`
- **product()** (3 connections) — `backend/tests/conftest.py`
- **_sentinel_check_clean_db()** (3 connections) — `backend/tests/conftest.py`
- **service()** (3 connections) — `backend/tests/conftest.py`
- **transacao()** (3 connections) — `backend/tests/conftest.py`
- **custom_generate_unique_id()** (2 connections) — `backend/app/main.py`
- *... and 26 more nodes in this community*

## Relationships

- [[Backend CRUD Core]] (19 shared connections)
- [[Service Transition Unit Tests]] (3 shared connections)
- [[Users Security Tests]] (1 shared connections)
- [[Permissions Model & Tests]] (1 shared connections)
- [[Stock Prediction Tests]] (1 shared connections)
- [[Services API Tests]] (1 shared connections)

## Source Files

- `backend/app/main.py`
- `backend/tests/api/routes/test_utils.py`
- `backend/tests/conftest.py`

## Audit Trail

- EXTRACTED: 153 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
