## 1. Database Models

- [x] 1.1 Add `ProductCategory` string enum (`tubos`, `conexoes`, `bombas`, `cabos`, `outros`) to `backend/app/models.py`
- [x] 1.2 Add `ProductItemStatus` string enum (`em_estoque`, `reservado`, `utilizado`) to `backend/app/models.py`
- [x] 1.3 Define `ProductType` SQLModel table with fields: `id` (UUID PK), `category` (ProductCategory, not null), `name` (String, not null), `unit_of_measure` (String, not null), `created_at`, `updated_at`
- [x] 1.4 Add a unique constraint on `(category, name)` in the `ProductType` model
- [x] 1.5 Define `Product` SQLModel table with fields: `id` (UUID PK), `product_type_id` (FK → `producttype.id`, not null), `name` (String, not null), `fornecedor_id` (FK → `fornecedor.id`, nullable), `unit_price` (Decimal(10, 2), >= 0, not null), `description` (optional Text), `created_at`, `updated_at`
- [x] 1.6 Define `ProductItem` SQLModel table with fields: `id` (UUID PK), `product_id` (FK → `product.id`, not null), `quantity` (Decimal(12, 4), > 0, not null), `status` (ProductItemStatus, default `em_estoque`, not null), `service_id` (FK → `service.id`, nullable, `ondelete="SET NULL"`), `created_at`, `updated_at`
- [x] 1.7 Add `products` relationship on `ProductType` (one-to-many to `Product`)
- [x] 1.8 Add `product_type` relationship on `Product` (many-to-one to `ProductType`)
- [x] 1.9 Add `fornecedor` relationship on `Product` (many-to-one to `Fornecedor`, optional)
- [x] 1.10 Add `items` relationship on `Product` (one-to-many to `ProductItem`)
- [x] 1.11 Add `product` relationship on `ProductItem` (many-to-one to `Product`)
- [x] 1.12 Add `service` relationship on `ProductItem` (many-to-one to `Service`, optional)
- [x] 1.13 Add `product_items` back-reference on `Service` (one-to-many to `ProductItem`) so stock queries can be driven from the service side

## 2. Alembic Migration

- [x] 2.1 Run `alembic revision --autogenerate -m "add product_type, product, product_item tables"` and review the generated file
- [x] 2.2 Verify `product.product_type_id` FK references `producttype.id` with `ondelete="RESTRICT"` (blocks deletion when products exist)
- [x] 2.3 Verify `product.fornecedor_id` FK references `fornecedor.id` with `ondelete="SET NULL"` (nullifies reference if fornecedor is deleted)
- [x] 2.4 Verify `product_item.product_id` FK references `product.id` with `ondelete="CASCADE"` (deletes items when product is deleted)
- [x] 2.5 Verify `product_item.service_id` FK references `service.id` with `ondelete="SET NULL"` (nullifies reference if service is deleted)
- [x] 2.6 Confirm the unique constraint on `(category, name)` in `producttype` is present in the migration
- [x] 2.7 Run `alembic upgrade head` in the development environment and verify no errors

## 3. Backend Schemas (Pydantic / SQLModel)

- [x] 3.1 Add `ProductTypeCreate` schema: `category` (ProductCategory), `name` (str), `unit_of_measure` (str)
- [x] 3.2 Add `ProductTypeRead` schema: includes `id`, `category`, `name`, `unit_of_measure`, `created_at`
- [x] 3.3 Add `ProductTypeUpdate` schema: all fields optional
- [x] 3.4 Add `ProductCreate` schema: `product_type_id` (UUID), `name` (str), `fornecedor_id` (UUID | None), `unit_price` (Decimal >= 0), `description` (str | None); validate `unit_price >= 0`
- [x] 3.5 Add `ProductRead` schema: includes `id`, `product_type_id`, `product_type` (ProductTypeRead), `name`, `fornecedor_id`, `fornecedor` (FornecedorRead | None), `unit_price`, `description`, `created_at`
- [x] 3.6 Add `ProductUpdate` schema: all fields optional
- [x] 3.7 Add `ProductItemCreate` schema: `product_id` (UUID), `quantity` (Decimal > 0); validate `quantity > 0`; status and service_id are NOT user-settable on creation
- [x] 3.8 Add `ProductItemRead` schema: includes `id`, `product_id`, `quantity`, `status`, `service_id`, `created_at`
- [x] 3.9 Add `StockPredictionRead` schema: `product_id` (UUID), `days_to_stockout` (int | None), `level` (Literal["green", "yellow", "red"]), `em_estoque_qty` (Decimal), `reservado_qty` (Decimal), `avg_daily_consumption` (Decimal | None)
- [x] 3.10 Add `CategoryDashboardItem` schema: `category` (ProductCategory), `em_estoque_total` (Decimal), `reservado_total` (Decimal), `utilizado_total` (Decimal)
- [x] 3.11 Add `StockWarning` schema: `product_id` (UUID), `product_name` (str), `required_qty` (Decimal), `available_qty` (Decimal), `shortfall_qty` (Decimal)
- [x] 3.12 Add `ServiceUpdateWithStockWarnings` response schema: extends the existing `ServiceRead` with an optional `stock_warnings` (list[StockWarning]) field for use by the scheduling and completion endpoints
- [x] 3.13 Add `BaixarEstoqueResponse` schema: `service_id` (UUID), `items_updated` (int)

## 4. Backend CRUD — ProductType

- [x] 4.1 Add `create_product_type(session, pt_in: ProductTypeCreate) -> ProductType` in `backend/app/crud.py`; raise `ValueError` if `(category, name)` already exists
- [x] 4.2 Add `get_product_type(session, product_type_id: UUID) -> ProductType | None`
- [x] 4.3 Add `get_product_types(session) -> list[ProductType]`; no eager loading needed (no relationships to load by default)
- [x] 4.4 Add `update_product_type(session, pt: ProductType, pt_in: ProductTypeUpdate) -> ProductType`
- [x] 4.5 Add `delete_product_type(session, product_type_id: UUID) -> None`; raise `ValueError` if any `Product` references this type (enforced by FK `RESTRICT`, but catch IntegrityError and re-raise as ValueError for clean HTTP mapping)

## 5. Backend CRUD — Product

- [x] 5.1 Add `create_product(session, product_in: ProductCreate) -> Product`; validate that `product_type_id` exists (404 if not); validate that `fornecedor_id` exists if provided (404 if not)
- [x] 5.2 Add `get_product(session, product_id: UUID) -> Product | None` with `selectinload(Product.product_type)` and `selectinload(Product.fornecedor)` to prevent N+1
- [x] 5.3 Add `get_products(session) -> list[Product]` with `selectinload(Product.product_type)` and `selectinload(Product.fornecedor)` — N+1 guard is critical here
- [x] 5.4 Add `update_product(session, product: Product, product_in: ProductUpdate) -> Product`
- [x] 5.5 Add `delete_product(session, product_id: UUID) -> None`; raise `ValueError` if the product has `ProductItem` records (FK `RESTRICT` behavior); cascade handled by DB if no items

## 6. Backend CRUD — ProductItem

- [x] 6.1 Add `create_product_item(session, item_in: ProductItemCreate) -> ProductItem`; validate that `product_id` exists; set status to `em_estoque` and `service_id` to `None`
- [x] 6.2 Add `get_product_items_by_product(session, product_id: UUID) -> list[ProductItem]` ordered by `created_at` descending; with `selectinload(ProductItem.service)` for optional service reference
- [x] 6.3 Add `get_product_items_by_service(session, service_id: UUID, status: ProductItemStatus | None = None) -> list[ProductItem]` with optional status filter
- [x] 6.4 Add `reserve_stock_for_service(session, service_id: UUID, product_quantities: list[tuple[UUID, Decimal]]) -> list[StockWarning]`; for each (product_id, needed_qty), select `em_estoque` items for that product up to needed_qty, update their status to `reservado` and set `service_id`; return warnings for any shortfall; use `SELECT ... WITH FOR UPDATE` or equivalent to prevent concurrent over-reservation
- [x] 6.5 Add `utilize_reserved_items_for_service(session, service_id: UUID) -> int`; transition all `reservado` items with matching `service_id` to `utilizado`; return count of updated items
- [x] 6.6 Add `validate_product_item_transition(current_status: ProductItemStatus, new_status: ProductItemStatus) -> None`; raise `ValueError` with a descriptive message if the transition is not in the allowed set: `{(em_estoque, reservado), (reservado, utilizado)}`

## 7. Backend CRUD — Stock Prediction & Dashboard

- [x] 7.1 Add `get_stock_prediction(session, product_id: UUID) -> StockPredictionRead`; query `SUM(quantity)` of `em_estoque` items, `SUM(quantity)` of `reservado` items, and `SUM(quantity)` of `utilizado` items created in the last 90 days for that product; compute `avg_daily_consumption = utilizado_90d / 90`; compute `days_to_stockout` per the spec formula; assign `level` based on thresholds
- [x] 7.2 Add `get_stock_dashboard(session) -> list[CategoryDashboardItem]`; use a GROUP BY query on `producttype.category` and `product_item.status` to aggregate totals; return all five categories even if empty (COALESCE to 0)

## 8. Backend API Routes — ProductType

- [x] 8.1 Create `backend/app/api/routes/product_types.py` with an `APIRouter` prefixed `/product-types`
- [x] 8.2 Implement `POST /product-types` → creates product type; requires `admin` via `require_role`; returns 201; returns 409 on duplicate (category, name) combination
- [x] 8.3 Implement `GET /product-types` → returns list; requires `admin` or `finance`; returns 200
- [x] 8.4 Implement `GET /product-types/{product_type_id}` → returns detail; returns 404 if missing
- [x] 8.5 Implement `PATCH /product-types/{product_type_id}` → updates product type; requires `admin`; returns 200
- [x] 8.6 Implement `DELETE /product-types/{product_type_id}` → deletes type; requires `admin`; returns 204; returns 409 if products reference this type

## 9. Backend API Routes — Product

- [x] 9.1 Create `backend/app/api/routes/products.py` with an `APIRouter` prefixed `/products`
- [x] 9.2 Implement `POST /products` → creates product; requires `admin`; returns 201; returns 404 if `product_type_id` or `fornecedor_id` not found
- [x] 9.3 Implement `GET /products` → returns list using `get_products` (with selectinload); requires `admin` or `finance`; supports optional query params `?category=` and `?fornecedor_id=` for filtering
- [x] 9.4 Implement `GET /products/{product_id}` → returns detail using `get_product`; returns 404 if missing
- [x] 9.5 Implement `PATCH /products/{product_id}` → updates product; requires `admin`; returns 200
- [x] 9.6 Implement `DELETE /products/{product_id}` → deletes product; requires `admin`; returns 204; returns 409 if product has stock items
- [x] 9.7 Implement `GET /products/{product_id}/items` → returns per-product stock history using `get_product_items_by_product`; requires `admin` or `finance`; returns 404 if product not found
- [x] 9.8 Implement `GET /products/{product_id}/prediction` → returns depletion prediction using `get_stock_prediction`; requires `admin` or `finance`; returns 404 if product not found

## 10. Backend API Routes — ProductItem

- [x] 10.1 Create `backend/app/api/routes/product_items.py` with an `APIRouter` prefixed `/product-items`
- [x] 10.2 Implement `POST /product-items` → creates a new stock entry (status forced to `em_estoque`); requires `admin`; returns 201; returns 404 if `product_id` not found
- [x] 10.3 Implement `GET /product-items` → returns list of all product items; requires `admin` or `finance`; supports optional `?product_id=`, `?status=`, `?service_id=` query params for filtering

## 11. Backend API Routes — Estoque Cross-Cutting

- [x] 11.1 Create `backend/app/api/routes/estoque.py` with an `APIRouter` prefixed `/estoque`
- [x] 11.2 Implement `GET /estoque/dashboard` → returns aggregated category dashboard using `get_stock_dashboard`; requires `admin` or `finance`; returns 200
- [x] 11.3 Implement `POST /services/{service_id}/baixar-estoque` in `backend/app/api/routes/services.py` (to keep service-scoped actions in the services router) → calls `utilize_reserved_items_for_service`; requires `admin`; returns 422 if service not in `executing` status; returns 200 with `BaixarEstoqueResponse`

## 12. Backend Service Lifecycle Integration

- [x] 12.1 In `crud.py`'s `update_service` function, after a successful transition to `scheduled`, call `reserve_stock_for_service` and attach the returned `stock_warnings` to the response object (or return as a tuple)
- [x] 12.2 In `crud.py`'s `update_service` function, after a successful transition to `completed`, call `utilize_reserved_items_for_service` and include the count of auto-utilized items in the return value
- [x] 12.3 Update `PATCH /services/{service_id}` route handler to return `ServiceUpdateWithStockWarnings` (which extends `ServiceRead`) so the `stock_warnings` field is included in the response when scheduling
- [x] 12.4 Ensure the `PATCH /services/{service_id}` handler does not break existing callers — `stock_warnings` defaults to `[]` for transitions other than `scheduled`

## 13. Backend Router Registration

- [x] 13.1 Register `product_types` router in `backend/app/api/main.py`
- [x] 13.2 Register `products` router in `backend/app/api/main.py`
- [x] 13.3 Register `product_items` router in `backend/app/api/main.py`
- [x] 13.4 Register `estoque` router in `backend/app/api/main.py`

## 14. Backend Tests

- [x] 14.1 Add tests for `ProductType` CRUD: create, read, update, delete, duplicate name conflict, delete-with-products conflict
- [x] 14.2 Add tests for `Product` CRUD: create, read, update, delete, invalid product_type_id, invalid fornecedor_id, negative unit_price
- [x] 14.3 Add tests for `ProductItem` creation: valid creation defaults to `em_estoque`, invalid quantity
- [x] 14.4 Add tests for `validate_product_item_transition`: all allowed and disallowed transitions
- [x] 14.5 Add tests for `reserve_stock_for_service`: sufficient stock reserves items and returns no warnings; insufficient stock returns warnings and partially reserves what is available
- [x] 14.6 Add tests for `utilize_reserved_items_for_service`: transitions reservado items to utilizado and returns correct count
- [x] 14.7 Add tests for `get_stock_prediction`: product with history returns correct days_to_stockout and level; product with no history returns null days_to_stockout and level green; depleted net stock returns level red
- [x] 14.8 Add tests for `get_stock_dashboard`: returns all categories with correct aggregated totals; empty stock returns zero counts
- [x] 14.9 Add API integration tests for `POST /product-types` (201, 403 for finance, 409 for duplicate)
- [x] 14.10 Add API integration tests for `DELETE /product-types/{id}` (204, 409 when products exist)
- [x] 14.11 Add API integration tests for `POST /products` (201, 403 for finance, 404 for bad product_type_id)
- [x] 14.12 Add API integration tests for `POST /product-items` (201, 403 for finance, 404 for bad product_id, 422 for zero quantity)
- [x] 14.13 Add API integration tests for `GET /products/{id}/prediction` (200 with valid product, 404 for missing)
- [x] 14.14 Add API integration tests for `GET /estoque/dashboard` (200 for admin and finance)
- [x] 14.15 Add API integration tests for `POST /services/{id}/baixar-estoque` (200 on executing service, 422 on non-executing service)
- [x] 14.16 Add API integration tests for `PATCH /services/{id}` scheduling transition: verify stock_warnings present when stock is short, verify items reserved when stock is sufficient

## 15. Frontend API Client Regeneration

- [x] 15.1 Regenerate the typed API client from the updated OpenAPI schema (run `bash ./scripts/generate-client.sh`) so that all new estoque endpoints and types are available in the frontend

## 16. Frontend Stock Dashboard Page

- [x] 16.1 Create route file `frontend/src/routes/_layout/estoque/index.tsx` as the stock overview dashboard
- [x] 16.2 Implement a `useQuery` call to `GET /api/v1/estoque/dashboard`
- [x] 16.3 Render one shadcn/ui Card per category (tubos, conexoes, bombas, cabos, outros) displaying `em_estoque_total`, `reservado_total`, and `utilizado_total`
- [x] 16.4 Add a "Ver Produtos" link/button on each card that navigates to `/estoque/produtos?category={category}`
- [x] 16.5 Implement loading and error states for the dashboard query

## 17. Frontend Products List Page

- [x] 17.1 Create route file `frontend/src/routes/_layout/estoque/produtos/index.tsx`
- [x] 17.2 Implement a `useQuery` call to `GET /api/v1/products` with filter params derived from URL search params (`category`, `fornecedor_id`)
- [x] 17.3 Render a table with columns: Name, Category, Fornecedor, Unit Price, Em Estoque (total), Prediction (badge)
- [x] 17.4 Implement filter controls: category dropdown (from ProductCategory enum), fornecedor selector (populated from `/api/v1/fornecedores`)
- [x] 17.5 Implement per-row depletion prediction badge: call `GET /api/v1/products/{id}/prediction` (or batch load) and display a color-coded badge (green/yellow/red) with the `days_to_stockout` value or "—" when null
- [x] 17.6 Add an "Adicionar Produto" button (visible to admin only) that navigates to `/estoque/produtos/new`
- [x] 17.7 Implement empty-state message when no products exist
- [x] 17.8 Make each row clickable, navigating to `/estoque/produtos/{productId}`

## 18. Frontend Add/Edit Product Form

- [x] 18.1 Create route file `frontend/src/routes/_layout/estoque/produtos/new.tsx` for the add product form
- [x] 18.2 Create route file `frontend/src/routes/_layout/estoque/produtos/$productId/edit.tsx` for the edit product form
- [x] 18.3 Implement a shared `ProductForm` component in `frontend/src/components/estoque/ProductForm.tsx` used by both new and edit routes
- [x] 18.4 Implement product type selector (dropdown from `GET /api/v1/product-types`)
- [x] 18.5 Implement fornecedor selector (dropdown from `/api/v1/fornecedores`, optional)
- [x] 18.6 Implement name text input, unit price number input (use `z.number()` + `onChange={(e) => field.onChange(e.target.valueAsNumber)}` per CLAUDE.md), and optional description textarea
- [x] 18.7 Implement an "Estoque Inicial" number input (optional) that, on submission, calls `POST /api/v1/product-items` to create an initial stock entry after the product is created
- [x] 18.8 Validate that `unit_price >= 0` client-side before submission using a Zod schema with `error:` (not `required_error:`)
- [x] 18.9 On successful creation, redirect to `/estoque/produtos/{productId}`
- [x] 18.10 On successful edit, redirect to `/estoque/produtos/{productId}` with a success toast
- [x] 18.11 Display inline validation errors for missing required fields without calling the API

## 19. Frontend Product Detail / Stock History Page

- [x] 19.1 Create route file `frontend/src/routes/_layout/estoque/produtos/$productId/index.tsx`
- [x] 19.2 Implement a `useQuery` to fetch `GET /api/v1/products/{productId}` and show product header: name, category, fornecedor, unit price, description
- [x] 19.3 Implement a `useQuery` to fetch `GET /api/v1/products/{productId}/items` and render a stock history table with columns: Quantity, Status (badge), Service (link if set), Date
- [x] 19.4 Implement a `useQuery` to fetch `GET /api/v1/products/{productId}/prediction` and render a prediction card showing `days_to_stockout` and the color-coded level
- [x] 19.5 Add an "Adicionar Entrada" button (visible to admin only) that opens a modal to create a new `ProductItem` via `POST /api/v1/product-items`, then invalidates the items query
- [x] 19.6 Add an "Editar" button (visible to admin only) linking to the edit form
- [x] 19.7 Return a 404 page if the product does not exist

## 20. Frontend Service Scheduling Stock Warning Integration

- [x] 20.1 Update the service status update handler (in the service detail or service list page) to parse the `stock_warnings` field from the `PATCH /services/{id}` response
- [x] 20.2 Create a `StockWarningModal` component in `frontend/src/components/estoque/StockWarningModal.tsx` that displays a list of products with their shortfall quantities
- [x] 20.3 When `stock_warnings` is non-empty after a scheduling transition, show the `StockWarningModal` before confirming and dismissing the status update UI
- [x] 20.4 When `stock_warnings` is empty, proceed silently without showing the modal

## 21. Frontend "Baixar do Estoque" Integration

- [x] 21.1 In the service detail page (`frontend/src/routes/_layout/services/$serviceId/index.tsx`), when service status is `executing`, show a "Baixar do Estoque" button (visible to admin only)
- [x] 21.2 Create a `BaixarEstoqueModal` component in `frontend/src/components/estoque/BaixarEstoqueModal.tsx` that lists the `reservado` items for the service and asks for confirmation
- [x] 21.3 On confirmation, call `POST /api/v1/services/{serviceId}/baixar-estoque` and show a success toast with the count of items updated
- [x] 21.4 Invalidate any stock-related queries after the baixar action so the product history and dashboard refresh

## 22. Frontend Completion Review Integration

- [x] 22.1 In the service detail page, when moving a service to `completed`, display the count of auto-utilized stock items from the response (if > 0) in a completion summary toast or confirmation
- [x] 22.2 Invalidate stock-related queries after a service is completed so the dashboard and product history reflect the updated utilizado totals

## 23. Frontend Sidebar Navigation

- [x] 23.1 Add an "Estoque" link to the main sidebar component pointing to `/estoque`
- [x] 23.2 Ensure the Estoque link is visible only to `admin` and `finance` roles (guard with role check consistent with existing sidebar pattern)
