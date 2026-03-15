# TODOS.md — prata-sys technical debt & deferred work

Last updated: 2026-03-15 (all phases 1–9 shipped, PRs #36–#60).

---

## ✅ SHIPPED — Phase 8 (Stock Integration)

- **T-01** — Stock reservation on `scheduled` transition → PR #36
- **T-02** — Stock deduction on `completed` transition → PR #36
- **T-03** — `POST /services/{id}/deduct-stock` implementation → PR #36
- **T-04** — `index=True` on `Service.client_id` and `Service.status` → PR #37
- **T-08** — Guard service deletion by status → PR #38
- **T-10** — Guard service item mutation by status → PR #38
- **T-09** — Stock prediction `created_at` → `updated_at` → PR #41
- **T-18** — Alembic migration for Service + ProductItem indexes → PR #42
- **T-22** — `ProductItem.status` DB index → PR #42
- **T-21** — `SELECT FOR UPDATE` in stock reservation → PR #40
- **T-19** — Product-scoped stock reservation → PR #55
- **T-20** — ServiceItem `product_id` FK → PR #55

## ✅ SHIPPED — Technical debt cleanup

- **T-23** — `assert result is not None` → explicit `RuntimeError` → PR #43
- **T-24** — `HTTPException` removed from CRUD layer → PR #44
- **T-13** — Structured logging on service transitions → PR #45
- **T-25** — Stale docstring on deduct-stock → PR #45
- **T-26** — `DeductionSummary` schema + typed route → PR #45
- **T-14** — Readiness endpoint `GET /readiness/` → PR #47
- **T-16** — Stock prediction unit tests (14 tests) → PR #48
- **T-11** — Login rate limiting (slowapi, 5/min) → PR #49
- **T-05** — `ServiceListRead` / remove status_logs from list → PR #50
- **T-06** — Permission caching in request.state + CPF test isolation → PR #51
- **T-07** — Frontend pagination (services, clients, admin) → PR #54
- **T-12** — Password reset token invalidation → PR #53
- **T-15** — CRUD service transition tests (13 tests) → PR #52
- **T-17** — Estoque product item UI → already implemented in Phase 7

## ✅ SHIPPED — Phase 9 (Orçamento)

- **#56** — Client structured address fields (bairro, city, state, cep)
- **#57** — Orcamento + OrcamentoItem + OrcamentoStatusLog models + migration
- **#58** — CompanySettings singleton + `/settings/empresa` API
- **#59** — Orçamento CRUD (11 endpoints) + permissions + 28 tests
- **#60** — Frontend: list page, detail page, create form, sidebar nav, print CSS

---

## 🔮 FUTURE — Wave D (Orçamento polish)

### F-01 · Orçamento edit form page
**What:** Create `/orcamentos/:id/edit` route to edit an existing orçamento (client, address, items, payment terms). Currently only creation is supported; edits must be done via API.
**Effort:** M
**Priority:** P2

### F-02 · Inline item management on detail page
**What:** Add/edit/remove items directly on the orçamento detail page (currently items can only be managed via API calls, not from the UI).
**Effort:** M
**Priority:** P2

### F-03 · Client address form fields in frontend
**What:** The Client model now has bairro, city, state, cep fields (PR #56) but the frontend client form doesn't expose them yet. Add these fields to the client create/edit form.
**Effort:** S
**Priority:** P2

### F-04 · Company settings admin page
**What:** Add a frontend settings page where admin can configure company letterhead info (name, CNPJ, address, phone, email, logo). The API exists (`PUT /settings/empresa`) but has no UI.
**Effort:** S
**Priority:** P2

### F-05 · Orçamento PDF generation (server-side)
**What:** Generate real PDF files from orçamentos using WeasyPrint or similar. Currently only browser print (`@media print`) is supported.
**Effort:** M
**Priority:** P3

---

## 🔮 FUTURE — Roadmap features

### F-06 · Client portal
**What:** Clients can log in and view their well status, documents, and service history.
**Priority:** P3

### F-07 · Field technician role
**What:** Add `technician` role with mobile-friendly UI for field operations.
**Priority:** P3

### F-08 · Billing from services
**What:** Auto-generate invoices from completed services.
**Priority:** P3
