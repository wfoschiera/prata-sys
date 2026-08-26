# Password Reset Tokens

> 39 nodes · cohesion 0.10

## Key Concepts

- **test_login.py** (23 connections) — `backend/tests/api/routes/test_login.py`
- **TestClient** (21 connections) — `backend/tests/api/routes/test_login.py`
- **Session** (10 connections) — `backend/tests/api/routes/test_login.py`
- **test_reset_password_already_used_token()** (10 connections) — `backend/tests/api/routes/test_login.py`
- **create_user()** (9 connections) — `backend/app/crud.py`
- **UsedPasswordResetToken** (9 connections) — `backend/app/models.py`
- **generate_password_reset_token()** (9 connections) — `backend/app/utils.py`
- **test_reset_password()** (9 connections) — `backend/tests/api/routes/test_login.py`
- **claim_password_reset_token()** (7 connections) — `backend/app/utils.py`
- **test_login_with_argon2_password_keeps_hash()** (7 connections) — `backend/tests/api/routes/test_login.py`
- **test_login_with_bcrypt_password_upgrades_to_argon2()** (7 connections) — `backend/tests/api/routes/test_login.py`
- **test_reset_password_inactive_user()** (7 connections) — `backend/tests/api/routes/test_login.py`
- **get_password_hash()** (6 connections) — `backend/app/core/security.py`
- **test_claim_password_reset_token()** (6 connections) — `backend/tests/api/routes/test_login.py`
- **test_get_access_token_inactive_user()** (6 connections) — `backend/tests/api/routes/test_login.py`
- **_token_hash()** (4 connections) — `backend/app/utils.py`
- **test_recover_password_rate_limited()** (4 connections) — `backend/tests/api/routes/test_login.py`
- **test_recover_password_same_response_and_background_send()** (4 connections) — `backend/tests/api/routes/test_login.py`
- **Any** (3 connections) — `backend/app/utils.py`
- **test_reset_password_nonexistent_user()** (3 connections) — `backend/tests/api/routes/test_login.py`
- **test_reset_password_rate_limited()** (3 connections) — `backend/tests/api/routes/test_login.py`
- **test_get_access_token()** (2 connections) — `backend/tests/api/routes/test_login.py`
- **test_get_access_token_incorrect_password()** (2 connections) — `backend/tests/api/routes/test_login.py`
- **test_recover_password_html_content()** (2 connections) — `backend/tests/api/routes/test_login.py`
- **test_recover_password_html_content_not_found()** (2 connections) — `backend/tests/api/routes/test_login.py`
- *... and 14 more nodes in this community*

## Relationships

- [[Backend CRUD Core]] (12 shared connections)
- [[Users Security Tests]] (9 shared connections)
- [[User CRUD Tests]] (8 shared connections)
- [[Email Utilities]] (6 shared connections)
- [[Login Router & Schemas]] (3 shared connections)
- [[Operational Dashboard Router]] (2 shared connections)
- [[Permissions Model & Tests]] (2 shared connections)
- [[Estoque Router]] (1 shared connections)
- [[User Schemas]] (1 shared connections)
- [[Token Revocation Tests]] (1 shared connections)

## Source Files

- `backend/app/core/security.py`
- `backend/app/crud.py`
- `backend/app/models.py`
- `backend/app/utils.py`
- `backend/tests/api/routes/test_login.py`

## Audit Trail

- EXTRACTED: 151 (78%)
- INFERRED: 42 (22%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
