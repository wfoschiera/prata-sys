# App Settings Config

> 20 nodes · cohesion 0.15

## Key Concepts

- **Settings** (12 connections) — `backend/app/core/config.py`
- **test_missing_secret_key_raises_outside_local()** (5 connections) — `backend/tests/core/test_config.py`
- **test_config.py** (4 connections) — `backend/tests/core/test_config.py`
- **_base_kwargs()** (4 connections) — `backend/tests/core/test_config.py`
- **test_explicit_secret_key_allowed_in_production()** (4 connections) — `backend/tests/core/test_config.py`
- **test_missing_secret_key_allowed_in_local()** (4 connections) — `backend/tests/core/test_config.py`
- **MonkeyPatch** (4 connections) — `backend/tests/core/test_config.py`
- **._enforce_non_default_secrets()** (3 connections) — `backend/app/core/config.py`
- **config.py** (2 connections) — `backend/app/core/config.py`
- **parse_cors()** (2 connections) — `backend/app/core/config.py`
- **._check_default_secret()** (2 connections) — `backend/app/core/config.py`
- **._set_default_emails_from()** (2 connections) — `backend/app/core/config.py`
- **.SQLALCHEMY_DATABASE_URI()** (2 connections) — `backend/app/core/config.py`
- **Self** (2 connections) — `backend/app/core/config.py`
- **Any** (1 connections) — `backend/app/core/config.py`
- **BaseSettings** (1 connections)
- **.all_cors_origins()** (1 connections) — `backend/app/core/config.py`
- **.emails_enabled()** (1 connections) — `backend/app/core/config.py`
- **SEC-010: an unset SECRET_KEY must fail closed outside local dev,     instead of** (1 connections) — `backend/tests/core/test_config.py`
- **PostgresDsn** (1 connections) — `backend/app/core/config.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `backend/app/core/config.py`
- `backend/tests/core/test_config.py`

## Audit Trail

- EXTRACTED: 50 (86%)
- INFERRED: 8 (14%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
