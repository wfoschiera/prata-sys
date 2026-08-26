# Service API Schemas

> 43 nodes · cohesion 0.16

## Key Concepts

- **CurrentUser** (51 connections) — `backend/app/api/deps.py`
- **ServiceRead** (32 connections) — `backend/app/models.py`
- **SessionDep** (25 connections) — `backend/app/api/routes/services.py`
- **UUID** (24 connections) — `backend/app/api/routes/services.py`
- **Service** (18 connections) — `backend/app/api/routes/services.py`
- **ServiceTransitionRequest** (17 connections) — `backend/app/models.py`
- **CurrentUser** (17 connections) — `backend/app/api/routes/services.py`
- **ServiceItemRead** (16 connections) — `backend/app/models.py`
- **ServicesPublic** (16 connections) — `backend/app/models.py`
- **ServiceTransitionResponse** (16 connections) — `backend/app/models.py`
- **BaixarEstoqueResponse** (16 connections) — `backend/app/api/routes/services.py`
- **DeductionSummary** (16 connections) — `backend/app/api/routes/services.py`
- **Request** (16 connections) — `backend/app/api/routes/services.py`
- **ServiceCreate** (16 connections) — `backend/app/api/routes/services.py`
- **ServiceItem** (16 connections) — `backend/app/api/routes/services.py`
- **ServiceItemCreate** (16 connections) — `backend/app/api/routes/services.py`
- **ServiceUpdate** (16 connections) — `backend/app/api/routes/services.py`
- **ServicesPublic** (16 connections) — `backend/app/api/routes/services.py`
- **ServiceTransitionRequest** (16 connections) — `backend/app/api/routes/services.py`
- **ServiceTransitionResponse** (16 connections) — `backend/app/api/routes/services.py`
- **services.py** (12 connections) — `backend/app/api/routes/services.py`
- **transition_service()** (7 connections) — `backend/app/api/routes/services.py`
- **update_service()** (7 connections) — `backend/app/api/routes/services.py`
- **create_service_item()** (6 connections) — `backend/app/api/routes/services.py`
- **deduct_stock()** (6 connections) — `backend/app/api/routes/services.py`
- *... and 18 more nodes in this community*

## Relationships

- [[Backend CRUD Core]] (150 shared connections)
- [[Estoque Router]] (14 shared connections)
- [[Login Router & Schemas]] (10 shared connections)
- [[User Schemas]] (9 shared connections)
- [[Orcamentos Router]] (4 shared connections)
- [[Auth Dependencies (deps.py)]] (2 shared connections)

## Source Files

- `backend/app/api/deps.py`
- `backend/app/api/routes/services.py`
- `backend/app/models.py`

## Audit Trail

- EXTRACTED: 124 (26%)
- INFERRED: 345 (74%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
