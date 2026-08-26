# Operational Dashboard Tests

> 22 nodes · cohesion 0.16

## Key Concepts

- **TestClient** (18 connections) — `backend/tests/api/routes/test_dashboard.py`
- **Session** (17 connections) — `backend/tests/api/routes/test_dashboard.py`
- **test_dashboard.py** (15 connections) — `backend/tests/api/routes/test_dashboard.py`
- **_add_drilling_item()** (7 connections) — `backend/tests/api/routes/test_dashboard.py`
- **_create_completed_service()** (7 connections) — `backend/tests/api/routes/test_dashboard.py`
- **test_dashboard_operational_sums_drilling_meters()** (7 connections) — `backend/tests/api/routes/test_dashboard.py`
- **test_dashboard_operational_computes_weekly_profit()** (6 connections) — `backend/tests/api/routes/test_dashboard.py`
- **test_dashboard_operational_counts_completed_perfuracao()** (5 connections) — `backend/tests/api/routes/test_dashboard.py`
- **test_dashboard_operational_counts_completed_reparo()** (5 connections) — `backend/tests/api/routes/test_dashboard.py`
- **test_dashboard_operational_ignores_non_completed_services()** (5 connections) — `backend/tests/api/routes/test_dashboard.py`
- **test_dashboard_operational_permission_denied()** (3 connections) — `backend/tests/api/routes/test_dashboard.py`
- **test_dashboard_operational_returns_valid_structure()** (3 connections) — `backend/tests/api/routes/test_dashboard.py`
- **test_dashboard_operational_unauthenticated()** (3 connections) — `backend/tests/api/routes/test_dashboard.py`
- **Tests for the operational dashboard endpoint.** (1 connections) — `backend/tests/api/routes/test_dashboard.py`
- **Completed reparo service increments repairs_count for its week.** (1 connections) — `backend/tests/api/routes/test_dashboard.py`
- **drilling_meters sums quantity of ItemType.perfuracao items on completed services** (1 connections) — `backend/tests/api/routes/test_dashboard.py`
- **Services not in completed status are excluded from counts.** (1 connections) — `backend/tests/api/routes/test_dashboard.py`
- **profit = receitas - despesas for the week. Check delta from before/after.** (1 connections) — `backend/tests/api/routes/test_dashboard.py`
- **Client role gets 403 Forbidden.** (1 connections) — `backend/tests/api/routes/test_dashboard.py`
- **Unauthenticated request gets 401.** (1 connections) — `backend/tests/api/routes/test_dashboard.py`
- **Endpoint returns YearlyOperationalDashboard with ano + weeks list.** (1 connections) — `backend/tests/api/routes/test_dashboard.py`
- **Completed perfuracao service increments drillings_count for its week.** (1 connections) — `backend/tests/api/routes/test_dashboard.py`

## Relationships

- [[Backend CRUD Core]] (26 shared connections)
- [[Services API Tests]] (5 shared connections)
- [[Transacoes API Tests]] (3 shared connections)
- [[Operational Dashboard Router]] (1 shared connections)
- [[Service Transition Unit Tests]] (1 shared connections)

## Source Files

- `backend/tests/api/routes/test_dashboard.py`

## Audit Trail

- EXTRACTED: 90 (82%)
- INFERRED: 20 (18%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [[index]] to navigate.*
