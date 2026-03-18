# Tasks: Phase 10 — Operational Dashboard

## 1. Backend — Data model changes

- [ ] 1.1 Add `ItemType.perfuracao = "perfuração"` to the `ItemType` enum in `models.py`
- [ ] 1.2 Add `WeeklyOperationalSummary` schema in `models.py`: `week_number: int`, `week_start: date`, `repairs_count: int`, `drillings_count: int`, `drilling_meters: Decimal`, `profit: Decimal`
- [ ] 1.3 Add `YearlyOperationalDashboard` response schema: `ano: int`, `weeks: list[WeeklyOperationalSummary]`
- [ ] 1.4 Generate Alembic migration: add `perfuração` value to `itemtype` enum + add `index=True` on `Service.type`

## 2. Backend — CRUD

- [ ] 2.1 Add `get_yearly_operational_summary(session, ano) -> list[WeeklyOperationalSummary]` in `crud.py`
  - Query 1: `SELECT EXTRACT(WEEK FROM updated_at), type, COUNT(*) FROM service WHERE status='completed' AND EXTRACT(YEAR FROM updated_at)=ano GROUP BY week, type`
  - Query 2: `SELECT EXTRACT(WEEK FROM s.updated_at), SUM(si.quantity) FROM service_item si JOIN service s ON ... WHERE si.item_type='perfuração' AND s.status='completed' AND EXTRACT(YEAR FROM s.updated_at)=ano GROUP BY week`
  - Query 3: `SELECT EXTRACT(WEEK FROM data_competencia), tipo, SUM(valor) FROM transacao WHERE EXTRACT(YEAR FROM data_competencia)=ano GROUP BY week, tipo`
  - Merge results into list[WeeklyOperationalSummary], one entry per ISO week (1 through current week)
  - Weeks with no data get zeros

## 3. Backend — Routes

- [ ] 3.1 Create `backend/app/api/routes/dashboard.py` with `GET /dashboard/operational?ano=<year>` endpoint
  - Permission: `view_dashboard`
  - Default `ano` to current year
  - Returns `YearlyOperationalDashboard`
- [ ] 3.2 Register route in `backend/app/api/main.py`

## 4. Backend — Tests

- [ ] 4.1 `test_dashboard_operational_returns_empty_when_no_services` — fresh DB returns empty weeks list
- [ ] 4.2 `test_dashboard_operational_counts_completed_services_by_type` — create perfuração + reparo services, complete them, verify counts
- [ ] 4.3 `test_dashboard_operational_sums_drilling_meters` — create service with perfuração items, complete, verify SUM(quantity)
- [ ] 4.4 `test_dashboard_operational_computes_weekly_profit` — create receita + despesa transactions, verify profit = receitas - despesas
- [ ] 4.5 `test_dashboard_operational_ignores_other_years` — services completed in different year not counted
- [ ] 4.6 `test_dashboard_operational_ignores_non_completed_services` — scheduled/executing services not counted
- [ ] 4.7 `test_dashboard_operational_permission_denied` — client role gets 403

## 5. Frontend — OpenAPI client

- [ ] 5.1 Regenerate OpenAPI client after backend changes

## 6. Frontend — Dashboard hub

- [ ] 6.1 Replace `frontend/src/routes/_layout/index.tsx` with tabbed dashboard hub
  - Add permission guard: `view_dashboard` (admin + finance), redirect others to `/`
  - Use Tabs component (Radix) — first tab: "Operacional", future tabs placeholder
  - Page title: "Dashboard - Prata Sys"
- [ ] 6.2 Operacional tab: 4 KPI cards in estoque mini-board style (grid-cols-2 sm:grid-cols-4)
  - Card 1: "Reparos" — `repairs_count` from current week
  - Card 2: "Perfurações" — `drillings_count` from current week
  - Card 3: "Metros Perfurados" — `drilling_meters` with "m" suffix, formatted pt-BR
  - Card 4: "Lucro Semanal" — `profit` formatted as BRL
- [ ] 6.3 KPI cards click-through: link to `/services?type=<type>&status=completed`
- [ ] 6.4 Yearly weekly bar chart below KPI cards (same pattern as financeiro 6-month chart)
  - X-axis: week numbers (S1, S2, ... S52)
  - Bars: repairs (one color) + drillings (another color)
  - Tooltip/title with exact numbers
- [ ] 6.5 Skeleton loading state for cards and chart
- [ ] 6.6 Format drilling meters with "m" suffix: `{value.toLocaleString("pt-BR")} m`
