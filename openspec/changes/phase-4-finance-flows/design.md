## Context

The system tracks clients and service orders but has no financial layer. The company buys fuel, pays day laborers, orders materials, and collects payment for drilled wells — all of this currently happens off-system. The finance role exists and has sidebar slots reserved (`view_contas_pagar`, `view_contas_receber`) but no pages behind them.

This design introduces a single `Transacao` table as the backbone of financial tracking. The design intentionally avoids double-entry accounting (no journal, no debit/credit ledger). The goal is a simple, opinionated cash-flow record: what happened, how much, which category, and optionally which service or client it relates to.

## Goals / Non-Goals

**Goals:**
- Persist every financial movement as a `Transacao` with `tipo`, `categoria`, `valor`, and `data_competencia`
- Enforce category/tipo compatibility at the API layer (not just the UI)
- Provide a `/resumo` endpoint that aggregates monthly totals for the dashboard chart
- Build four frontend pages: Finance Dashboard, Transactions list, Contas a Pagar (filtered expenses), Contas a Receber (filtered income)
- Wire `view_contas_pagar` and `view_contas_receber` sidebar slots to real pages
- Add `manage_financeiro` and `view_financeiro` to the permission registry

**Non-Goals:**
- Double-entry accounting (no journal entries, no accounts chart)
- Installment payments / parcelamento (no MVP requirement)
- Multi-currency (BRL only)
- Supplier (fornecedor) linkage (planned for a future phase when `Fornecedor` model exists)
- Accounts-payable workflow with payment due dates and status (`pendente` / `pago`) — deferred to a future "Contas a Pagar/Receber proper" phase
- Budget vs. actual tracking
- PDF/CSV export (deferred)

## Decisions

### 1. Single `Transacao` table — no split receitas/despesas tables

**Decision:** One table with a `tipo` discriminator column, not separate `Receita` and `Despesa` tables.

*Why:* The query patterns (monthly summaries, combined list views) always need both sides together. A single table allows a single `SELECT SUM(valor) GROUP BY tipo` for the resumo, and a single list query with an optional `?tipo` filter. Separate tables would require `UNION ALL` for every dashboard query and duplicate most schema fields.

*Alternative considered:* Separate tables (`receita`, `despesa`) with a shared base or view. Rejected — too much duplication for MVP, harder to filter and aggregate.

### 2. Category/tipo compatibility enforced via Pydantic `model_validator`, not DB constraints

**Decision:** The set of valid income categories and valid expense categories is defined in `models.py` as two Python `frozenset` constants. A Pydantic `model_validator(mode="after")` on `TransacaoCreate` and `TransacaoUpdate` checks compatibility and raises `ValueError` if violated (FastAPI converts this to HTTP 422).

```python
INCOME_CATEGORIES = frozenset({
    CategoriaTransacao.SERVICO,
    CategoriaTransacao.VENDA_EQUIPAMENTO,
    CategoriaTransacao.RENDIMENTO,
    CategoriaTransacao.CAPITAL_FIXO,
})

EXPENSE_CATEGORIES = frozenset({
    CategoriaTransacao.COMBUSTIVEL,
    CategoriaTransacao.MANUTENCAO_EQUIPAMENTO,
    CategoriaTransacao.MANUTENCAO_VEICULO,
    CategoriaTransacao.MANUTENCAO_ESCRITORIO,
    CategoriaTransacao.COMPRA_MATERIAL,
    CategoriaTransacao.MO_CLT,
    CategoriaTransacao.MO_DIARISTA,
    CategoriaTransacao.ADMIN,
})
```

*Why not a DB constraint:* Postgres doesn't support cross-column enum compatibility checks cleanly without a custom check constraint that mirrors the enum list in SQL — this creates a maintenance burden every time a category is added. The Pydantic layer is the right place for this business rule.

*Alternative considered:* Two separate enum types (`CategoriaReceita`, `CategoriaDespesa`) and two separate columns. Rejected — complicates querying and the single-category filter on the list endpoint.

### 3. `tipo` is immutable after creation

**Decision:** The PATCH endpoint schema (`TransacaoUpdate`) omits `tipo` entirely. Any attempt to include `tipo` in a PATCH body is silently ignored (Pydantic strips unknown fields by default with `model_config = ConfigDict(extra="ignore")`).

*Why:* Changing `tipo` from `receita` to `despesa` would invalidate the `client_id` link and potentially the `categoria` — making a safe in-place mutation impossible without complex re-validation. The correct action is to delete and recreate.

### 4. Foreign keys use SET NULL on delete — no cascade

**Decision:** `service_id` and `client_id` on `Transacao` use `ondelete="SET NULL"` (nullable FKs). Deleting a service or client does not delete associated transactions.

*Why:* Financial records have regulatory and audit significance. If a service is deleted (e.g., was created in error), the payment already made against it is still a historical fact. Nullifying the FK preserves the transaction with its `valor` and `categoria` intact, while removing the now-invalid reference.

*Alternative considered:* `ondelete="CASCADE"`. Rejected — deleting a client should never silently erase financial records.

### 5. `/resumo` endpoint returns a single-month aggregate — frontend fetches multiple months for the chart

**Decision:** `GET /api/v1/transacoes/resumo?ano=2025&mes=1` returns one `ResumoMensal` object. The frontend dashboard fetches 6 concurrent requests (one per month) using `Promise.all` via TanStack Query to populate the bar chart.

*Why:* A single multi-month aggregate endpoint would require a more complex query surface (e.g., `data_inicio` / `data_fim` with group-by month). The frontend can parallelize 6 cheap requests. Each request hits a simple aggregation with two indexed filters (`data_competencia` date range + implicit all rows). With an index on `data_competencia` this is fast even for thousands of rows.

*Alternative considered:* A single `/resumo/range?meses=6` endpoint returning an array. Reasonable, but adds API complexity for a pattern that's trivially parallelized client-side. Can be added later if latency becomes an issue.

### 6. Contas a Pagar / Contas a Receber are filtered views for MVP

**Decision:** `/financeiro/contas-a-pagar` renders `GET /api/v1/transacoes?tipo=despesa`; `/financeiro/contas-a-receber` renders `GET /api/v1/transacoes?tipo=receita`. They are not separate data models.

*Why:* The user requirement is "give clarity on where money goes" — a simple filtered list achieves this immediately. A proper accounts-payable workflow (due dates, payment status, payment matching) is a separate future change. Building it now would require schema fields (`data_vencimento`, `status_pagamento`, `data_pagamento`) and workflow logic that are out of scope for this MVP phase.

*Trade-off:* "Contas a pagar" literally means "bills to pay" (future obligations). For now the page shows recorded expenses, not future obligations. The page label in PT-BR will be "Despesas" to avoid confusion until the proper workflow is built.

### 7. `valor` stored as `Numeric(12, 2)` — not `float`

**Decision:** The `valor` column uses `sa.Numeric(12, 2)` (DECIMAL in Postgres). Python-side it is annotated as `Decimal` from the `decimal` module.

*Why:* Floating-point arithmetic introduces rounding errors in financial calculations. `SUM(valor)` over many rows must be exact. `Numeric` in Postgres is exact arbitrary-precision. This is standard practice for any monetary column.

*Note:* Pydantic serializes `Decimal` to a JSON number (no quotes). The frontend receives a number and formats it with `Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })`.

### 8. New permissions: `manage_financeiro` and `view_financeiro`

**Decision:** Add two permissions rather than reusing the existing `view_contas_pagar` / `view_contas_receber` permissions as gatekeepers for the main finance routes.

*Why:* `view_contas_pagar` and `view_contas_receber` are narrow, page-level permissions that already exist and are already assignable. They should remain as-is. The new `view_financeiro` permission gates access to the general transaction list and dashboard — a broader capability. The `manage_financeiro` permission gates write operations (create, update, delete transactions). This separation allows an admin to give a user read-only access to all finance data without granting write access.

Role defaults:

| Role | New defaults |
|---|---|
| `finance` | `manage_financeiro`, `view_financeiro` (plus existing `view_contas_pagar`, `view_contas_receber`) |
| `admin` | `view_financeiro` |
| `client` | *(none)* |

## Risks / Trade-offs

- **No due-date / payment-status workflow:** The "Contas a Pagar" page does not show future obligations. Users who expect an accounts-payable ledger with pending/paid status will be disappointed. Mitigation: set clear expectations in the UI ("Histórico de Despesas") and plan the proper workflow as Phase 4b.
- **No supplier linkage:** Day laborer names and material suppliers are captured only in the free-text `descricao` field. This limits reporting by vendor. Mitigation: when the `Fornecedor` model is built, add an optional `fornecedor_id` FK to `Transacao` via a new migration.
- **Single-month `/resumo` means 6 API calls for the chart:** Under normal conditions these are fast (indexed query, small data). Under very slow connections the dashboard chart may stutter. Mitigation: TanStack Query caches previous months; only the current month is live.
- **No pagination on `/resumo`:** The resumo endpoint computes aggregates server-side; it does not paginate. For companies with thousands of transactions per month this is still a single fast aggregation query. The list endpoint (`/transacoes`) DOES paginate via `?skip` and `?limit`.
- **`tipo` immutability adds friction:** Users who create a transaction with the wrong `tipo` must delete and recreate. Mitigation: the Add Transaction form makes `tipo` the first and most visually prominent field, reducing accidental mistakes.

## Migration Plan

1. Add `TipoTransacao` and `CategoriaTransacao` enums and the `Transacao` SQLModel to `backend/app/models.py`
2. Run `alembic revision --autogenerate -m "add transacao table"` and review the migration
3. Run `alembic upgrade head` in dev
4. Add `manage_financeiro` and `view_financeiro` to `ALL_PERMISSIONS` in `permissions.py`
5. Update `ROLE_PERMISSIONS` in `permissions.py` for `finance` and `admin` roles
6. Add CRUD functions for `Transacao` to `crud.py`
7. Create `backend/app/api/routes/transacoes.py` and register in `main.py`
8. Write backend tests for CRUD, API routes, and permission guards
9. Run `bash ./scripts/generate-client.sh` to regenerate the frontend API client
10. Build frontend Finance Dashboard page (`/financeiro`)
11. Build frontend Transactions list page with filters (`/financeiro/transacoes`)
12. Build Add Transaction form (modal or page)
13. Build Contas a Pagar page (`/financeiro/contas-a-pagar`)
14. Build Contas a Receber page (`/financeiro/contas-a-receber`)
15. Update sidebar to render finance links conditionally based on permissions
16. Run `bun run lint && bun run build && bun run test` in `frontend/`

## Open Questions

- Should `MO_DIARISTA` transactions be required to link to a `service_id`? **Proposed: recommended but not enforced** — a day laborer may be paid for general site prep not tied to a specific service order. Enforce via UI hint, not API constraint.
- Should we add a `nome_contraparte` (free-text name of the other party — e.g., day laborer name, supplier name) to `Transacao` now, before the `Fornecedor` model exists? **Proposed: yes** — a nullable `varchar(200)` field adds low cost and immediately lets finance users record who was paid without needing a full supplier model. Add in this phase.
- Should the Permissions page matrix include the new `manage_financeiro` and `view_financeiro` columns automatically? **Proposed: yes** — since the Permissions page reads `ALL_PERMISSIONS` dynamically, adding the new permissions to `ALL_PERMISSIONS` is sufficient. No frontend code change needed for the matrix columns.
