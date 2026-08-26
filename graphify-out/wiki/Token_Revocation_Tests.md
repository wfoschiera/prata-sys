# Token Revocation Tests

> 14 nodes · cohesion 0.19

## Key Concepts

- **test_old_token_rejected_after_reset_password()** (9 connections) — `backend/tests/api/routes/test_token_revocation.py`
- **test_old_token_rejected_after_self_password_change()** (8 connections) — `backend/tests/api/routes/test_token_revocation.py`
- **user_authentication_headers()** (8 connections) — `backend/tests/utils/user.py`
- **Session** (6 connections) — `backend/tests/api/routes/test_token_revocation.py`
- **create_random_user()** (6 connections) — `backend/tests/utils/user.py`
- **TestClient** (5 connections) — `backend/tests/api/routes/test_token_revocation.py`
- **test_token_revocation.py** (5 connections) — `backend/tests/api/routes/test_token_revocation.py`
- **test_user_model_defaults_token_version_to_zero()** (5 connections) — `backend/tests/api/routes/test_token_revocation.py`
- **user.py** (4 connections) — `backend/tests/utils/user.py`
- **Session** (3 connections) — `backend/tests/utils/user.py`
- **TestClient** (3 connections) — `backend/tests/utils/user.py`
- **User** (3 connections) — `backend/tests/utils/user.py`
- **Changing a user's own password must bump token_version and     invalidate previo** (1 connections) — `backend/tests/api/routes/test_token_revocation.py`
- **Resetting a password via the recovery flow (crud.update_user) must     also bump** (1 connections) — `backend/tests/api/routes/test_token_revocation.py`

## Relationships

- [[Backend CRUD Core]] (12 shared connections)
- [[Permissions Model & Tests]] (8 shared connections)
- [[Users Security Tests]] (8 shared connections)
- [[User CRUD Tests]] (4 shared connections)
- [[Password Reset Tokens]] (1 shared connections)

## Source Files

- `backend/tests/api/routes/test_token_revocation.py`
- `backend/tests/utils/user.py`

## Audit Trail

- EXTRACTED: 38 (57%)
- INFERRED: 29 (43%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
