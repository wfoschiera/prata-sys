# Operational Dashboard Router

> 10 nodes · cohesion 0.20

## Key Concepts

- **datetime** (12 connections) — `backend/app/models.py`
- **security.py** (4 connections) — `backend/app/core/security.py`
- **get_operational_dashboard()** (4 connections) — `backend/app/api/routes/dashboard.py`
- **timedelta** (4 connections) — `backend/app/core/security.py`
- **SessionDep** (3 connections) — `backend/app/api/routes/dashboard.py`
- **YearlyOperationalDashboard** (3 connections) — `backend/app/api/routes/dashboard.py`
- **create_access_token()** (3 connections) — `backend/app/core/security.py`
- **dashboard.py** (3 connections) — `backend/app/api/routes/dashboard.py`
- **Any** (1 connections) — `backend/app/core/security.py`
- **Weekly operational KPIs for the given year.      Returns a list of WeeklyOperati** (1 connections) — `backend/app/api/routes/dashboard.py`

## Relationships

- [[Backend CRUD Core]] (8 shared connections)
- [[Estoque Router]] (2 shared connections)
- [[Password Reset Tokens]] (2 shared connections)
- [[Login Router & Schemas]] (2 shared connections)
- [[User CRUD Tests]] (1 shared connections)
- [[Orcamentos Router]] (1 shared connections)
- [[Email Utilities]] (1 shared connections)
- [[Operational Dashboard Tests]] (1 shared connections)
- [[Transacoes API Tests]] (1 shared connections)
- [[Service Transition Unit Tests]] (1 shared connections)

## Source Files

- `backend/app/api/routes/dashboard.py`
- `backend/app/core/security.py`
- `backend/app/models.py`

## Audit Trail

- EXTRACTED: 31 (82%)
- INFERRED: 7 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
