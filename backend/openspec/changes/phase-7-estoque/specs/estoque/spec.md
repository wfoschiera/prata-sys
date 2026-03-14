## ADDED Requirements

### Requirement: Product types can be managed by admin users
The system SHALL allow users with the `admin` role to create, update, and delete product types. A `ProductType` MUST have a `category` (tubos | conexoes | bombas | cabos | outros), a `name` (string, not null, unique within category), and a `unit_of_measure` (string, e.g., "un", "m", "kg", "L"). Read access is granted to `admin` and `finance` roles.

#### Scenario: Admin creates a product type successfully
- **WHEN** an `admin` user POSTs to `/api/v1/product-types` with valid `category`, `name`, and `unit_of_measure`
- **THEN** the system creates a new `ProductType` record and returns HTTP 201 with the created object including `id`, `category`, `name`, and `unit_of_measure`

#### Scenario: Finance user cannot create a product type
- **WHEN** a `finance` user POSTs to `/api/v1/product-types`
- **THEN** the system returns HTTP 403 Forbidden

#### Scenario: Missing required field is rejected
- **WHEN** a POST to `/api/v1/product-types` omits `unit_of_measure`
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Finance user can read product types
- **WHEN** a `finance` user sends GET to `/api/v1/product-types`
- **THEN** the system returns HTTP 200 with an array of product types

---

### Requirement: Products can be managed by admin users
The system SHALL allow `admin` users to create, update, and delete products. A `Product` MUST have a `product_type_id` (FK → `product_type.id`), a `name` (string, not null), a `fornecedor_id` (FK → `fornecedor.id`, nullable), a `unit_price` (Decimal, >= 0), and an optional `description`. Read access is granted to `admin` and `finance` roles. Deleting a `ProductType` that still has associated `Product` records SHALL be rejected with HTTP 409 Conflict.

#### Scenario: Admin creates a product successfully
- **WHEN** an `admin` user POSTs to `/api/v1/products` with valid `product_type_id`, `name`, and `unit_price`
- **THEN** the system creates a new `Product` record and returns HTTP 201 with the created object including `id`, `product_type_id`, `name`, `fornecedor_id`, `unit_price`, and `description`

#### Scenario: Finance user cannot create a product
- **WHEN** a `finance` user POSTs to `/api/v1/products`
- **THEN** the system returns HTTP 403 Forbidden

#### Scenario: Non-existent product type is rejected
- **WHEN** a POST to `/api/v1/products` provides a `product_type_id` that does not exist
- **THEN** the system returns HTTP 404 Not Found

#### Scenario: Negative unit price is rejected
- **WHEN** a POST to `/api/v1/products` provides a `unit_price` of `-1.00`
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Deleting product type with products is rejected
- **WHEN** an `admin` user sends DELETE to `/api/v1/product-types/{id}` and that type has associated products
- **THEN** the system returns HTTP 409 Conflict with a message indicating the type is in use

---

### Requirement: Stock entries (ProductItem) can be registered and managed
The system SHALL allow `admin` users to create `ProductItem` records representing individual stock entries. A `ProductItem` MUST have a `product_id` (FK → `product.id`), a `quantity` (Decimal, > 0), a `status` (em_estoque | reservado | utilizado), and an optional `service_id` (FK → `service.id`, nullable). New entries created directly by an admin MUST default to status `em_estoque` and MUST NOT set `service_id`. Read access is granted to `admin` and `finance` roles.

#### Scenario: Admin adds stock entries to a product
- **WHEN** an `admin` user POSTs to `/api/v1/product-items` with a valid `product_id` and `quantity`
- **THEN** the system creates a new `ProductItem` with status `em_estoque` and `service_id` null, and returns HTTP 201

#### Scenario: Finance user cannot add stock entries
- **WHEN** a `finance` user POSTs to `/api/v1/product-items`
- **THEN** the system returns HTTP 403 Forbidden

#### Scenario: Zero or negative quantity is rejected
- **WHEN** a POST to `/api/v1/product-items` provides `quantity` of `0` or negative
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Non-existent product is rejected
- **WHEN** a POST to `/api/v1/product-items` provides a `product_id` that does not exist
- **THEN** the system returns HTTP 404 Not Found

---

### Requirement: Stock status transitions follow a defined lifecycle
The system SHALL enforce that `ProductItem.status` transitions follow the sequence: `em_estoque` → `reservado` → `utilizado`. Direct transitions from `em_estoque` to `utilizado`, from `utilizado` back to any prior state, or any other out-of-sequence transitions SHALL be rejected.

#### Scenario: Valid transition em_estoque → reservado
- **WHEN** an authorized system action transitions a `ProductItem` from `em_estoque` to `reservado` with a valid `service_id`
- **THEN** the system accepts the transition and persists the updated status and `service_id`

#### Scenario: Valid transition reservado → utilizado
- **WHEN** an `admin` user triggers "Baixar do estoque" for a `ProductItem` with status `reservado`
- **THEN** the system transitions the item to `utilizado` and returns HTTP 200

#### Scenario: Invalid skip transition is rejected
- **WHEN** an action attempts to transition a `ProductItem` directly from `em_estoque` to `utilizado`
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Reverse transition is rejected
- **WHEN** an action attempts to transition a `ProductItem` from `utilizado` to `reservado`
- **THEN** the system returns HTTP 422 Unprocessable Entity

---

### Requirement: Scheduling a service triggers automatic stock reservation with warning on shortage
The system SHALL, when a service status is updated to `scheduled`, attempt to reserve `em_estoque` `ProductItem` entries linked to that service's required materials. If sufficient stock is available, items are marked `reservado` automatically. If stock is insufficient for any product, the transition SHALL still proceed but the response MUST include a `stock_warnings` list identifying the affected products and the shortfall quantity.

#### Scenario: Scheduling with sufficient stock reserves items
- **WHEN** an authorized user moves a service to status `scheduled` and all required products have enough `em_estoque` items
- **THEN** the system marks the corresponding `ProductItem` entries as `reservado` with the service's `service_id`
- **AND** returns HTTP 200 with an empty `stock_warnings` list

#### Scenario: Scheduling with insufficient stock warns but proceeds
- **WHEN** an authorized user moves a service to status `scheduled` and a required product has fewer `em_estoque` items than needed
- **THEN** the system still transitions the service to `scheduled`
- **AND** returns HTTP 200 with a non-empty `stock_warnings` list indicating the product name and shortfall quantity

---

### Requirement: Executing a service allows manual "Baixar do estoque" action
The system SHALL provide a `POST /api/v1/services/{service_id}/baixar-estoque` endpoint that an `admin` user can call when a service is in `executing` status. This action SHALL transition all `reservado` `ProductItem` entries linked to that service to `utilizado`.

#### Scenario: Baixar do estoque transitions reservado items to utilizado
- **WHEN** an `admin` user POSTs to `/api/v1/services/{service_id}/baixar-estoque` and the service is in `executing` status
- **THEN** all `ProductItem` entries with status `reservado` and `service_id` matching the service are transitioned to `utilizado`
- **AND** the system returns HTTP 200 with the count of items updated

#### Scenario: Baixar do estoque on non-executing service is rejected
- **WHEN** an `admin` user POSTs to `/api/v1/services/{service_id}/baixar-estoque` and the service status is not `executing`
- **THEN** the system returns HTTP 422 Unprocessable Entity

---

### Requirement: Completing a service triggers automatic review of remaining reservado items
The system SHALL, when a service status is updated to `completed`, automatically transition any remaining `reservado` `ProductItem` entries linked to that service to `utilizado`. This ensures no stock items remain indefinitely in a `reservado` state after a service is closed.

#### Scenario: Completing a service auto-utilizes remaining reservado items
- **WHEN** an authorized user moves a service to status `completed` and there are `reservado` items for that service
- **THEN** the system transitions all such items to `utilizado`
- **AND** returns HTTP 200 with the updated service and a count of auto-utilized items

#### Scenario: Completing a service with no reservado items has no side effects
- **WHEN** an authorized user moves a service to status `completed` and no `reservado` items exist for that service
- **THEN** the system transitions the service to `completed` normally with no stock-related side effects

---

### Requirement: Stock depletion prediction is available per product
The system SHALL provide a `GET /api/v1/products/{product_id}/prediction` endpoint that returns a depletion prediction for the given product. The prediction MUST be computed as: `(em_estoque_qty - reservado_qty) / avg_daily_consumption`, where `avg_daily_consumption` is derived from `utilizado` records over a rolling 90-day window. If `avg_daily_consumption` is zero (no consumption history), the endpoint SHALL return `null` for `days_to_stockout`. The response MUST include a `level` field: `green` (> 30 days or null), `yellow` (8–30 days), `red` (0–7 days).

#### Scenario: Product with consumption history returns days_to_stockout
- **WHEN** a user sends GET to `/api/v1/products/{product_id}/prediction` for a product with utilizado records in the last 90 days
- **THEN** the system returns HTTP 200 with `days_to_stockout` (a number), `level` (green | yellow | red), `em_estoque_qty`, and `reservado_qty`

#### Scenario: Product with no consumption history returns null days_to_stockout
- **WHEN** a user sends GET to `/api/v1/products/{product_id}/prediction` for a product with no utilizado records
- **THEN** the system returns HTTP 200 with `days_to_stockout: null` and `level: "green"`

#### Scenario: Product with depleted net stock returns level red
- **WHEN** `em_estoque_qty - reservado_qty <= 0` for a product with any consumption history
- **THEN** the system returns `days_to_stockout: 0` and `level: "red"`

---

### Requirement: Stock overview dashboard provides aggregated counts per category
The system SHALL provide a `GET /api/v1/estoque/dashboard` endpoint that returns, for each product category, the total `em_estoque`, `reservado`, and `utilizado` quantities across all products in that category.

#### Scenario: Dashboard returns aggregated quantities per category
- **WHEN** a user with `admin` or `finance` role sends GET to `/api/v1/estoque/dashboard`
- **THEN** the system returns HTTP 200 with an array of objects, one per category, each containing `category`, `em_estoque_total`, `reservado_total`, and `utilizado_total`

#### Scenario: Empty stock returns zero counts for all categories
- **WHEN** no `ProductItem` records exist
- **THEN** the dashboard returns each known category with all totals set to `0`

---

### Requirement: Per-product stock history is accessible
The system SHALL provide a `GET /api/v1/products/{product_id}/items` endpoint that returns all `ProductItem` entries for a given product, ordered by `created_at` descending, including `id`, `quantity`, `status`, `service_id`, and `created_at`.

#### Scenario: Product stock history lists all items for a product
- **WHEN** a user sends GET to `/api/v1/products/{product_id}/items`
- **THEN** the system returns HTTP 200 with an array of `ProductItem` records for that product, ordered newest first

#### Scenario: Non-existent product returns 404
- **WHEN** a GET to `/api/v1/products/{product_id}/items` references a product that does not exist
- **THEN** the system returns HTTP 404 Not Found

---

### Requirement: Products list is returned without N+1 queries
The system SHALL return all products from `GET /api/v1/products` with `product_type` and `fornecedor` data eagerly loaded using `selectinload()` so that the query count does not grow with the number of products.

#### Scenario: Products list loads related data in bounded queries
- **WHEN** a user sends GET to `/api/v1/products` and there are N products
- **THEN** the system returns all products with `product_type` and `fornecedor` embedded
- **AND** the total SQL queries issued SHALL be at most 3 (one for products, one for product_types, one for fornecedores) regardless of N

---

### Requirement: Frontend products list page displays all products
The system SHALL provide a frontend page at `/estoque/produtos` listing all products, filterable by category, fornecedor, and stock status. The table MUST show product name, category, fornecedor name, unit price, total em_estoque quantity, and the depletion prediction level indicator.

#### Scenario: Products list renders with data
- **WHEN** a logged-in `admin` or `finance` user navigates to `/estoque/produtos`
- **THEN** the page displays a filterable table of products with name, category, fornecedor, unit price, total em_estoque quantity, and a color-coded prediction badge

#### Scenario: Prediction badge is color-coded
- **WHEN** a product has a `level` of `red`, `yellow`, or `green` from the prediction endpoint
- **THEN** the corresponding table row badge is displayed in red, yellow, or green respectively

#### Scenario: Empty state is shown when no products exist
- **WHEN** a logged-in user navigates to `/estoque/produtos` and no products exist
- **THEN** the page displays an empty-state message

---

### Requirement: Frontend stock overview dashboard shows category-level summaries
The system SHALL provide a frontend dashboard at `/estoque` with one card per product category displaying the `em_estoque`, `reservado`, and `utilizado` totals for that category.

#### Scenario: Dashboard displays category cards
- **WHEN** a logged-in `admin` or `finance` user navigates to `/estoque`
- **THEN** the page displays one card per category (tubos, conexoes, bombas, cabos, outros) with the aggregated em_estoque, reservado, and utilizado totals

---

### Requirement: Frontend scheduling flow validates stock and shows warnings
The system SHALL, when an authorized user schedules a service via the frontend, display a warning modal if the scheduling response contains a non-empty `stock_warnings` list, listing the affected product names and shortfall quantities before confirming the transition.

#### Scenario: Scheduling with stock shortage shows warning modal
- **WHEN** an authorized user moves a service to `scheduled` and the API returns stock warnings
- **THEN** the frontend displays a modal listing the products with insufficient stock before the user confirms

#### Scenario: Scheduling with sufficient stock proceeds silently
- **WHEN** an authorized user moves a service to `scheduled` and no stock warnings are returned
- **THEN** the service status is updated without any additional modal

---

### Requirement: Sidebar navigation includes an Estoque link
The system SHALL display an "Estoque" link in the main application sidebar that navigates to `/estoque`.

#### Scenario: Sidebar link navigates to estoque dashboard
- **WHEN** a logged-in user clicks "Estoque" in the sidebar
- **THEN** the browser navigates to `/estoque` and the stock overview dashboard is rendered
