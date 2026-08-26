## 1. Models

- [x] 1.1 Add a `# ── Custo de Aquisição ──` section to `backend/app/models.py`, placed after the Estoque block (after `BaixarEstoqueResponse`, ~line 1076)
- [x] 1.2 Define `TipoCustoAjuste(str, enum.Enum)` with members `frete`, `seguro`, `icms_st`, `ipi`, `despesa_acessoria`, `desconto_comercial`, `devolucao`, `correcao_documento`, `outros`
- [x] 1.3 Define module-level `NEGATIVE_AJUSTE_TIPOS: frozenset[TipoCustoAjuste]` = `{desconto_comercial, devolucao}`, mirroring the `INCOME_CATEGORIES` / `EXPENSE_CATEGORIES` pattern at `models.py:570`
- [x] 1.4 Define `AJUSTE_LABELS: dict[TipoCustoAjuste, str]` with PT-BR display labels for the frontend, mirroring `CATEGORIA_LABELS` at `models.py:~590`
- [x] 1.5 Define `EntradaEstoque(SQLModel, table=True)` with `id`, `fornecedor_id` (FK `fornecedor.id`, `ondelete="SET NULL"`, indexed), `data_entrada: date`, `numero_documento: str | None` (max_length=44), `observacao: str | None` (Text), `transacao_id` (FK `transacao.id`, `ondelete="SET NULL"`), `created_by_id` (FK `user.id`, `ondelete="SET NULL"`), `created_at` / `updated_at` using `default_factory=get_datetime_utc` and `DateTime(timezone=True)`
- [x] 1.6 Define `CustoAjuste(SQLModel, table=True)` with `id`, `entrada_id` (FK `entradaestoque.id`, `ondelete="CASCADE"`, indexed), `tipo: TipoCustoAjuste`, `valor: Decimal = Field(sa_type=Numeric(12, 2))  # type: ignore`, `documento_referencia: str | None` (max_length=100), `observacao: str | None` (Text), `created_at`
- [x] 1.7 Add relationships: `EntradaEstoque.ajustes` (cascade `all, delete-orphan`), `EntradaEstoque.items`, `EntradaEstoque.fornecedor`
- [x] 1.8 Add `entrada_id: uuid.UUID | None` (FK `entradaestoque.id`, `ondelete="SET NULL"`, indexed) and `custo_unitario_nf: Decimal | None = Field(default=None, sa_type=Numeric(12, 4))  # type: ignore` to `ProductItem` (`models.py:920`)
- [x] 1.9 Add schemas `EntradaItemCreate`, `CustoAjusteCreate`, `EntradaEstoqueCreate` (with `itens: list[EntradaItemCreate]` min length 1, `ajustes: list[CustoAjusteCreate] = []`, `criar_transacao: bool = False`), `CustoAjusteRead`, `EntradaItemRead` (includes derived `custo_unitario_real`), `EntradaEstoqueRead`, `EntradaEstoqueListRead`
- [x] 1.10 Add a `field_validator` on `CustoAjusteCreate` rejecting `valor == 0`, requiring `valor < 0` for members of `NEGATIVE_AJUSTE_TIPOS` and `valor > 0` otherwise, and requiring a non-empty `observacao` when `tipo == outros`
- [x] 1.11 Add `custo_medio_ponderado: Decimal | None` and `lotes_sem_custo: int` to `ProductRead`
- [x] 1.12 Confirm no update schema anywhere exposes `custo_unitario_nf`

## 2. Migration

- [x] 2.1 Hand-wrote `backend/app/alembic/versions/d4e5f6a7b8c9_add_entrada_estoque_and_custo_ajuste.py` (autogenerate unavailable — no local Postgres; hand-written revision ids are already a repo convention)
- [x] 2.2 Verify the generated file sets `down_revision = '6134a479de6e'` (current single head)
- [x] 2.3 Verify string columns use `sqlmodel.sql.sqltypes.AutoString`, matching `f3a68091d1fb_add_fornecedor_tables.py`
- [x] 2.4 Verify the `productitem` changes are `op.add_column` only — the migration MUST NOT contain any `UPDATE` against `productitem`, because `get_stock_prediction` (`crud.py:1226`) reads `updated_at` as a consumption signal
- [x] 2.5 Verify `downgrade()` drops both tables and both columns
- [x] 2.6 Ran `uv run alembic upgrade head` — now at `d4e5f6a7b8c9 (head)`; tables verified in Postgres

## 3. CRUD — cost derivation

- [x] 3.1 Import all new models at the **top** of `backend/app/crud.py` — never inline with string annotations (see `docs/pitfalls.md` #3)
- [x] 3.2 Implement `_apportion_ajustes(*, itens, total_ajustes) -> dict[uuid.UUID, Decimal]` — value-share weights, `Decimal.quantize(Decimal("0.01"), ROUND_HALF_UP)` per share, residual assigned to the largest `valor_base` so shares sum exactly to `total_ajustes`
- [x] 3.3 Handle the degenerate case in `_apportion_ajustes`: when total invoice value is zero, fall back to quantity share
- [x] 3.4 Implement `_custo_unitario_real(item, share) -> Decimal`
- [x] 3.5 Implement `get_custo_medio_ponderado(*, session, product_ids) -> dict[uuid.UUID, tuple[Decimal | None, int]]` as a **single** GROUP BY aggregate over `productitem` filtered to `status = em_estoque`, returning average and `lotes_sem_custo` per product

## 4. CRUD — entrada

- [x] 4.1 Implement `create_entrada_estoque(*, session, entrada_in: EntradaEstoqueCreate, created_by_id: uuid.UUID) -> EntradaEstoque` following the flush-then-commit pattern of `create_fornecedor` (~`crud.py:820`): `session.add(header)` → `session.flush()` → add `ProductItem` and `CustoAjuste` children → single `commit()`
- [x] 4.2 Validate every `product_id` exists before flushing; raise `ValueError` on the first miss so the route maps it to 404 and nothing is persisted
- [x] 4.3 When `criar_transacao` is true, build a `TransacaoCreate` with `tipo=despesa`, `categoria=COMPRA_MATERIAL`, `valor` = total invoice value + adjustments, `data_competencia = data_entrada`, `fornecedor_id` from the entrada, and **no** `client_id` (rejected by the validator at `models.py:630`); set `transacao_id` on the header within the same transaction
- [x] 4.4 Implement `_entrada_options()` returning `selectinload` for `fornecedor`, `ajustes`, and `items` → `product`, mirroring `_product_options()` (`crud.py:1003`)
- [x] 4.5 Implement `get_entrada_estoque(*, session, entrada_id)` and `get_entradas_estoque(*, session, fornecedor_id=None, data_inicio=None, data_fim=None)` using `.options(*_entrada_options())`
- [x] 4.6 Implement `add_custo_ajuste(*, session, entrada_id, ajuste_in)` and `delete_custo_ajuste(*, session, entrada_id, ajuste_id)`
- [x] 4.7 Immutability of `custo_unitario_nf` needs no runtime guard — there is no `ProductItemUpdate` schema and no PATCH/PUT route on `/api/v1/product-items`, so the field is unwritable after creation by construction. Covered by a regression test (6.7) instead.

## 5. Routes

- [x] 5.1 Create `backend/app/api/routes/entradas_estoque.py` with `router = APIRouter(prefix="/entradas-estoque", tags=["entradas-estoque"])`, modelled on `products.py`
- [x] 5.2 Define `ViewGuard = Depends(require_permission("view_estoque"))` and `ManageGuard = Depends(require_permission("manage_estoque"))` as module-level constants
- [x] 5.3 Implement `POST ""` (201), `GET ""`, `GET /{entrada_id}`, `POST /{entrada_id}/ajustes` (201), `DELETE /{entrada_id}/ajustes/{ajuste_id}` (204) using `HTTPStatus` enum members, mapping `ValueError` → 404
- [x] 5.4 On `POST ""` with `criar_transacao: true`, additionally require `manage_financeiro` and return 403 when absent, before any record is created
- [x] 5.5 Write a hand-written `_to_entrada_read(entrada) -> EntradaEstoqueRead` mapper that applies `_apportion_ajustes` and populates `custo_unitario_real` per lot
- [x] 5.6 Register the router in `backend/app/api/main.py`
- [x] 5.7 Extend `backend/app/api/routes/products.py` — `GET ""` and `GET /{id}` populate `custo_medio_ponderado` and `lotes_sem_custo` via one `get_custo_medio_ponderado` call for the whole result set

## 6. Backend tests


- [x] 6.1 Test the worked apportionment example: lots (10 × 100,00) and (5 × 200,00) with `frete` 200,00 yield real costs 110,00 and 220,00
- [x] 6.2 Test that apportioned shares sum exactly to the adjustment total across a case with an uneven three-way split (rounding residual)
- [x] 6.3 Test bonificação: a zero-cost lot receives no freight share and the full freight lands on the priced lots
- [x] 6.4 Test the zero-total-value fallback to quantity share
- [x] 6.5 Test sign validation: `desconto_comercial` with positive `valor` → 422; `frete` with negative `valor` → 422; `valor` of 0 → 422
- [x] 6.6 Test `tipo: outros` without `observacao` → 422
- [x] 6.7 Regression test: no request schema in `app.models` exposes `custo_unitario_nf` outside `EntradaItemCreate`; PATCH `/api/v1/product-items/{id}` returns 404 (no such route defined)
- [x] 6.8 Test atomicity: an entrada whose second lot references a missing product creates neither the entrada nor the first `ProductItem`
- [x] 6.9 Test weighted average excludes null-cost lots and reports `lotes_sem_custo`; test the null-not-zero case; test that `reservado` and `utilizado` lots are excluded
- [x] 6.10 Test `criar_transacao: true` creates the `Transacao` with the right total; test the default creates none; test 403 without `manage_financeiro` leaves no records
- [x] 6.11 Test 403 for a `client`-role user on entrada create, entrada read, and adjustment create
- [x] 6.12 Add a query-count test asserting `GET /api/v1/products` issues at most 3 queries regardless of N, in the style of the Phase 4 financeiro scenario
- [x] 6.13 Add a query-count test asserting `GET /api/v1/entradas-estoque` issues at most 4 queries regardless of N
- [x] 6.14 Static check that the migration is additive only — asserts `op.add_column` on `productitem` and no `UPDATE` / `op.execute` in `upgrade()`

## 7. Frontend

- [x] 7.1 Run `bash ./scripts/generate-client.sh`
- [x] 7.2 Create the entrada registration form under `frontend/src/routes/estoque/entradas/` — supplier select, date, document number, dynamic lot lines (product, quantity, unit cost), dynamic adjustment lines (tipo, valor, documento_referencia, observacao), and a `criar_transacao` checkbox
- [x] 7.3 On every money and quantity input use `z.number()` with `onChange={(e) => field.onChange(e.target.valueAsNumber)}` — never `z.coerce.number()` (see `docs/pitfalls.md` #2)
- [x] 7.4 Show a live computed total and per-lot real cost preview in the form so the apportionment is visible before submit
- [x] 7.5 Create the entrada list page with supplier and date-range filters, and the entrada detail page showing lots, real costs, and adjustments with their document references
- [x] 7.6 Add a cost panel to the product detail page showing `custo_medio_ponderado` alongside `unit_price`, rendering a caveat when `lotes_sem_custo > 0`
- [x] 7.7 Add the "Entradas de Estoque" sidebar entry
- [x] 7.8 All user-facing strings in PT-BR; code and comments in English

## 8. Verification

- [x] 8.1 Ran `uv run pytest -n auto tests/` — 425 passed, all 38 new tests green. NOTE: `scripts/test.sh` itself fails with `pytest: command not found` (calls bare `pytest`, not `uv run pytest`) — pre-existing, unrelated to this change
- [x] 8.2 Run `cd frontend && bun run build` — passes (2235 modules, clean)
- [x] 8.3 E2E against the dev stack: entrada with 2 products + frete 200,00 → real costs 110,0000 / 220,0000; Σ(real × qtd) = 2200.00 = produtos + ajustes, reconciles exactly
- [x] 8.4 `tests/crud/test_stock_prediction.py` passes unchanged; prediction endpoint returns identical values before/after an entrada
- [x] 8.5 `GET /estoque/dashboard` intact — correctly reports the 15 units the entrada created; `test_estoque.py` passes unchanged
- [x] 8.6 Updated `docs/domain-model.md` (entrada + custo concepts) and `docs/pitfalls.md` (ProductItem.updated_at, routeTree.gen.ts)
