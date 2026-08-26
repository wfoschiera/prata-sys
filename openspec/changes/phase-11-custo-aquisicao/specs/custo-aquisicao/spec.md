## ADDED Requirements

### Requirement: Entrada de estoque records a delivery and creates its stock lots
The system SHALL allow users with `manage_estoque` to register an `EntradaEstoque` representing one delivery. An `EntradaEstoque` MUST have a `data_entrada` (date, not null) and MAY have a `fornecedor_id` (FK → `fornecedor.id`, nullable), a `numero_documento` (string, max 44), and an `observacao`. The request MUST include at least one lot line, each carrying a `product_id` (FK → `product.id`), a `quantity` (Decimal, > 0), and a `custo_unitario_nf` (Decimal, >= 0). Each lot line SHALL create one `ProductItem` with `status = em_estoque`, `service_id` null, `entrada_id` set to the new entrada, and `custo_unitario_nf` set from the request. The entrada, its lots, and its adjustments SHALL be created in a single transaction — a failure on any line SHALL leave no partial records. Read access requires `view_estoque`.

#### Scenario: Entrada with two lots creates stock
- **WHEN** a user with `manage_estoque` POSTs to `/api/v1/entradas-estoque` with `data_entrada`, a valid `fornecedor_id`, and two lot lines
- **THEN** the system returns HTTP 201 with the created entrada including `id`, `data_entrada`, `fornecedor`, and both lots
- **AND** two `ProductItem` records exist with `status = em_estoque` and `entrada_id` set to the new entrada

#### Scenario: User without manage_estoque cannot register an entrada
- **WHEN** a user holding only `view_estoque` POSTs to `/api/v1/entradas-estoque`
- **THEN** the system returns HTTP 403 Forbidden

#### Scenario: Entrada with no lot lines is rejected
- **WHEN** a POST to `/api/v1/entradas-estoque` provides an empty `itens` array
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Non-existent product is rejected and nothing is created
- **WHEN** a POST to `/api/v1/entradas-estoque` provides two lot lines where the second references a `product_id` that does not exist
- **THEN** the system returns HTTP 404 Not Found
- **AND** no `EntradaEstoque` and no `ProductItem` record is created

#### Scenario: Negative quantity is rejected
- **WHEN** a POST to `/api/v1/entradas-estoque` provides a lot line with `quantity` of `0` or negative
- **THEN** the system returns HTTP 422 Unprocessable Entity

---

### Requirement: Invoice unit cost is immutable once recorded
`ProductItem.custo_unitario_nf` SHALL be written exactly once, at lot creation, and SHALL NOT be modifiable thereafter. No update schema SHALL expose the field. Corrections to an invoice price SHALL be recorded as a `CustoAjuste` of type `correcao_documento` referencing the correcting document, preserving both the original figure and the correction. Lots created through `POST /api/v1/product-items` SHALL continue to be accepted with `custo_unitario_nf` null.

#### Scenario: No API surface exists to modify a recorded invoice cost
- **WHEN** a client sends PATCH or PUT to `/api/v1/product-items/{id}`
- **THEN** the system returns HTTP 404 Not Found, because no such route is defined
- **AND** no request schema in the application exposes `custo_unitario_nf` as a writable field outside lot creation

#### Scenario: Correction is recorded as an adjustment
- **WHEN** a user with `manage_estoque` POSTs a `CustoAjuste` of type `correcao_documento` with `documento_referencia` set to a carta de correção number
- **THEN** the system returns HTTP 201
- **AND** the lot's `custo_unitario_nf` remains at its original value
- **AND** the entrada's derived real cost reflects the correction

#### Scenario: Legacy stock entry without cost is still accepted
- **WHEN** a user with `manage_estoque` POSTs to `/api/v1/product-items` with only `product_id` and `quantity`
- **THEN** the system returns HTTP 201 with `custo_unitario_nf` null and `entrada_id` null

---

### Requirement: Cost adjustments are typed and carry a documentary reference
The system SHALL allow users with `manage_estoque` to attach `CustoAjuste` records to an existing `EntradaEstoque`. A `CustoAjuste` MUST have a `tipo` drawn from the closed set (`frete` | `seguro` | `icms_st` | `ipi` | `despesa_acessoria` | `desconto_comercial` | `devolucao` | `correcao_documento` | `outros`) and a `valor` (Decimal, non-zero). Adjustments of type `desconto_comercial` and `devolucao` MUST have `valor` < 0; all other types MUST have `valor` > 0. Adjustments of type `outros` MUST have a non-empty `observacao`. The system SHALL NOT accept a cost amount that is not classified by one of these types. Deleting an adjustment requires `manage_estoque`.

#### Scenario: Freight adjustment is attached to an entrada
- **WHEN** a user with `manage_estoque` POSTs to `/api/v1/entradas-estoque/{id}/ajustes` with `tipo: "frete"`, `valor: 200.00`, and `documento_referencia` set to a CT-e key
- **THEN** the system returns HTTP 201 with the created adjustment
- **AND** the entrada's derived real costs reflect the freight

#### Scenario: Positive value on a discount type is rejected
- **WHEN** a POST to `/api/v1/entradas-estoque/{id}/ajustes` provides `tipo: "desconto_comercial"` with `valor: 50.00`
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Negative value on a cost-increasing type is rejected
- **WHEN** a POST to `/api/v1/entradas-estoque/{id}/ajustes` provides `tipo: "frete"` with `valor: -50.00`
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Unclassified adjustment is rejected
- **WHEN** a POST to `/api/v1/entradas-estoque/{id}/ajustes` omits `tipo`
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Type outros without an explanation is rejected
- **WHEN** a POST to `/api/v1/entradas-estoque/{id}/ajustes` provides `tipo: "outros"` with a null or empty `observacao`
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: User without manage_estoque cannot attach an adjustment
- **WHEN** a user holding only `view_estoque` POSTs to `/api/v1/entradas-estoque/{id}/ajustes`
- **THEN** the system returns HTTP 403 Forbidden

---

### Requirement: Real unit cost is derived by value-share apportionment
The system SHALL derive `custo_unitario_real` for each lot of an entrada by apportioning the sum of the entrada's adjustments across its lots in proportion to each lot's invoice value (`custo_unitario_nf * quantity`), then dividing by the lot quantity. Apportioned shares SHALL be quantised to two decimal places, and the rounding residual SHALL be assigned to the lot with the largest invoice value, such that the sum of apportioned shares equals the sum of adjustments exactly. A lot with an invoice value of zero SHALL receive no share. Where the entrada's total invoice value is zero, adjustments SHALL be apportioned by quantity share instead. All monetary arithmetic SHALL use `Decimal`.

#### Scenario: Freight is apportioned by value share
- **WHEN** an entrada has lot A (`quantity` 10, `custo_unitario_nf` 100.00) and lot B (`quantity` 5, `custo_unitario_nf` 200.00) and a `frete` adjustment of 200.00
- **THEN** GET `/api/v1/entradas-estoque/{id}` returns `custo_unitario_real` of `110.00` for lot A and `220.00` for lot B

#### Scenario: Apportioned shares reconcile to the adjustment total
- **WHEN** an entrada's adjustments are apportioned across any number of lots
- **THEN** the sum of the apportioned shares equals the sum of the adjustment values to the centavo

#### Scenario: Bonificação receives no share of freight
- **WHEN** an entrada contains a lot with `custo_unitario_nf` of `0` alongside priced lots, and carries a `frete` adjustment
- **THEN** the zero-cost lot's `custo_unitario_real` is `0`
- **AND** the entire freight is apportioned across the priced lots

#### Scenario: Discount reduces real cost below invoice price
- **WHEN** an entrada with a single lot (`quantity` 10, `custo_unitario_nf` 100.00) carries a `desconto_comercial` adjustment of `-100.00`
- **THEN** the lot's `custo_unitario_real` is `90.00`

---

### Requirement: Weighted average cost excludes lots of unknown cost and reports coverage
The system SHALL expose `custo_medio_ponderado` per product: the quantity-weighted average of `custo_unitario_real` across that product's lots with `status = em_estoque` and a non-null `custo_unitario_nf`. Lots with a null `custo_unitario_nf` SHALL be excluded from the average and counted in `lotes_sem_custo`, which SHALL be returned alongside it. When no lot qualifies, `custo_medio_ponderado` SHALL be null rather than zero. Computing this value across a product list SHALL use a single aggregate query. Read access requires `view_estoque`.

#### Scenario: Average is weighted by quantity
- **WHEN** a product has one `em_estoque` lot of `quantity` 10 at real cost `100.00` and one of `quantity` 30 at real cost `200.00`
- **THEN** GET `/api/v1/products/{id}` returns `custo_medio_ponderado` of `175.00`

#### Scenario: Lots predating the feature are excluded and counted
- **WHEN** a product has two `em_estoque` lots with known cost and three with `custo_unitario_nf` null
- **THEN** GET `/api/v1/products/{id}` returns `custo_medio_ponderado` computed from the two priced lots
- **AND** returns `lotes_sem_custo` of `3`

#### Scenario: Product with no priced stock returns null, not zero
- **WHEN** a product has no `em_estoque` lot with a non-null `custo_unitario_nf`
- **THEN** GET `/api/v1/products/{id}` returns `custo_medio_ponderado` as `null`

#### Scenario: Consumed and reserved lots do not affect the average
- **WHEN** a product has priced lots in `utilizado` and `reservado` status alongside `em_estoque` lots
- **THEN** `custo_medio_ponderado` reflects only the `em_estoque` lots

#### Scenario: Product list computes averages in bounded queries
- **WHEN** a user with `view_estoque` sends GET to `/api/v1/products` and there are N products each with multiple stock lots
- **THEN** the system returns all products with `custo_medio_ponderado` and `lotes_sem_custo`
- **AND** the total number of SQL queries SHALL be at most 3 regardless of N

---

### Requirement: An entrada may book a corresponding despesa transaction
The system SHALL accept an optional `criar_transacao` flag on entrada creation, defaulting to `false`. When true, the system SHALL create one `Transacao` with `tipo = despesa`, `categoria = COMPRA_MATERIAL`, `valor` equal to the entrada's total invoice value plus its adjustments, `data_competencia` equal to `data_entrada`, and `fornecedor_id` copied from the entrada, and SHALL store its id on `EntradaEstoque.transacao_id`. The transaction SHALL NOT set `client_id`. When the flag is false or omitted, no transaction SHALL be created. Creating a transaction requires `manage_financeiro` in addition to `manage_estoque`.

#### Scenario: Entrada books the expense when requested
- **WHEN** a user with `manage_estoque` and `manage_financeiro` POSTs to `/api/v1/entradas-estoque` with `criar_transacao: true` for a delivery totalling `2200.00`
- **THEN** the system returns HTTP 201 with `transacao_id` populated
- **AND** a `Transacao` exists with `tipo = despesa`, `categoria = COMPRA_MATERIAL`, and `valor` of `2200.00`

#### Scenario: No transaction is created by default
- **WHEN** a POST to `/api/v1/entradas-estoque` omits `criar_transacao`
- **THEN** the system returns HTTP 201 with `transacao_id` null
- **AND** no `Transacao` record is created

#### Scenario: Booking a despesa without finance permission is rejected
- **WHEN** a user with `manage_estoque` but without `manage_financeiro` POSTs to `/api/v1/entradas-estoque` with `criar_transacao: true`
- **THEN** the system returns HTTP 403 Forbidden
- **AND** no `EntradaEstoque` and no `Transacao` record is created

---

### Requirement: Entradas can be listed and inspected
The system SHALL expose entrada listing and detail to users with `view_estoque`. The list SHALL support filtering by `fornecedor_id` and by `data_entrada` range. The detail response SHALL include the supplier, all lots with their `custo_unitario_nf` and derived `custo_unitario_real`, all adjustments with their `tipo` and `documento_referencia`, and the entrada totals. Related records SHALL be eagerly loaded.

#### Scenario: Entrada detail returns lots and adjustments
- **WHEN** a user with `view_estoque` sends GET to `/api/v1/entradas-estoque/{id}`
- **THEN** the system returns HTTP 200 with the entrada, its supplier, its lots including derived real costs, and its adjustments

#### Scenario: Entrada list is filtered by supplier
- **WHEN** a user with `view_estoque` sends GET to `/api/v1/entradas-estoque?fornecedor_id={id}`
- **THEN** the system returns HTTP 200 with only the entradas of that supplier

#### Scenario: Entrada detail loads relations in bounded queries
- **WHEN** a user with `view_estoque` sends GET to `/api/v1/entradas-estoque` and there are N entradas with lots and adjustments
- **THEN** the system returns all entradas with their nested data
- **AND** the total number of SQL queries SHALL be at most 4 regardless of N

#### Scenario: Unknown entrada returns not found
- **WHEN** a user with `view_estoque` sends GET to `/api/v1/entradas-estoque/{id}` for an id that does not exist
- **THEN** the system returns HTTP 404 Not Found

#### Scenario: User without view_estoque cannot read entradas
- **WHEN** a user holding neither `view_estoque` nor `manage_estoque` sends GET to `/api/v1/entradas-estoque`
- **THEN** the system returns HTTP 403 Forbidden
