## Context

The application already manages `User`, `Client`, `Service`/`ServiceItem`, RBAC roles, finance flows, and `Fornecedor` records. Phase 7 adds a three-layer inventory model on top of those foundations:

1. **ProductType** — a catalog of product categories and their unit of measure.
2. **Product** — individual SKUs linked to a type and a fornecedor.
3. **ProductItem** — granular stock entries, each tied to a product and optionally to a service.

The service lifecycle (Phase 2) is extended so that scheduling, executing, and completing a service drives automatic status transitions on `ProductItem` records. This keeps inventory state consistent with operational state without requiring separate manual steps for every item.

## Goals / Non-Goals

**Goals:**
- Define `ProductType`, `Product`, and `ProductItem` SQLModel table models with correct FK relationships.
- Enforce a `em_estoque → reservado → utilizado` status lifecycle on `ProductItem`, with the transition driven by service lifecycle events.
- Expose REST APIs for CRUD on all three models, guarded by `require_role` (read: admin + finance; write: admin only).
- Provide a depletion prediction endpoint using a rolling 90-day average daily consumption formula.
- Provide a dashboard aggregation endpoint (per category totals).
- Deliver frontend pages: stock dashboard, products list, per-product stock history, add/edit product form.
- Integrate stock validation warnings into the service scheduling frontend modal.
- Integrate "Baixar do estoque" and completion review into the service execution and completion flows.
- Prevent N+1 queries on all list endpoints by using `selectinload()`.

**Non-Goals:**
- Barcode / QR code scanning for physical stock intake.
- Automatic purchase order generation when stock drops below a threshold.
- Multi-warehouse or multi-location stock tracking.
- Real-time push notifications when stock levels change.
- Audit log with full field-level change history (history shows item entries, not diffs).
- PDF export of stock reports.
- Stock reservation for services not yet in `scheduled` state.

## Decisions

### 1. `ProductItem` as granular entries, not a running balance

Each stock intake and each service allocation creates explicit `ProductItem` rows rather than updating a single balance counter on `Product`. This makes the full history queryable by status (`em_estoque`, `reservado`, `utilizado`) without needing a separate audit table.

*Alternative considered:* a single `stock_quantity` field on `Product` decremented on each use. Rejected because it loses history and makes the `reservado` concept impossible to enforce at the row level.

### 2. Status transitions enforce ordering via service lifecycle hooks

`ProductItem` status changes are driven by service state changes: scheduling → reserve, executing + baixar → utilize, completing → auto-utilize remainders. The `PATCH /services/{id}` handler calls stock transition helpers in `crud.py` during the appropriate transitions rather than having a separate endpoint per stock action (except "Baixar do estoque" which needs an explicit user action mid-execution).

*Alternative considered:* fully decoupled stock management where users manually change item statuses. Rejected because it introduces data inconsistency risk (service completed but items still `reservado`).

### 3. Scheduling does not block on insufficient stock

Moving a service to `scheduled` proceeds regardless of stock availability and returns a `stock_warnings` list in the response when items are short. The frontend shows a warning modal but allows confirmation. This matches the operational reality where the company schedules jobs first and procures materials after if needed.

*Alternative considered:* hard block — reject the scheduling transition if any product is out of stock. Rejected because it would prevent scheduling when procurement is in-flight.

### 4. Depletion prediction uses a rolling 90-day window

Average daily consumption is computed as `SUM(quantity of utilizado items in last 90 days) / 90`. This is a simple, auditable formula. If no utilizado records exist in the window, `avg_daily_consumption = 0` and `days_to_stockout` is returned as `null` (interpreted as "no known risk").

*Alternative considered:* exponential moving average or linear regression. Rejected because the company does not have sufficient historical data at MVP stage to benefit from more sophisticated models, and the simpler formula is easier to explain to operators.

### 5. Prediction endpoint is computed on-demand (no materialized cache)

`GET /api/v1/products/{product_id}/prediction` runs the aggregation query at request time. Given expected stock sizes (hundreds to low thousands of items), this is acceptable without caching.

*Alternative considered:* periodic background job that writes prediction results to a `product_prediction` table. Rejected for MVP — adds operational complexity without measurable benefit at this scale.

### 6. `fornecedor_id` on `Product` is nullable

Not every product may have a known or single supplier at the time of entry. Making it nullable avoids blocking catalog creation while procurement relationships are being established.

*Alternative considered:* require fornecedor at creation. Rejected because it would force dummy records and create data quality issues.

### 7. Separate routers per resource

`product_types.py`, `products.py`, and `product_items.py` are separate router modules, plus a `estoque.py` module for cross-cutting endpoints (dashboard, baixar-estoque). This mirrors the existing pattern (one file per resource) and keeps each router independently testable.

*Alternative considered:* a single `estoque.py` router handling all three resources. Rejected because it would create a large, hard-to-maintain file and break the existing convention.

### 8. `selectinload()` over `joinedload()` for list endpoints

The products list must eagerly load `product_type` and `fornecedor` (many-to-one). The product items list must eagerly load `product` and optionally `service`. `selectinload` is preferred over `joinedload` because it avoids Cartesian product row inflation when future one-to-many relationships are added.

### 9. Frontend routing under `/estoque` prefix

All inventory-related pages live under `/estoque`: dashboard at `/estoque`, product list at `/estoque/produtos`, product detail/history at `/estoque/produtos/{productId}`, and the add/edit form at `/estoque/produtos/new` and `/estoque/produtos/{productId}/edit`. This groups inventory in the sidebar and URL hierarchy.

## Risks / Trade-offs

- **Concurrent reservation race condition** → if two requests simultaneously try to reserve the same `em_estoque` item for different services, both could succeed. Mitigation: use a `SELECT ... FOR UPDATE` lock or optimistic concurrency (check status before update) in the reservation CRUD function. Document as a known limitation at MVP scale; revisit with row-level locking if needed.
- **Large ProductItem tables over time** → every service generates utilizado records indefinitely. Mitigation: acceptable at MVP scale; archiving or partitioning can be added later. The 90-day window already bounds the prediction query.
- **Stock warnings not persisted** → the `stock_warnings` in the scheduling response are computed and returned but not stored. If the user dismisses the modal, the warning is lost. Mitigation: acceptable for MVP; a notification or alert system can be added in a future phase.
- **Backwards compatibility with existing service PATCH** → adding stock side-effects to the existing `PATCH /services/{id}` endpoint is a behavioral change. Mitigation: the change is additive (new fields in the response); existing API clients that ignore unknown fields will not break.

## Migration Plan

1. Run `alembic revision --autogenerate -m "add product_type, product, product_item tables"` after models are defined.
2. Review the generated migration: ensure `product.product_type_id` FK references `producttype.id`, `product.fornecedor_id` FK references `fornecedor.id`, `product_item.product_id` FK references `product.id`, `product_item.service_id` FK references `service.id` with `ondelete="SET NULL"`.
3. Apply: `alembic upgrade head` in development, then staging, then production.
4. Rollback: `alembic downgrade -1` drops `product_item`, `product`, and `producttype` tables in reverse dependency order.
5. No data migration required — tables are new.

## Open Questions

- Should there be a minimum `quantity` threshold configurable per product to trigger reorder alerts? Deferred — the prediction formula covers this indirectly; a threshold field can be added to `Product` in a follow-up phase.
- Should the "Baixar do estoque" action allow partial utilization (e.g., mark only some reservado items as utilized)? Currently the action applies to all reservado items for a service. A per-item selection UI can be added later if operators need finer control.
- Should completed services allow viewing their utilized stock items from the service detail page? This is a useful feature but deferred to avoid scope creep — the per-product history already provides this data from the inventory side.
