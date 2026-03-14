## Why

The system currently manages clients and service orders but has no financial tracking whatsoever. The company operates with cash-flow realities that are invisible: fuel is bought, day laborers are paid, equipment breaks down, and service orders generate income — but none of this is recorded anywhere. The finance team has no visibility into where money goes or comes from.

Two sidebar slots (`view_contas_pagar` and `view_contas_receber`) were intentionally wired into the RBAC system in Phase 3, but the pages behind them do not exist yet. This change fills that gap.

The goal is simple financial clarity: track every real monetary movement (income or expense), tag it with a category and optionally a service order, and provide a monthly overview so the company knows whether it is profitable.

## What Changes

- Introduce a **`Transacao`** (transaction) model — the single source of truth for all financial movements. A transaction is either `receita` (income) or `despesa` (expense), has an amount, a date, a category, an optional description, and optional foreign keys to a `Service` and a `Client`.
- Introduce a **`CategoriaTransacao`** enum with all known income and expense categories. Categories are fixed at the code level for MVP — no user-managed taxonomy.
- Add **CRUD functions** and **API routes** for transactions (`/api/v1/transacoes`).
- Add a **Finance Dashboard** page with a monthly income vs. expense summary chart and KPI cards.
- Add a **Transactions list** page (filterable by type, category, and date range) with an **Add Transaction** form.
- Wire the existing `view_contas_pagar` and `view_contas_receber` permission slots to new pages: **Contas a Pagar** (upcoming expenses) and **Contas a Receber** (upcoming income). For MVP these are filtered views of the transaction list, not a separate accounts-payable ledger.
- Add `manage_financeiro` and `view_financeiro` permissions to the permissions registry, and assign `manage_financeiro` + `view_financeiro` as defaults for the `finance` role and `view_financeiro` for the `admin` role.

## Capabilities

### New Capabilities

- `transacoes`: Full CRUD for financial transactions (receitas + despesas) with category, date, optional service linkage, and optional client linkage
- `finance-dashboard`: Monthly income vs. expense summary with KPI cards (total receitas, total despesas, resultado líquido for current month)
- `contas-a-pagar`: Filtered view of upcoming expenses (`data_vencimento` in the future, not yet paid) — wires the existing `view_contas_pagar` sidebar slot
- `contas-a-receber`: Filtered view of upcoming income (`data_vencimento` in the future, not yet received) — wires the existing `view_contas_receber` sidebar slot

### Modified Capabilities

- `rbac-permissions`: Add `manage_financeiro` and `view_financeiro` to `ALL_PERMISSIONS`; assign to `finance` (both) and `admin` (`view_financeiro`) role defaults; update Finance Permissions page matrix columns
- `servicos`: Add a "Lançar transação" action on the service detail page to quickly create a `receita` linked to that service

## Impact

- **Backend:** new `Transacao` SQLModel table; new `CategoriaTransacao` and `TipoTransacao` enums; new CRUD functions in `crud.py`; new `backend/app/api/routes/transacoes.py` router; Alembic migration; updated `ALL_PERMISSIONS` and `ROLE_PERMISSIONS` in `permissions.py`
- **Frontend:** new Finance Dashboard page (`/financeiro`); new Transactions list page (`/financeiro/transacoes`); new Add Transaction form; Contas a Pagar page (`/financeiro/contas-a-pagar`); Contas a Receber page (`/financeiro/contas-a-receber`); regenerated API client; updated sidebar with finance links
- **DB:** new `transacao` table; Alembic migration required
- **Auth:** two new permissions (`manage_financeiro`, `view_financeiro`) added to registry; `finance` role defaults updated
