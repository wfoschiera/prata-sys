# Email Utilities

> 17 nodes · cohesion 0.18

## Key Concepts

- **utils.py** (15 connections) — `backend/app/utils.py`
- **utils.py** (6 connections) — `backend/app/api/routes/utils.py`
- **EmailData** (5 connections) — `backend/app/utils.py`
- **generate_reset_password_email()** (5 connections) — `backend/app/utils.py`
- **render_email_template()** (5 connections) — `backend/app/utils.py`
- **test_email()** (5 connections) — `backend/app/api/routes/utils.py`
- **generate_new_account_email()** (4 connections) — `backend/app/utils.py`
- **generate_test_email()** (4 connections) — `backend/app/utils.py`
- **Message** (4 connections) — `backend/app/api/routes/utils.py`
- **readiness()** (4 connections) — `backend/app/api/routes/utils.py`
- **send_email()** (3 connections) — `backend/app/utils.py`
- **verify_password_reset_token()** (3 connections) — `backend/app/utils.py`
- **SessionDep** (3 connections) — `backend/app/api/routes/utils.py`
- **EmailStr** (3 connections) — `backend/app/api/routes/utils.py`
- **Decode and validate a password reset JWT.      Returns the email address if the** (1 connections) — `backend/app/utils.py`
- **health_check()** (1 connections) — `backend/app/api/routes/utils.py`
- **Readiness probe: verify the database is reachable.      Returns 200 when a trivi** (1 connections) — `backend/app/api/routes/utils.py`

## Relationships

- [[Login Router & Schemas]] (7 shared connections)
- [[Password Reset Tokens]] (6 shared connections)
- [[User Schemas]] (3 shared connections)
- [[Estoque Router]] (3 shared connections)
- [[Backend CRUD Core]] (2 shared connections)
- [[Operational Dashboard Router]] (1 shared connections)

## Source Files

- `backend/app/api/routes/utils.py`
- `backend/app/utils.py`

## Audit Trail

- EXTRACTED: 62 (86%)
- INFERRED: 10 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
