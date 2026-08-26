# Clients API Tests

> 32 nodes · cohesion 0.16

## Key Concepts

- **test_clients.py** (28 connections) — `backend/tests/api/routes/test_clients.py`
- **TestClient** (27 connections) — `backend/tests/api/routes/test_clients.py`
- **Session** (16 connections) — `backend/tests/api/routes/test_clients.py`
- **Client** (14 connections) — `backend/tests/api/routes/test_clients.py`
- **test_update_client_duplicate_document()** (5 connections) — `backend/tests/api/routes/test_clients.py`
- **test_update_client_same_document_no_conflict()** (5 connections) — `backend/tests/api/routes/test_clients.py`
- **test_create_client_duplicate_document()** (4 connections) — `backend/tests/api/routes/test_clients.py`
- **test_delete_client()** (4 connections) — `backend/tests/api/routes/test_clients.py`
- **test_delete_client_unauthenticated()** (4 connections) — `backend/tests/api/routes/test_clients.py`
- **test_delete_client_wrong_role_forbidden()** (4 connections) — `backend/tests/api/routes/test_clients.py`
- **test_read_client()** (4 connections) — `backend/tests/api/routes/test_clients.py`
- **test_read_client_unauthenticated()** (4 connections) — `backend/tests/api/routes/test_clients.py`
- **test_read_clients_pagination()** (4 connections) — `backend/tests/api/routes/test_clients.py`
- **test_read_clients_superuser()** (4 connections) — `backend/tests/api/routes/test_clients.py`
- **test_update_client_document_number()** (4 connections) — `backend/tests/api/routes/test_clients.py`
- **test_update_client_name()** (4 connections) — `backend/tests/api/routes/test_clients.py`
- **test_update_client_unauthenticated()** (4 connections) — `backend/tests/api/routes/test_clients.py`
- **test_create_client_cpf()** (3 connections) — `backend/tests/api/routes/test_clients.py`
- **test_read_clients_finance_user_forbidden()** (3 connections) — `backend/tests/api/routes/test_clients.py`
- **test_read_clients_no_permission_forbidden()** (3 connections) — `backend/tests/api/routes/test_clients.py`
- **test_create_client_cnpj()** (2 connections) — `backend/tests/api/routes/test_clients.py`
- **test_create_client_document_with_letters()** (2 connections) — `backend/tests/api/routes/test_clients.py`
- **test_create_client_invalid_cpf_length()** (2 connections) — `backend/tests/api/routes/test_clients.py`
- **test_create_client_unauthenticated()** (2 connections) — `backend/tests/api/routes/test_clients.py`
- **test_create_client_wrong_role_forbidden()** (2 connections) — `backend/tests/api/routes/test_clients.py`
- *... and 7 more nodes in this community*

## Relationships

- [[Backend CRUD Core]] (10 shared connections)
- [[Service Transition Unit Tests]] (1 shared connections)

## Source Files

- `backend/tests/api/routes/test_clients.py`

## Audit Trail

- EXTRACTED: 163 (96%)
- INFERRED: 6 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
