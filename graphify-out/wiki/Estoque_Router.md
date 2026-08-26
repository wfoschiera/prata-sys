# Estoque Router

> 23 nodes · cohesion 0.17

## Key Concepts

- **SessionDep** (115 connections) — `backend/app/api/deps.py`
- **permissions.py** (10 connections) — `backend/app/api/routes/permissions.py`
- **_build_user_permissions_out()** (7 connections) — `backend/app/api/routes/permissions.py`
- **set_user_permissions()** (6 connections) — `backend/app/api/routes/permissions.py`
- **create_user()** (6 connections) — `backend/app/api/routes/private.py`
- **PrivateUserCreate** (6 connections) — `backend/app/api/routes/private.py`
- **Any** (5 connections) — `backend/app/api/routes/permissions.py`
- **SessionDep** (5 connections) — `backend/app/api/routes/permissions.py`
- **UUID** (5 connections) — `backend/app/api/routes/permissions.py`
- **get_user_permissions()** (5 connections) — `backend/app/api/routes/permissions.py`
- **SetPermissionsIn** (5 connections) — `backend/app/api/routes/permissions.py`
- **UserPermissionsOut** (5 connections) — `backend/app/api/routes/permissions.py`
- **Any** (4 connections) — `backend/app/api/routes/private.py`
- **SessionDep** (4 connections) — `backend/app/api/routes/private.py`
- **get_users_permissions()** (4 connections) — `backend/app/api/routes/permissions.py`
- **CategoryDashboardItem** (3 connections) — `backend/app/api/routes/estoque.py`
- **SessionDep** (3 connections) — `backend/app/api/routes/estoque.py`
- **User** (3 connections) — `backend/app/api/routes/permissions.py`
- **BaseModel** (3 connections)
- **estoque.py** (3 connections) — `backend/app/api/routes/estoque.py`
- **get_dashboard()** (3 connections) — `backend/app/api/routes/estoque.py`
- **private.py** (3 connections) — `backend/app/api/routes/private.py`
- **get_available_permissions()** (1 connections) — `backend/app/api/routes/permissions.py`

## Relationships

- [[Backend CRUD Core]] (41 shared connections)
- [[Inventory & Supplier Schemas]] (19 shared connections)
- [[Service API Schemas]] (14 shared connections)
- [[Login Router & Schemas]] (13 shared connections)
- [[Fornecedor Schemas]] (9 shared connections)
- [[User Schemas]] (9 shared connections)
- [[Clients Router]] (7 shared connections)
- [[Company Settings Subsystem]] (3 shared connections)
- [[Email Utilities]] (3 shared connections)
- [[Auth Dependencies (deps.py)]] (2 shared connections)
- [[Operational Dashboard Router]] (2 shared connections)
- [[Orcamentos Router]] (2 shared connections)

## Source Files

- `backend/app/api/deps.py`
- `backend/app/api/routes/estoque.py`
- `backend/app/api/routes/permissions.py`
- `backend/app/api/routes/private.py`

## Audit Trail

- EXTRACTED: 73 (34%)
- INFERRED: 141 (66%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
