# Clients Router

> 16 nodes · cohesion 0.30

## Key Concepts

- **SessionDep** (12 connections) — `backend/app/api/routes/clients.py`
- **UUID** (11 connections) — `backend/app/api/routes/clients.py`
- **Client** (10 connections) — `backend/app/api/routes/clients.py`
- **ClientPublic** (9 connections) — `backend/app/models.py`
- **ClientsPublic** (9 connections) — `backend/app/models.py`
- **ClientCreate** (8 connections) — `backend/app/api/routes/clients.py`
- **ClientUpdate** (8 connections) — `backend/app/api/routes/clients.py`
- **Message** (8 connections) — `backend/app/api/routes/clients.py`
- **ClientsPublic** (8 connections) — `backend/app/api/routes/clients.py`
- **clients.py** (7 connections) — `backend/app/api/routes/clients.py`
- **update_client()** (5 connections) — `backend/app/api/routes/clients.py`
- **create_client()** (4 connections) — `backend/app/api/routes/clients.py`
- **delete_client()** (4 connections) — `backend/app/api/routes/clients.py`
- **read_client()** (4 connections) — `backend/app/api/routes/clients.py`
- **read_clients()** (4 connections) — `backend/app/api/routes/clients.py`
- **List clients (admin and finance only).** (1 connections) — `backend/app/api/routes/clients.py`

## Relationships

- [[Backend CRUD Core]] (26 shared connections)
- [[Estoque Router]] (7 shared connections)
- [[Login Router & Schemas]] (7 shared connections)

## Source Files

- `backend/app/api/routes/clients.py`
- `backend/app/models.py`

## Audit Trail

- EXTRACTED: 49 (44%)
- INFERRED: 63 (56%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
