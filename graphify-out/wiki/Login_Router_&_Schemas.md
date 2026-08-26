# Login Router & Schemas

> 22 nodes · cohesion 0.28

## Key Concepts

- **Message** (31 connections) — `backend/app/models.py`
- **UserPublic** (24 connections) — `backend/app/models.py`
- **NewPassword** (12 connections) — `backend/app/models.py`
- **Token** (12 connections) — `backend/app/models.py`
- **SessionDep** (11 connections) — `backend/app/api/routes/login.py`
- **Request** (10 connections) — `backend/app/api/routes/login.py`
- **Any** (9 connections) — `backend/app/api/routes/login.py`
- **Message** (9 connections) — `backend/app/api/routes/login.py`
- **CurrentUser** (8 connections) — `backend/app/api/routes/login.py`
- **login.py** (8 connections) — `backend/app/api/routes/login.py`
- **BackgroundTasks** (8 connections) — `backend/app/api/routes/login.py`
- **Depends** (8 connections) — `backend/app/api/routes/login.py`
- **NewPassword** (8 connections) — `backend/app/api/routes/login.py`
- **OAuth2PasswordRequestForm** (8 connections) — `backend/app/api/routes/login.py`
- **login_access_token()** (8 connections) — `backend/app/api/routes/login.py`
- **Token** (8 connections) — `backend/app/api/routes/login.py`
- **recover_password()** (7 connections) — `backend/app/api/routes/login.py`
- **reset_password()** (7 connections) — `backend/app/api/routes/login.py`
- **recover_password_html_content()** (6 connections) — `backend/app/api/routes/login.py`
- **test_token()** (3 connections) — `backend/app/api/routes/login.py`
- **HTML Content for Password Recovery** (1 connections) — `backend/app/api/routes/login.py`
- **OAuth2 compatible token login, get an access token for future requests** (1 connections) — `backend/app/api/routes/login.py`

## Relationships

- [[Backend CRUD Core]] (19 shared connections)
- [[User Schemas]] (18 shared connections)
- [[Estoque Router]] (13 shared connections)
- [[Service API Schemas]] (10 shared connections)
- [[Clients Router]] (7 shared connections)
- [[Email Utilities]] (7 shared connections)
- [[Password Reset Tokens]] (3 shared connections)
- [[Operational Dashboard Router]] (2 shared connections)

## Source Files

- `backend/app/api/routes/login.py`
- `backend/app/models.py`

## Audit Trail

- EXTRACTED: 59 (29%)
- INFERRED: 148 (71%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
