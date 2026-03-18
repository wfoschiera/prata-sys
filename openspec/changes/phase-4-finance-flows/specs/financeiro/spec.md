## ADDED Requirements

### Requirement: Transaction can be created by authorized users
The system SHALL allow users with `manage_financeiro` permission to create a transaction by providing `tipo` (receita | despesa), `categoria`, `valor` (positive, BRL), `data_competencia`, and an optional `descricao`, `service_id`, and `client_id`. The `client_id` field is only valid when `tipo` is `receita`.

#### Scenario: Successful expense creation
- **WHEN** a user with `manage_financeiro` submits a POST to `/api/v1/transacoes` with `tipo=despesa`, a valid `categoria` for an expense, a positive `valor`, and a `data_competencia`
- **THEN** the system creates a new `Transacao` record and returns HTTP 201 with the created transaction payload including `id`, `tipo`, `categoria`, `valor`, `data_competencia`, `descricao`, `service_id`, and `client_id`

#### Scenario: Successful income creation linked to a service
- **WHEN** a user with `manage_financeiro` submits a POST to `/api/v1/transacoes` with `tipo=receita`, `categoria=SERVICO`, a valid `service_id`, a positive `valor`, and a `data_competencia`
- **THEN** the system creates the transaction linked to that service and returns HTTP 201

#### Scenario: Unauthorized user cannot create transaction
- **WHEN** a user without `manage_financeiro` submits a POST to `/api/v1/transacoes`
- **THEN** the system returns HTTP 403 Forbidden

#### Scenario: Negative or zero valor is rejected
- **WHEN** a POST to `/api/v1/transacoes` provides `valor` of `0` or a negative number
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Income category used with tipo despesa is rejected
- **WHEN** a POST to `/api/v1/transacoes` provides `tipo=despesa` and `categoria=SERVICO` (an income-only category)
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: client_id on a despesa is rejected
- **WHEN** a POST to `/api/v1/transacoes` provides `tipo=despesa` and a non-null `client_id`
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Non-existent service_id is rejected
- **WHEN** a POST to `/api/v1/transacoes` provides a `service_id` that does not exist in the database
- **THEN** the system returns HTTP 404 Not Found

---

### Requirement: Transactions list is returned without N+1 queries
The system SHALL return all transactions from `GET /api/v1/transacoes` with related `service` (summary only: id, tipo, status) and `client` (summary only: id, nome) eagerly loaded using `selectinload()`.

#### Scenario: Transactions list loads related data in bounded queries
- **WHEN** a user with `view_financeiro` sends GET to `/api/v1/transacoes` and there are N transactions with linked services and clients
- **THEN** the system returns all transactions with embedded service and client summaries
- **AND** the total number of SQL queries SHALL be at most 3 regardless of N

#### Scenario: List supports filtering by tipo
- **WHEN** a user sends GET to `/api/v1/transacoes?tipo=despesa`
- **THEN** the system returns only transactions where `tipo=despesa`

#### Scenario: List supports filtering by categoria
- **WHEN** a user sends GET to `/api/v1/transacoes?categoria=COMBUSTIVEL`
- **THEN** the system returns only transactions with `categoria=COMBUSTIVEL`

#### Scenario: List supports filtering by date range
- **WHEN** a user sends GET to `/api/v1/transacoes?data_inicio=2025-01-01&data_fim=2025-01-31`
- **THEN** the system returns only transactions where `data_competencia` falls within the given range (inclusive)

#### Scenario: Filters can be combined
- **WHEN** a user sends GET to `/api/v1/transacoes?tipo=despesa&categoria=COMBUSTIVEL&data_inicio=2025-01-01`
- **THEN** the system returns only transactions matching all supplied filters simultaneously

#### Scenario: Empty list is returned when no transactions match
- **WHEN** a GET to `/api/v1/transacoes` is sent and no transactions exist or no transactions match the filters
- **THEN** the system returns HTTP 200 with an empty array `[]`

---

### Requirement: Transaction detail is accessible
The system SHALL return the full detail of a single transaction from `GET /api/v1/transacoes/{id}`, including embedded service and client summaries.

#### Scenario: Existing transaction is retrieved
- **WHEN** a user with `view_financeiro` sends GET to `/api/v1/transacoes/{id}` for an existing transaction
- **THEN** the system returns HTTP 200 with the full transaction object

#### Scenario: Non-existent transaction returns 404
- **WHEN** a GET is sent to `/api/v1/transacoes/{id}` for an id that does not exist
- **THEN** the system returns HTTP 404 Not Found

---

### Requirement: Transaction can be updated by authorized users
The system SHALL allow users with `manage_financeiro` to update a transaction's `valor`, `data_competencia`, `descricao`, `categoria`, and `service_id` via PATCH. `tipo` and `client_id` cannot be changed after creation.

#### Scenario: Successful update
- **WHEN** a user with `manage_financeiro` sends PATCH to `/api/v1/transacoes/{id}` with a new `valor`
- **THEN** the system updates the field and returns HTTP 200 with the updated transaction

#### Scenario: Tipo cannot be changed after creation
- **WHEN** a PATCH to `/api/v1/transacoes/{id}` includes a `tipo` field
- **THEN** the system ignores the `tipo` field (or returns 422 if strictly validated)

---

### Requirement: Transaction can be deleted by authorized users
The system SHALL allow users with `manage_financeiro` to delete a transaction via DELETE `/api/v1/transacoes/{id}`. Deletion is permanent with no soft-delete.

#### Scenario: Successful deletion
- **WHEN** a user with `manage_financeiro` sends DELETE to `/api/v1/transacoes/{id}` for an existing transaction
- **THEN** the system deletes the record and returns HTTP 204 No Content

#### Scenario: Deleting a non-existent transaction returns 404
- **WHEN** a DELETE is sent to `/api/v1/transacoes/{id}` for an id that does not exist
- **THEN** the system returns HTTP 404 Not Found

---

### Requirement: Monthly summary endpoint provides income and expense totals
The system SHALL expose `GET /api/v1/transacoes/resumo` that returns the total `receitas`, total `despesas`, and `resultado_liquido` (receitas − despesas) for a given month. The month is specified by `ano` and `mes` query parameters (defaults to current month if omitted).

#### Scenario: Summary for a month with transactions
- **WHEN** a user with `view_financeiro` sends GET to `/api/v1/transacoes/resumo?ano=2025&mes=1`
- **THEN** the system returns a JSON object with `total_receitas`, `total_despesas`, `resultado_liquido`, `ano`, and `mes`

#### Scenario: Summary for a month with no transactions
- **WHEN** a GET is sent to `/api/v1/transacoes/resumo` for a month with no transactions
- **THEN** the system returns HTTP 200 with `total_receitas=0`, `total_despesas=0`, `resultado_liquido=0`

---

### Requirement: Finance Dashboard page displays monthly financial overview
The system SHALL provide a frontend page at `/financeiro` accessible to users with `view_financeiro`. The page SHALL show KPI cards for the current month and a bar chart comparing total receitas vs. total despesas for the last 6 months.

#### Scenario: Dashboard renders KPI cards for current month
- **WHEN** a user with `view_financeiro` navigates to `/financeiro`
- **THEN** the page displays three KPI cards: "Receitas (mês)", "Despesas (mês)", and "Resultado Líquido"
- **AND** each card shows the correct BRL-formatted amount from the `/resumo` endpoint

#### Scenario: Dashboard renders 6-month comparison chart
- **WHEN** a user with `view_financeiro` navigates to `/financeiro`
- **THEN** the page displays a bar chart with grouped bars for receitas and despesas for each of the last 6 months

#### Scenario: Unauthorized user cannot access dashboard
- **WHEN** a user without `view_financeiro` navigates to `/financeiro`
- **THEN** the router redirects them away (e.g., to `/`)

---

### Requirement: Transactions list page with filters
The system SHALL provide a frontend page at `/financeiro/transacoes` listing all transactions with filter controls for `tipo`, `categoria`, and a date range picker.

#### Scenario: Transactions list renders with data
- **WHEN** a user with `view_financeiro` navigates to `/financeiro/transacoes`
- **THEN** the page displays a table with columns: Data, Tipo, Categoria, Descrição, Valor, Serviço (linked), Cliente (linked)

#### Scenario: Filter by tipo hides unmatched rows
- **WHEN** the user selects "Despesa" in the tipo filter
- **THEN** only expense rows remain visible; income rows are hidden

#### Scenario: Empty state is shown when no transactions match filters
- **WHEN** the active filters return no results
- **THEN** the page displays an empty-state message indicating no transactions found

---

### Requirement: Add Transaction form allows creating a transaction
The system SHALL provide an "Add Transaction" modal or page accessible from `/financeiro/transacoes` where users with `manage_financeiro` can fill in all required fields. The `categoria` select SHALL dynamically filter to show only categories valid for the selected `tipo`.

#### Scenario: Successful form submission creates transaction
- **WHEN** a user with `manage_financeiro` fills in all required fields and submits
- **THEN** the system calls POST `/api/v1/transacoes`, the list refreshes to include the new row, and a success toast is shown

#### Scenario: Category dropdown filters by tipo
- **WHEN** the user selects `tipo=Receita`
- **THEN** the categoria dropdown shows only income categories: Serviço, Venda de Equipamento, Rendimento, Capital Fixo

#### Scenario: Category dropdown filters by tipo (despesa)
- **WHEN** the user selects `tipo=Despesa`
- **THEN** the categoria dropdown shows only expense categories: Combustível, Manutenção de Equipamento, Manutenção de Veículo, Manutenção de Escritório, Compra de Material, Mão de Obra CLT, Mão de Obra Diarista, Administrativo

#### Scenario: Form prevents submission with missing required fields
- **WHEN** the user submits the form without selecting `categoria` or entering `valor`
- **THEN** the form displays inline validation errors and does not call the API

---

### Requirement: Contas a Pagar page lists upcoming expenses
The system SHALL provide a frontend page at `/financeiro/contas-a-pagar` accessible to users with `view_contas_pagar`. For MVP this is a filtered view of transactions where `tipo=despesa` — it serves as a ledger of recorded expenses.

#### Scenario: Page renders expense transactions
- **WHEN** a user with `view_contas_pagar` navigates to `/financeiro/contas-a-pagar`
- **THEN** the page displays a filtered transaction list showing only `despesa` records

---

### Requirement: Contas a Receber page lists income transactions
The system SHALL provide a frontend page at `/financeiro/contas-a-receber` accessible to users with `view_contas_receber`. For MVP this is a filtered view of transactions where `tipo=receita`.

#### Scenario: Page renders income transactions
- **WHEN** a user with `view_contas_receber` navigates to `/financeiro/contas-a-receber`
- **THEN** the page displays a filtered transaction list showing only `receita` records

---

### Requirement: Sidebar finance section renders based on permissions

The system SHALL display finance-related links in the main application sidebar conditionally based on the current user's effective permissions.

#### Scenario: Finance user sees all finance links
- **WHEN** a user with `view_financeiro`, `view_contas_pagar`, and `view_contas_receber` is logged in
- **THEN** the sidebar shows: "Financeiro" (dashboard), "Transações", "Contas a Pagar", "Contas a Receber"

#### Scenario: User without finance permissions sees no finance links
- **WHEN** a user without any finance permissions is logged in
- **THEN** none of the finance sidebar links are visible

---

## Domain Model

### Enums

**TipoTransacao**
- `receita` — money coming in
- `despesa` — money going out

**CategoriaTransacao**

Income categories (valid only when `tipo=receita`):
- `SERVICO` — payment received for a service order
- `VENDA_EQUIPAMENTO` — sale of equipment
- `RENDIMENTO` — investment return or interest income
- `CAPITAL_FIXO` — capital injection or fixed asset proceeds

Expense categories (valid only when `tipo=despesa`):
- `COMBUSTIVEL` — fuel for vehicles and machinery
- `MANUTENCAO_EQUIPAMENTO` — equipment repair and maintenance
- `MANUTENCAO_VEICULO` — vehicle repair and maintenance
- `MANUTENCAO_ESCRITORIO` — office maintenance and utilities
- `COMPRA_MATERIAL` — purchase of drilling materials, connections, tubes
- `MO_CLT` — CLT payroll (formal employees)
- `MO_DIARISTA` — day laborer payments (per-service labor)
- `ADMIN` — administrative costs (accounting, banking fees, subscriptions)

### Table Model: Transacao

| Column | Type | Constraints | Notes |
|---|---|---|---|
| `id` | UUID | PK, default uuid4 | |
| `tipo` | TipoTransacao enum | NOT NULL | receita or despesa |
| `categoria` | CategoriaTransacao enum | NOT NULL | must be valid for tipo |
| `valor` | Numeric(12, 2) | NOT NULL, > 0 | BRL, always positive |
| `data_competencia` | Date | NOT NULL | accounting date |
| `descricao` | Text | nullable | free-text memo |
| `service_id` | UUID | FK → service.id, SET NULL, nullable, indexed | optional linkage |
| `client_id` | UUID | FK → client.id, SET NULL, nullable, indexed | receita only |
| `created_at` | DateTime | NOT NULL, default utcnow | audit |
| `updated_at` | DateTime | NOT NULL, default utcnow, onupdate | audit |

No `installment` fields. No soft-delete (`deleted_at`). MVP scope.

### API Schemas

**TransacaoCreate**
```
tipo: TipoTransacao
categoria: CategoriaTransacao
valor: Decimal (> 0)
data_competencia: date
descricao: str | None
service_id: UUID | None
client_id: UUID | None  # only valid when tipo=receita
```

**TransacaoUpdate** (all fields optional)
```
categoria: CategoriaTransacao | None
valor: Decimal | None
data_competencia: date | None
descricao: str | None
service_id: UUID | None
```

**TransacaoPublic**
```
id: UUID
tipo: TipoTransacao
categoria: CategoriaTransacao
valor: Decimal
data_competencia: date
descricao: str | None
service_id: UUID | None
client_id: UUID | None
service: ServiceSummary | None  # embedded
client: ClientSummary | None    # embedded
created_at: datetime
updated_at: datetime
```

**ResumoMensal**
```
ano: int
mes: int
total_receitas: Decimal
total_despesas: Decimal
resultado_liquido: Decimal
```

### API Endpoints

| Method | Path | Permission | Description |
|---|---|---|---|
| GET | `/api/v1/transacoes` | `view_financeiro` | List transactions; supports `?tipo`, `?categoria`, `?data_inicio`, `?data_fim`, `?service_id`, `?skip`, `?limit` |
| POST | `/api/v1/transacoes` | `manage_financeiro` | Create transaction |
| GET | `/api/v1/transacoes/resumo` | `view_financeiro` | Monthly summary totals; supports `?ano`, `?mes` |
| GET | `/api/v1/transacoes/{id}` | `view_financeiro` | Get single transaction |
| PATCH | `/api/v1/transacoes/{id}` | `manage_financeiro` | Update transaction (tipo immutable) |
| DELETE | `/api/v1/transacoes/{id}` | `manage_financeiro` | Delete transaction |

### Constraints and Validation Rules

1. `valor` MUST be strictly positive (> 0). Zero and negative values are rejected at the Pydantic level.
2. `categoria` MUST be compatible with `tipo`. Income categories are only valid for `tipo=receita`; expense categories are only valid for `tipo=despesa`. This is enforced in the Pydantic `model_validator`.
3. `client_id` may only be set when `tipo=receita`. Setting it on a `despesa` is a 422 error.
4. `service_id` may be set on either `tipo`. A service income links directly to the service; a labor expense (`MO_DIARISTA`) can also be linked to a service.
5. Currency is BRL only. No multi-currency, no FX, no installments in MVP.
6. `tipo` is immutable after creation — it determines the category set and foreign key rules.
7. Deleting a `Service` or `Client` does NOT cascade-delete transactions. FKs are SET NULL (historical record preservation).

### Permissions

Two new permissions are added to `ALL_PERMISSIONS`:

| Permission | PT-BR Label | Assigned to (role defaults) |
|---|---|---|
| `manage_financeiro` | Gerenciar Financeiro | `finance` |
| `view_financeiro` | Visualizar Financeiro | `finance`, `admin` |

The existing `view_contas_pagar` and `view_contas_receber` permissions (already in `ALL_PERMISSIONS` from Phase 3) are now wired to real pages. Their role defaults remain as specified in Phase 3 (`finance` gets both).
