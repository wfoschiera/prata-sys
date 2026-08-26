# Permissions Model & Tests

> 44 nodes · cohesion 0.09

## Key Concepts

- **UserCreate** (129 connections) — `backend/app/models.py`
- **test_permissions.py** (27 connections) — `backend/tests/api/routes/test_permissions.py`
- **TestClient** (18 connections) — `backend/tests/api/routes/test_permissions.py`
- **Session** (15 connections) — `backend/tests/api/routes/test_permissions.py`
- **get_effective_permissions()** (8 connections) — `backend/app/core/permissions.py`
- **test_require_permission_allows_override()** (7 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_effective_no_duplicate()** (6 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_effective_with_overrides()** (6 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_set_overrides_deduplicates()** (6 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_set_overrides_filters_role_defaults()** (6 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_set_overrides_twice_adds_second()** (6 connections) — `backend/tests/api/routes/test_permissions.py`
- **_setup_test_db()** (6 connections) — `backend/tests/conftest.py`
- **init_db()** (5 connections) — `backend/app/core/db.py`
- **test_clear_user_permissions()** (5 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_get_single_user_permissions()** (5 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_set_overrides_invalid_permission()** (5 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_set_user_overrides()** (5 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_set_user_permissions_invalid_permission_raises()** (5 connections) — `backend/tests/api/routes/test_permissions.py`
- **Session** (4 connections) — `backend/app/core/db.py`
- **db.py** (3 connections) — `backend/app/core/db.py`
- **test_get_available_permissions_admin()** (3 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_require_permission_allows_role_default()** (3 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_require_permission_denies_no_permission()** (3 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_require_permission_superuser_bypass()** (3 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_set_user_permissions_invalid_user_raises()** (3 connections) — `backend/tests/api/routes/test_permissions.py`
- *... and 19 more nodes in this community*

## Relationships

- [[Backend CRUD Core]] (84 shared connections)
- [[User CRUD Tests]] (21 shared connections)
- [[Users Security Tests]] (17 shared connections)
- [[User Schemas]] (10 shared connections)
- [[Token Revocation Tests]] (8 shared connections)
- [[Role Defaults Logic]] (5 shared connections)
- [[Password Reset Tokens]] (2 shared connections)
- [[Initial Data Script]] (1 shared connections)
- [[API Core Tests]] (1 shared connections)

## Source Files

- `backend/app/core/db.py`
- `backend/app/core/permissions.py`
- `backend/app/models.py`
- `backend/tests/api/routes/test_permissions.py`
- `backend/tests/conftest.py`

## Audit Trail

- EXTRACTED: 200 (63%)
- INFERRED: 115 (37%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
