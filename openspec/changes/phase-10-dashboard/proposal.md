# Proposal: Phase 10 — Operational Dashboard

## Problem
The main dashboard page (`/`) is an empty stub showing only "Hi, {name}". Admin and finance users have no at-a-glance view of operational performance — they must navigate to individual pages to understand business health.

## Solution
Build a **tabbed dashboard hub** on the homepage with an "Operacional" tab showing:
- 4 KPI cards (current week): repairs count, drillings count, drilling meters, weekly profit
- Yearly weekly bar chart comparing all weeks of the current year

### Key decisions (from CEO review):
- **Drilling meters**: Computed from `ServiceItem` with new `ItemType.perfuracao` enum value. `SUM(quantity)` where `item_type='perfuração'` on completed services. No new column on Service model.
- **Week definition**: ISO week (Monday–Sunday UTC)
- **Data scope**: Full year (52 weeks), KPI cards show current week, chart shows all weeks YTD
- **Architecture**: Tabs component on dashboard page. Dashboards are only accessible inside the dashboard page — no sidebar links for individual dashboards.
- **Permissions**: `view_dashboard` (admin + finance)

### Delight features (build now):
- Click-through from KPI cards to filtered `/services` list
- Drilling meters displayed with "m" suffix

### Deferred (see TODOS.md F-09 to F-13):
- F-09: Embed Financeiro dashboard as tab
- F-10: Week-over-week trend arrows
- F-11: PT-BR time-aware greeting
- F-12: Color-coded profit card
- F-13: Empty state illustration

## Files touched
- `backend/app/models.py` — ItemType enum + new schemas
- `backend/app/crud.py` — get_yearly_operational_summary()
- `backend/app/api/routes/dashboard.py` — NEW route file
- `backend/app/api/main.py` — register route
- `backend/app/alembic/versions/` — NEW migration
- `backend/tests/api/routes/test_dashboard.py` — NEW test file
- `frontend/src/routes/_layout/index.tsx` — replace with dashboard hub
- `frontend/src/client/` — regenerated

## Effort
S-M (1 backend endpoint + 1 frontend page replacement)
