# Role Defaults Logic

> 10 nodes · cohesion 0.20

## Key Concepts

- **get_role_defaults()** (12 connections) — `backend/app/core/permissions.py`
- **permissions.py** (5 connections) — `backend/app/core/permissions.py`
- **test_role_defaults_admin()** (2 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_role_defaults_client()** (2 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_role_defaults_finance()** (2 connections) — `backend/tests/api/routes/test_permissions.py`
- **test_admin_role_has_view_financeiro()** (2 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_client_role_has_no_finance_permissions()** (2 connections) — `backend/tests/api/routes/test_transacoes.py`
- **test_finance_role_has_manage_financeiro()** (2 connections) — `backend/tests/api/routes/test_transacoes.py`
- **Role-based permissions with per-user overrides.  Two-tier model: 1. Role default** (1 connections) — `backend/app/core/permissions.py`
- **Return the default permission set for a role.** (1 connections) — `backend/app/core/permissions.py`

## Relationships

- [[Permissions Model & Tests]] (5 shared connections)
- [[Backend CRUD Core]] (4 shared connections)
- [[Transacoes API Tests]] (3 shared connections)
- [[Estoque Router]] (1 shared connections)

## Source Files

- `backend/app/core/permissions.py`
- `backend/tests/api/routes/test_permissions.py`
- `backend/tests/api/routes/test_transacoes.py`

## Audit Trail

- EXTRACTED: 17 (55%)
- INFERRED: 14 (45%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
