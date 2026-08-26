## Why

The system has no purchase cost. `Product.unit_price` is a **sale** price — it is the value copied into `OrcamentoItem.unit_price` and `ServiceItem.unit_price`. `ProductItem`, the physical stock lot, carries only `quantity` and `status`. There is no cost basis, no COGS, no weighted average, and no link between a purchase and the stock it produced.

Two consequences follow. First, margin on every orçamento is computed against a list price that was never reconciled with what the company actually paid, so the reported margin is unverifiable. Second, when a supplier's prices move, nothing in the system notices — the sale price is edited by hand, if at all.

The real acquisition cost of a delivery legitimately differs from the invoice line price, for reasons that are individually documentable: frete is billed on a separate CT-e; seguro and despesas acessórias arrive on the invoice but outside the line price; ICMS-ST and IPI compose cost under Simples Nacional; commercial discounts are negotiated after issuance; bonificação (CFOP 1910) delivers zero-cost units that dilute the average; partial devolução reduces the effective quantity; and the supplier's commercial unit (`uCom` "CX 12") often differs from the stock unit ("UN").

Recording only the invoice price therefore produces a cost that is wrong in a known direction. Recording a corrected cost *without* recording why produces a number nobody can audit. This change records both: the invoice price, immutably, and each divergence from it as a typed adjustment carrying a reference to its supporting document.

## What Changes

- New `EntradaEstoque` model: the document representing one physical delivery from one supplier on one date. Groups the stock lots received together and owns the cost adjustments that apply to the delivery as a whole.
- New `CustoAjuste` model: a typed, signed cost adjustment attached to an `EntradaEstoque`, with a closed `TipoCustoAjuste` enum (frete | seguro | icms_st | ipi | despesa_acessoria | desconto_comercial | devolucao | correcao_documento | outros) and an optional `documento_referencia`.
- `ProductItem` gains `entrada_id` (nullable FK) and `custo_unitario_nf` (nullable Decimal, **write-once**) — the invoice unit price for that lot, never mutated after creation.
- Real unit cost per lot is **derived, not stored**: adjustments are apportioned across the delivery's lots by value share, using largest-remainder rounding so no centavo is lost.
- Weighted average cost per product (`custo_medio_ponderado`) is computed on read over lots in `em_estoque` that have a known cost. Lots with unknown cost are excluded and counted separately in `lotes_sem_custo`, so a partially-populated average is never presented as complete.
- New REST routes under `/api/v1/entradas-estoque`, including nested adjustment create/delete. Read requires `view_estoque`; write requires `manage_estoque`. No new permissions.
- Creating an entrada MAY optionally book the corresponding `Transacao` (`tipo=despesa`, `categoria=COMPRA_MATERIAL`), linking the purchase to the financial ledger for the first time.
- Alembic migration for the two new tables and the two new `ProductItem` columns. Existing lots backfill to `NULL` cost.
- Frontend: entrada registration form (supplier, date, document number, N lot lines, M adjustment lines), entrada list and detail pages, and cost display on the product detail page.

## Capabilities

### New Capabilities

- `custo-aquisicao.entrada`: Register a delivery document that creates stock lots and records the invoice unit cost per lot.
- `custo-aquisicao.ajustes`: Attach typed, document-referenced cost adjustments to a delivery.
- `custo-aquisicao.apuracao`: Derive real unit cost per lot by value-share apportionment of the delivery's adjustments.
- `custo-aquisicao.media-ponderada`: Compute weighted average acquisition cost per product over lots with known cost, reporting coverage.
- `custo-aquisicao.despesa`: Optionally book an entrada as a `despesa` transaction linked to the supplier.

### Modified Capabilities

- `estoque`: `ProductItem` gains `entrada_id` and `custo_unitario_nf`. Product read responses gain `custo_medio_ponderado` and `lotes_sem_custo`. The existing manual stock-entry route (`POST /api/v1/product-items`) is unchanged and continues to create cost-less lots — entrada is an additional, richer path, not a replacement.
- `financeiro`: `Transacao` records may now originate from an entrada de estoque, establishing the first link between a purchase and the inventory it produced.

## Impact

- **Backend:** `backend/app/models.py` (new `# ── Custo de Aquisição ──` section: two table models, one enum, request/response schemas; two new columns on `ProductItem`); `backend/app/crud.py` (composite `create_entrada_estoque` using the flush-then-commit pattern, adjustment CRUD, apportionment helper, weighted-average aggregate, `_entrada_options()` eager-loading helper); `backend/app/api/routes/entradas_estoque.py` (new router); `backend/app/api/routes/products.py` (cost fields on read responses); `backend/app/api/main.py` (router registration).
- **Frontend:** new route files under `frontend/src/routes/estoque/entradas/`; product detail page gains a cost panel; sidebar entry; regenerated API client.
- **DB:** new `entradaestoque` and `custoajuste` tables; two nullable columns added to `productitem`; Alembic migration with `down_revision = '6134a479de6e'`.
- **Auth:** no new permissions — reuses `view_estoque` / `manage_estoque` from `backend/app/core/permissions.py`.
- **N+1 risk:** entrada list and detail must eagerly load `fornecedor`, `ajustes`, and `items` (with `product`) via `selectinload()`. The weighted-average computation MUST be a single GROUP BY aggregate, never a per-product loop.
- **Regression risk:** `get_stock_prediction` (`crud.py:1226`) infers consumption from `ProductItem.updated_at`. The migration MUST NOT touch `updated_at` on existing rows.
