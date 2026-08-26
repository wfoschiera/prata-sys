# User CRUD Tests

> 20 nodes · cohesion 0.21

## Key Concepts

- **random_lower_string()** (73 connections) — `backend/tests/utils/utils.py`
- **Session** (14 connections) — `backend/tests/crud/test_user.py`
- **test_user.py** (13 connections) — `backend/tests/crud/test_user.py`
- **verify_password()** (8 connections) — `backend/app/core/security.py`
- **test_authenticate_user_with_bcrypt_upgrades_to_argon2()** (7 connections) — `backend/tests/crud/test_user.py`
- **test_update_user()** (7 connections) — `backend/tests/crud/test_user.py`
- **test_create_user_ignores_is_superuser_on_schema()** (6 connections) — `backend/tests/crud/test_user.py`
- **test_authenticate_user()** (5 connections) — `backend/tests/crud/test_user.py`
- **test_check_if_user_is_active()** (5 connections) — `backend/tests/crud/test_user.py`
- **test_check_if_user_is_active_inactive()** (5 connections) — `backend/tests/crud/test_user.py`
- **test_check_if_user_is_superuser()** (5 connections) — `backend/tests/crud/test_user.py`
- **test_check_if_user_is_superuser_normal_user()** (5 connections) — `backend/tests/crud/test_user.py`
- **test_create_user()** (5 connections) — `backend/tests/crud/test_user.py`
- **test_get_user()** (5 connections) — `backend/tests/crud/test_user.py`
- **test_not_authenticate_user()** (4 connections) — `backend/tests/crud/test_user.py`
- **utils.py** (3 connections) — `backend/tests/utils/utils.py`
- **get_superuser_token_headers()** (2 connections) — `backend/tests/utils/utils.py`
- **TestClient** (1 connections) — `backend/tests/utils/utils.py`
- **Test that a user with bcrypt password hash gets upgraded to argon2 on login.** (1 connections) — `backend/tests/crud/test_user.py`
- **UserCreate no longer accepts is_superuser — passing it must have no     effect;** (1 connections) — `backend/tests/crud/test_user.py`

## Relationships

- [[Users Security Tests]] (34 shared connections)
- [[Permissions Model & Tests]] (21 shared connections)
- [[Estoque API Tests]] (13 shared connections)
- [[Password Reset Tokens]] (8 shared connections)
- [[Backend CRUD Core]] (7 shared connections)
- [[Fornecedores API Tests]] (5 shared connections)
- [[Token Revocation Tests]] (4 shared connections)
- [[User Schemas]] (1 shared connections)
- [[Operational Dashboard Router]] (1 shared connections)
- [[Transacoes API Tests]] (1 shared connections)

## Source Files

- `backend/app/core/security.py`
- `backend/tests/crud/test_user.py`
- `backend/tests/utils/utils.py`

## Audit Trail

- EXTRACTED: 70 (40%)
- INFERRED: 105 (60%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
