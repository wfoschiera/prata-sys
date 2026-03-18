## Why

The company purchases and consumes physical materials — tubes, pumps, cables, connections — across every service job. Without inventory tracking, there is no visibility into what is in stock, what has already been allocated to a service, or when critical materials will run out. This creates operational risk: field teams may arrive at a job site without the necessary materials, or finance may pay for items that are already in stock.

## What Changes

- New `ProductType` model: a category-level grouping (tubos | conexoes | bombas | cabos | outros) with a name and unit of measure (un, m, kg, L, etc.).
- New `Product` model: a specific product SKU linked to a `ProductType` and a `Fornecedor`, with a name, unit price, and optional description.
- New `ProductItem` model: individual stock entries for a product, each carrying a `quantity`, a `status` (em_estoque | reservado | utilizado), and an optional `service_id` FK that is set when the item is reserved or used.
- New REST API routes under `/api/v1/product-types`, `/api/v1/products`, and `/api/v1/product-items` with role-based access (read: admin + finance; write: admin only).
- Stock status transitions driven by the service lifecycle: items become `reservado` automatically when a service moves to `scheduled`; items move to `utilizado` via a manual "Baixar do estoque" action or automatically during service completion review.
- Stock depletion prediction endpoint: returns estimated days-to-stockout per product based on average daily consumption and current quantities.
- Alembic migrations for the three new tables.
- Frontend: products list page, add/edit product form, per-product stock history, stock overview dashboard with category cards, depletion prediction indicators, and integration modals in the service lifecycle (scheduling warning, "Baixar do estoque", completion review).

## Capabilities

### New Capabilities

- `estoque.tipos-de-produto`: Manage product type catalog (category + unit of measure).
- `estoque.produtos`: Manage the product catalog linked to product types and fornecedores with unit pricing.
- `estoque.itens`: Track individual stock entries per product with lifecycle status (em_estoque → reservado → utilizado).
- `estoque.predicao`: Compute and surface a depletion prediction (days to stockout) per product based on consumption history.
- `estoque.dashboard`: Aggregated stock overview cards by category.
- `estoque.historico`: Per-product chronological log of stock entry status changes.

### Modified Capabilities

- `servicos`: The service scheduling flow gains a stock reservation check. Moving a service to `scheduled` triggers automatic reservation of associated `ProductItem` entries and warns the user if stock is insufficient. Moving to `executing` enables the "Baixar do estoque" action to mark items as `utilizado`. Completion triggers an automatic review of any remaining `reservado` items.

## Impact

- **Backend:** `backend/app/models.py` (three new table models + enums), `backend/app/crud.py` (new CRUD functions + stock transition helpers), `backend/app/api/routes/product_types.py`, `backend/app/api/routes/products.py`, `backend/app/api/routes/product_items.py` (new routers), `backend/app/api/main.py` (router registration), new Alembic migration.
- **Frontend:** new route files under `frontend/src/routes/estoque/`, updated sidebar, updated service lifecycle modals in `frontend/src/routes/services/`.
- **Dependencies:** assumes Phase 2 (`Service` model), Phase 3 (RBAC `require_role` dependency), and the `Fornecedor` model from Phase 6 are merged.
- **N+1 risk:** product items list queries must eagerly load `product` and `service` relationships via `selectinload()`. Product list must eagerly load `product_type` and `fornecedor`.
