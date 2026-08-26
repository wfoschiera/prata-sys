# CORS Security Tests

> 8 nodes · cohesion 0.32

## Key Concepts

- **TestClient** (3 connections) — `backend/tests/test_main.py`
- **test_main.py** (3 connections) — `backend/tests/test_main.py`
- **test_cors_preflight_allowed_origin_and_method()** (3 connections) — `backend/tests/test_main.py`
- **test_cors_preflight_disallowed_method_not_reflected()** (3 connections) — `backend/tests/test_main.py`
- **test_cors_preflight_disallowed_origin_not_reflected()** (3 connections) — `backend/tests/test_main.py`
- **A method outside the explicit allow-list is not granted by the preflight.** (1 connections) — `backend/tests/test_main.py`
- **An origin outside the configured allow-list gets no CORS headers.** (1 connections) — `backend/tests/test_main.py`
- **SEC-009: an allowed origin/method preflight is reflected with the     restricted** (1 connections) — `backend/tests/test_main.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `backend/tests/test_main.py`

## Audit Trail

- EXTRACTED: 18 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
