## Context

The estoque domain (Phase 7) models stock as three tables: `ProductType` (catalog kind, carries `unit_of_measure` as free text), `Product` (a SKU from a supplier, carries `unit_price` — a **sale** price), and `ProductItem` (a physical lot with `quantity` and `status`). Phase 8 wired `ProductItem.status` to the service lifecycle: `em_estoque → reservado → utilizado`.

Three properties of that design constrain everything here:

1. **There is no movement ledger.** `ProductItem` rows are mutated in place. A stock movement leaves no trace beyond `status` and `updated_at`. History is destructive.
2. **`get_stock_prediction` (`crud.py:1226`) reads `updated_at` as a consumption signal** — it sums `quantity` where `status == utilizado AND updated_at >= now - 90d`. Any write that touches `updated_at` for a non-consumption reason silently corrupts stock predictions.
3. **Lots are never split.** `_deduct_stock_items` (`crud.py:~440`) consumes whole `ProductItem` rows FIFO until the cumulative quantity is satisfied.

On the finance side, `Transacao` is the only table. There is no contas a pagar: no `data_vencimento`, no payment status, only `data_competencia`. `Transacao.fornecedor_id` exists (FK, indexed, `SET NULL`) and `CategoriaTransacao.COMPRA_MATERIAL` exists, but nothing has ever connected a `COMPRA_MATERIAL` transaction to the stock it paid for.

No cost of any kind exists in the system today. Grep for `custo`, `preco_custo`, `preco_medio`, `weighted` returns only false positives.

## Goals / Non-Goals

**Goals:**

- Record the invoice unit price per stock lot, immutably.
- Record every divergence between invoice price and real cost as a typed adjustment with a reference to its supporting document.
- Derive a real unit cost per lot and a weighted average cost per product.
- Make the coverage of that average explicit, so a partially-populated number is never mistaken for a complete one.
- Provide the document header that a future NF-e XML importer can write into without a schema change.

**Non-Goals:**

- **An untyped "valor real pago" field.** Recording a cost figure with no documentary basis is out of scope and is structurally prevented: `CustoAjuste.valor` is only writable alongside a `TipoCustoAjuste`, and `outros` requires a non-empty `observacao`. Every divergence from the invoice price is typed and attributable. This is a design constraint of the feature, not a validation preference.
- **NF-e XML import.** No parsing, no XSD validation, no SEFAZ integration, no supplier-product de-para mapping. `numero_documento` is sized at 44 characters to hold a chave de acesso later, but it is entered by hand in this phase.
- **A stock movement ledger.** Introducing an append-only movement table would require rewriting `_check_stock_for_service`, `_deduct_stock_items`, `_release_stock_items`, `reserve_stock_for_service`, `utilize_reserved_items_for_service`, `get_stock_prediction`, and `get_stock_dashboard` simultaneously. Deferred.
- **COGS on service completion.** Knowing the cost of consumed stock is the natural next step, but it needs the movement ledger above to be meaningful.
- **Contas a pagar.** No due dates, no installments, no payment status. Already deferred by Phase 4 and unchanged here.
- **Retroactive cost.** Existing lots have no cost data and none can be inferred. They backfill to `NULL`.
- **Multi-currency, FX.** Out of scope.

## Decisions

### 1. Adjustments attach to a delivery header, not to a lot

*Why:* Frete, seguro, and ICMS-ST are charged against a whole delivery. Attaching them to a single `ProductItem` would force the user to invent an allocation by hand, and would make the total unverifiable against the carrier's CT-e. A header makes the adjustment total directly comparable to the source document.

*Alternative considered:* Per-lot adjustment rows. Rejected — it pushes apportionment onto the user, and produces no place to record a delivery-level document reference.

*Consequence:* A new table (`EntradaEstoque`) that groups lots. `ProductItem.entrada_id` is nullable, so lots created through the existing `POST /api/v1/product-items` path remain valid and simply have no entrada.

### 2. `custo_unitario_nf` is write-once

*Why:* This is the integrity property the whole feature rests on. If the invoice price can be edited after the fact, the fiscal figure and the managerial figure stop being independently checkable and the audit trail is worthless. Corrections flow through a `correcao_documento` adjustment referencing the carta de correção — which preserves both the original and the correction.

*Enforcement:* No `custo_unitario_nf` field on any update schema, plus a CRUD-level guard raising `ValueError` if a caller attempts to change a non-null value. Mirrors the existing precedent of `TransacaoUpdate` omitting `tipo` (`models.py:660`).

### 3. Real cost is derived on read, not stored

*Why:* A stored `custo_unitario_real` would need recomputation on every adjustment insert and delete, giving two sources of truth that can drift. The inputs (lot cost, adjustment rows) are small and already loaded together.

*Alternative considered:* Denormalized column updated on adjustment write. Rejected — drift risk outweighs the read cost at this scale. Revisit only if entrada detail queries measurably slow down.

*Note:* This does **not** extend to `custo_medio_ponderado`, which aggregates across all lots of a product. That one is computed by a single GROUP BY aggregate (Decision 5), not by loading lots into Python.

### 4. Apportionment by value share, with largest-remainder rounding

Adjustments are distributed across the delivery's lots in proportion to each lot's invoice value:

```
valor_base(item) = custo_unitario_nf * quantity
peso(item)       = valor_base(item) / Σ valor_base(entrada)
custo_real(item) = (valor_base(item) + peso(item) * Σ ajustes) / quantity
```

Worked example — entrada with two lots and R$ 200,00 of frete:

| Lot | qty | custo_unitario_nf | valor_base | peso | share of frete | custo_real |
|---|---|---|---|---|---|---|
| A | 10 | 100,00 | 1.000,00 | 0,5 | 100,00 | **110,00** |
| B | 5 | 200,00 | 1.000,00 | 0,5 | 100,00 | **220,00** |

*Why value share rather than quantity share:* quantity share is meaningless across different units of measure — `ProductType.unit_of_measure` is unconstrained free text, so a delivery can mix "un", "m", and "kg". Value is the only dimension comparable across lots.

*Bonificação falls out correctly:* a lot with `custo_unitario_nf = 0` has `peso = 0`, receives no share of the freight, and enters stock at cost zero — correctly diluting the product's weighted average.

*Rounding:* each share is quantised to 2 decimals; the residual (`Σ ajustes − Σ shares`) is assigned to the lot with the largest `valor_base`. This guarantees `Σ shares == Σ ajustes` exactly, so the apportionment always reconciles to the source documents. Use `Decimal.quantize(Decimal("0.01"), ROUND_HALF_UP)` — never float.

*Degenerate case:* if `Σ valor_base == 0` (every lot is a bonificação) the weights are undefined. Adjustments are then split by quantity share as a fallback, and if that is also zero the entrada is rejected at 422.

### 5. Weighted average excludes unknown-cost lots and reports coverage

`custo_medio_ponderado` is computed over lots where `status = em_estoque AND custo_unitario_nf IS NOT NULL`. Every product response also carries `lotes_sem_custo`: the count of `em_estoque` lots excluded.

*Why:* Every lot existing before this change has no cost. Silently averaging over the subset that does would present a confident number computed from partial data — the worst of the three options. Returning `null` when coverage is incomplete would discard information the user does have. Reporting both the average and its coverage lets the caller decide.

*Why not backfill a guess:* there is no defensible source for a historical cost. `Product.unit_price` is a sale price, not a cost, and using it would manufacture margins of exactly zero.

### 6. Booking the despesa is opt-in

`POST /api/v1/entradas-estoque` accepts `criar_transacao: bool = False`. When true, it creates a `Transacao` (`tipo=despesa`, `categoria=COMPRA_MATERIAL`, `fornecedor_id` copied from the entrada, `valor` = `Σ valor_base + Σ ajustes`, `data_competencia` = `data_entrada`) and stores its id on `EntradaEstoque.transacao_id`.

*Why opt-in:* the expense may already have been entered by hand in the financeiro module before the goods were logged in estoque. Defaulting to automatic creation would produce duplicates in the ledger, which is worse than requiring a click.

*Note:* `TransacaoCreate` rejects `client_id` on a `despesa` (`models.py:630`) — the entrada path must not set it.

### 7. Reuse `view_estoque` / `manage_estoque`

*Why:* cost is stock data, and the `finance` role already holds `view_estoque`. Adding a `view_custos` permission would create a state where a user can see a product but not its cost, for no articulated requirement. If cost visibility later needs to be separable, adding the permission then is a one-line change to `ALL_PERMISSIONS`.

## Risks / Trade-offs

- **Risk**: The migration adds columns to `productitem`; a careless `UPDATE` would bump `updated_at` and corrupt `get_stock_prediction`'s 90-day consumption window. → Mitigation: the migration is `add_column` only, with no `UPDATE` statement; a test asserts `updated_at` is unchanged for pre-existing rows across `alembic upgrade head`.
- **Risk**: `custo_medio_ponderado` on the product **list** endpoint could become an N+1 across products. → Mitigation: one GROUP BY aggregate over `productitem` joined to the product set, merged in Python; covered by a query-count test in the style of the Phase 4 financeiro scenario (`at most 3 queries regardless of N`).
- **Risk**: Rounding drift makes apportioned shares fail to sum to the adjustment total, so the entrada no longer reconciles to the CT-e. → Mitigation: largest-remainder assignment of the residual (Decision 4), asserted directly in tests.
- **Trade-off**: Deriving real cost on read means an entrada detail response does arithmetic per request. Acceptable — a delivery has on the order of tens of lots, and the alternative is a denormalised column that can drift.
- **Trade-off**: `entrada_id` is nullable, so two stock-entry paths coexist (`POST /product-items` without cost, `POST /entradas-estoque` with cost). This is deliberate — it keeps the change additive and avoids touching the service lifecycle — but it means stock can still be created without cost data indefinitely. `lotes_sem_custo` makes that visible rather than hidden.
- **Trade-off**: `numero_documento` is free text in this phase. It will need a uniqueness constraint once the XML importer lands and it starts holding a chave de acesso; adding that constraint later may surface duplicates entered by hand. The precedent to follow is `ix_fornecedor_cnpj_unique` (`f3a68091d1fb_add_fornecedor_tables.py`) — a **partial** unique index with `postgresql_where=sa.text('cnpj IS NOT NULL')`, which is how this repo makes a nullable column unique.

## Migration Plan

1. Add the `# ── Custo de Aquisição ──` section to `models.py` (enum, two table models, schemas) and the two nullable columns on `ProductItem`.
2. Generate the migration: `cd backend && uv run alembic revision --autogenerate -m "add entrada estoque and custo ajuste"`. Verify `down_revision = '6134a479de6e'` and that the `productitem` changes are `add_column` only — autogenerate must not emit any `UPDATE`.
3. Implement CRUD, then routes, then register the router.
4. `bash ./scripts/generate-client.sh`, then build the frontend pages.
5. Existing `ProductItem` rows require no data migration: `entrada_id` and `custo_unitario_nf` are `NULL`, and every consumer treats `NULL` cost as "excluded from the average, counted in `lotes_sem_custo`".
6. No rollback data loss: `downgrade()` drops the two tables and the two columns. Cost data entered after the upgrade would be lost on downgrade, which is acceptable for a feature with no downstream dependency yet.
