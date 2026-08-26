# Company Settings Tests

> 21 nodes · cohesion 0.13

## Key Concepts

- **test_settings.py** (10 connections) — `backend/tests/api/routes/test_settings.py`
- **TestClient** (9 connections) — `backend/tests/api/routes/test_settings.py`
- **test_get_company_settings_admin_can_view()** (3 connections) — `backend/tests/api/routes/test_settings.py`
- **test_get_company_settings_client_forbidden()** (3 connections) — `backend/tests/api/routes/test_settings.py`
- **test_get_company_settings_finance_can_view()** (3 connections) — `backend/tests/api/routes/test_settings.py`
- **test_get_company_settings_returns_default()** (3 connections) — `backend/tests/api/routes/test_settings.py`
- **test_update_company_settings_creates_first_time()** (3 connections) — `backend/tests/api/routes/test_settings.py`
- **test_update_company_settings_finance_forbidden()** (3 connections) — `backend/tests/api/routes/test_settings.py`
- **test_update_company_settings_non_superuser_forbidden()** (3 connections) — `backend/tests/api/routes/test_settings.py`
- **test_update_company_settings_unauthenticated()** (3 connections) — `backend/tests/api/routes/test_settings.py`
- **test_update_company_settings_updates_existing()** (3 connections) — `backend/tests/api/routes/test_settings.py`
- **Tests for /api/v1/settings endpoints (company settings).** (1 connections) — `backend/tests/api/routes/test_settings.py`
- **Only superusers can update company settings; admin gets 403.** (1 connections) — `backend/tests/api/routes/test_settings.py`
- **Finance role cannot update company settings.** (1 connections) — `backend/tests/api/routes/test_settings.py`
- **Unauthenticated request should return 401.** (1 connections) — `backend/tests/api/routes/test_settings.py`
- **When no settings exist yet, return defaults.** (1 connections) — `backend/tests/api/routes/test_settings.py`
- **Admin role (view_dashboard) can read company settings.** (1 connections) — `backend/tests/api/routes/test_settings.py`
- **Finance role (view_dashboard) can read company settings.** (1 connections) — `backend/tests/api/routes/test_settings.py`
- **Client role does NOT have view_dashboard, should be 403.** (1 connections) — `backend/tests/api/routes/test_settings.py`
- **First PUT creates the singleton settings row.** (1 connections) — `backend/tests/api/routes/test_settings.py`
- **Second PUT updates the existing settings row.** (1 connections) — `backend/tests/api/routes/test_settings.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `backend/tests/api/routes/test_settings.py`

## Audit Trail

- EXTRACTED: 56 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
