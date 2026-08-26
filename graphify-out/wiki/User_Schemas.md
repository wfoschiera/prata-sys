# User Schemas

> 24 nodes · cohesion 0.26

## Key Concepts

- **SessionDep** (19 connections) — `backend/app/api/routes/users.py`
- **Any** (18 connections) — `backend/app/api/routes/users.py`
- **CurrentUser** (16 connections) — `backend/app/api/routes/users.py`
- **UUID** (14 connections) — `backend/app/api/routes/users.py`
- **Message** (13 connections) — `backend/app/api/routes/users.py`
- **users.py** (13 connections) — `backend/app/api/routes/users.py`
- **UsersPublic** (12 connections) — `backend/app/models.py`
- **UpdatePassword** (11 connections) — `backend/app/models.py`
- **UserUpdateMe** (11 connections) — `backend/app/models.py`
- **UserCreate** (11 connections) — `backend/app/api/routes/users.py`
- **UserUpdate** (11 connections) — `backend/app/api/routes/users.py`
- **UpdatePassword** (11 connections) — `backend/app/api/routes/users.py`
- **UserUpdateMe** (11 connections) — `backend/app/api/routes/users.py`
- **update_password_me()** (8 connections) — `backend/app/api/routes/users.py`
- **create_user()** (6 connections) — `backend/app/api/routes/users.py`
- **read_user_by_id()** (6 connections) — `backend/app/api/routes/users.py`
- **read_user_me()** (6 connections) — `backend/app/api/routes/users.py`
- **delete_user()** (5 connections) — `backend/app/api/routes/users.py`
- **delete_user_me()** (5 connections) — `backend/app/api/routes/users.py`
- **update_user()** (5 connections) — `backend/app/api/routes/users.py`
- **update_user_me()** (5 connections) — `backend/app/api/routes/users.py`
- **read_users()** (4 connections) — `backend/app/api/routes/users.py`
- **Get current user, including effective permissions.** (1 connections) — `backend/app/api/routes/users.py`
- **Get a specific user by id.** (1 connections) — `backend/app/api/routes/users.py`

## Relationships

- [[Backend CRUD Core]] (26 shared connections)
- [[Login Router & Schemas]] (18 shared connections)
- [[Permissions Model & Tests]] (10 shared connections)
- [[Estoque Router]] (9 shared connections)
- [[Service API Schemas]] (9 shared connections)
- [[Email Utilities]] (3 shared connections)
- [[Password Reset Tokens]] (1 shared connections)
- [[User CRUD Tests]] (1 shared connections)

## Source Files

- `backend/app/api/routes/users.py`
- `backend/app/models.py`

## Audit Trail

- EXTRACTED: 103 (46%)
- INFERRED: 120 (54%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
