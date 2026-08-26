# Users Security Tests

> 43 nodes · cohesion 0.12

## Key Concepts

- **random_email()** (46 connections) — `backend/tests/utils/utils.py`
- **TestClient** (34 connections) — `backend/tests/api/routes/test_users.py`
- **test_users.py** (33 connections) — `backend/tests/api/routes/test_users.py`
- **Session** (25 connections) — `backend/tests/api/routes/test_users.py`
- **test_create_user_by_unprivileged_user()** (8 connections) — `backend/tests/api/routes/test_users.py`
- **test_delete_user_without_privileges()** (8 connections) — `backend/tests/api/routes/test_users.py`
- **test_update_user_can_still_change_role()** (7 connections) — `backend/tests/api/routes/test_users.py`
- **test_update_user_ignores_is_superuser_mass_assignment()** (7 connections) — `backend/tests/api/routes/test_users.py`
- **test_update_user_role_change_clears_permissions()** (7 connections) — `backend/tests/api/routes/test_users.py`
- **test_update_user_same_role_keeps_permissions()** (7 connections) — `backend/tests/api/routes/test_users.py`
- **test_create_user_existing_username()** (6 connections) — `backend/tests/api/routes/test_users.py`
- **test_create_user_ignores_is_superuser_mass_assignment()** (6 connections) — `backend/tests/api/routes/test_users.py`
- **test_delete_user_me()** (6 connections) — `backend/tests/api/routes/test_users.py`
- **test_delete_user_super_user()** (6 connections) — `backend/tests/api/routes/test_users.py`
- **test_get_existing_user_as_superuser()** (6 connections) — `backend/tests/api/routes/test_users.py`
- **test_get_existing_user_current_user()** (6 connections) — `backend/tests/api/routes/test_users.py`
- **test_retrieve_users()** (6 connections) — `backend/tests/api/routes/test_users.py`
- **test_signup_endpoint_removed()** (6 connections) — `backend/tests/api/routes/test_users.py`
- **test_update_password_me()** (6 connections) — `backend/tests/api/routes/test_users.py`
- **test_update_user()** (6 connections) — `backend/tests/api/routes/test_users.py`
- **test_update_user_email_exists()** (6 connections) — `backend/tests/api/routes/test_users.py`
- **test_update_user_me_email_exists()** (6 connections) — `backend/tests/api/routes/test_users.py`
- **test_create_user_new_email()** (5 connections) — `backend/tests/api/routes/test_users.py`
- **test_get_existing_user_permissions_error()** (4 connections) — `backend/tests/api/routes/test_users.py`
- **test_update_user_me()** (4 connections) — `backend/tests/api/routes/test_users.py`
- *... and 18 more nodes in this community*

## Relationships

- [[User CRUD Tests]] (34 shared connections)
- [[Permissions Model & Tests]] (17 shared connections)
- [[Password Reset Tokens]] (9 shared connections)
- [[Token Revocation Tests]] (8 shared connections)
- [[Backend CRUD Core]] (6 shared connections)
- [[API Core Tests]] (1 shared connections)

## Source Files

- `backend/tests/api/routes/test_users.py`
- `backend/tests/utils/utils.py`

## Audit Trail

- EXTRACTED: 203 (68%)
- INFERRED: 94 (32%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
