# Auth Dependencies (deps.py)

> 11 nodes · cohesion 0.27

## Key Concepts

- **TokenPayload** (9 connections) — `backend/app/models.py`
- **deps.py** (6 connections) — `backend/app/api/deps.py`
- **get_current_user()** (5 connections) — `backend/app/api/deps.py`
- **User** (4 connections) — `backend/app/api/deps.py`
- **get_current_active_superuser()** (3 connections) — `backend/app/api/deps.py`
- **require_permission()** (3 connections) — `backend/app/api/deps.py`
- **Any** (3 connections) — `backend/app/api/deps.py`
- **Session** (3 connections) — `backend/app/api/deps.py`
- **TokenDep** (3 connections) — `backend/app/api/deps.py`
- **get_db()** (2 connections) — `backend/app/api/deps.py`
- **Dependency factory. Checks that the current user has ALL listed     permissions** (1 connections) — `backend/app/api/deps.py`

## Relationships

- [[Backend CRUD Core]] (8 shared connections)
- [[Service API Schemas]] (2 shared connections)
- [[Estoque Router]] (2 shared connections)

## Source Files

- `backend/app/api/deps.py`
- `backend/app/models.py`

## Audit Trail

- EXTRACTED: 28 (67%)
- INFERRED: 14 (33%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
