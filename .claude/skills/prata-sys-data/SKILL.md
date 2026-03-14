---
name: prata-sys-data
description: |
  prata-sys PostgreSQL database reference — tables, columns, relationships, enums, and SQL patterns.
  Use this skill whenever someone asks to write SQL, analyze data, understand the data model, write raw
  PostgreSQL queries, debug database issues, write Alembic migrations, or needs to understand relationships
  between entities. Triggers on: "SQL", "query", "PostgreSQL", "database", "tabela", "dados", "schema",
  "migration", "Alembic", "model", "relationship", "join", "estoque", "inventory", "financeiro",
  "transacao", "service", "client", "fornecedor", "product", "stock".
---

# prata-sys Database — PostgreSQL Schema Reference

This skill helps you write accurate SQL queries and understand the data model for prata-sys, a water well drilling company management system backed by PostgreSQL.

## Database Access

- **ORM**: SQLModel (SQLAlchemy under the hood)
- **Migrations**: Alembic
- **Connection**: configured in `backend/app/core/config.py` via `SQLALCHEMY_DATABASE_URI`
- **All models**: defined in `backend/app/models.py`
- **All CRUD**: defined in `backend/app/crud.py`

## Schema Overview

```
user                    # System users (admin, finance, client roles)
user_permission         # Per-user permission overrides
client                  # Clients (CPF or CNPJ)
service                 # Service orders (drilling or repair)
serviceitem             # Line items within a service (material or service type)
service_status_log      # Audit trail of service status transitions
transacao               # Financial transactions (income/expense)
fornecedor              # Suppliers
fornecedor_contato      # Supplier contacts
fornecedor_categoria    # Supplier product categories (M2M)
producttype             # Inventory product type definitions
product                 # Specific products (linked to type + supplier)
productitem             # Individual stock items with status tracking
```

## Table Details

### user
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| email | VARCHAR(255) | Unique, indexed |
| hashed_password | VARCHAR | |
| is_active | BOOLEAN | Default true |
| is_superuser | BOOLEAN | Default false |
| full_name | VARCHAR(255) | Nullable |
| role | ENUM('admin','finance','client') | Default 'admin' |
| created_at | TIMESTAMPTZ | |

### user_permission
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| user_id | UUID | FK → user.id (CASCADE), indexed |
| permission | VARCHAR(100) | |
| | | UNIQUE(user_id, permission) |

### client
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| name | VARCHAR(255) | |
| document_type | ENUM('cpf','cnpj') | |
| document_number | VARCHAR(14) | Unique. CPF=11 digits, CNPJ=14 chars |
| email | VARCHAR(255) | Nullable |
| phone | VARCHAR(50) | Nullable |
| address | VARCHAR(500) | Nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | Nullable |

### service
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| client_id | UUID | FK → client.id |
| type | ENUM('perfuração','reparo') | |
| status | ENUM('requested','scheduled','executing','completed','cancelled') | Default 'requested' |
| execution_address | VARCHAR(500) | Where work is performed |
| description | TEXT | Nullable |
| notes | TEXT | Nullable |
| cancelled_reason | VARCHAR(500) | Nullable, required when cancelled |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | Nullable |

### serviceitem
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| service_id | UUID | FK → service.id |
| item_type | ENUM('material','serviço') | |
| description | VARCHAR(500) | |
| quantity | FLOAT | > 0 |
| unit_price | FLOAT | >= 0 |

### service_status_log
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| service_id | UUID | FK → service.id (CASCADE), indexed |
| from_status | ServiceStatus ENUM | |
| to_status | ServiceStatus ENUM | |
| changed_by | UUID | FK → user.id (SET NULL), nullable |
| changed_at | TIMESTAMPTZ | |
| notes | VARCHAR(500) | Nullable |

### transacao
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| tipo | ENUM('receita','despesa') | Immutable after creation |
| categoria | CategoriaTransacao ENUM | Must match tipo (see below) |
| valor | NUMERIC(12,2) | > 0 |
| data_competencia | DATE | Accrual date |
| descricao | TEXT | Nullable |
| nome_contraparte | VARCHAR(200) | Nullable |
| service_id | UUID | FK → service.id (SET NULL), indexed, nullable |
| client_id | UUID | FK → client.id (SET NULL), indexed, nullable. Only for receita |
| fornecedor_id | UUID | FK → fornecedor.id (SET NULL), indexed, nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | |

### fornecedor
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| company_name | VARCHAR(255) | Indexed |
| cnpj | VARCHAR(14) | Nullable |
| address | VARCHAR(500) | Nullable |
| notes | TEXT | Nullable |

### fornecedor_contato
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| fornecedor_id | UUID | FK → fornecedor.id (CASCADE), indexed |
| name | VARCHAR(255) | |
| telefone | VARCHAR(20) | |
| whatsapp | VARCHAR(20) | Nullable |
| description | VARCHAR(100) | Contact role/description |

### fornecedor_categoria
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| fornecedor_id | UUID | FK → fornecedor.id (CASCADE), indexed |
| category | VARCHAR(20) | UNIQUE(fornecedor_id, category) |

### producttype
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| category | ENUM('tubos','conexoes','bombas','cabos','outros') | |
| name | VARCHAR(255) | UNIQUE(category, name) |
| unit_of_measure | VARCHAR(50) | e.g. "metros", "unidades" |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | Nullable |

### product
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| product_type_id | UUID | FK → producttype.id (RESTRICT) |
| name | VARCHAR(255) | |
| fornecedor_id | UUID | FK → fornecedor.id (SET NULL), nullable |
| unit_price | NUMERIC(10,2) | >= 0 |
| description | TEXT | Nullable |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | Nullable |

### productitem
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| product_id | UUID | FK → product.id (CASCADE) |
| quantity | NUMERIC(12,4) | > 0 |
| status | ENUM('em_estoque','reservado','utilizado') | Default 'em_estoque' |
| service_id | UUID | FK → service.id (SET NULL), nullable. Set when reserved/used |
| created_at | TIMESTAMPTZ | |
| updated_at | TIMESTAMPTZ | Nullable |

## Enums Reference

### ServiceStatus — Valid Transitions
```
requested → scheduled, cancelled
scheduled → executing, cancelled
executing → completed, cancelled
completed → (terminal)
cancelled → (terminal)
```

### CategoriaTransacao
**Income categories** (tipo='receita' only):
- `SERVICO` — Service revenue
- `VENDA_EQUIPAMENTO` — Equipment sales
- `RENDIMENTO` — Investment returns
- `CAPITAL_FIXO` — Fixed capital

**Expense categories** (tipo='despesa' only):
- `COMBUSTIVEL` — Fuel
- `MANUTENCAO_EQUIPAMENTO` — Equipment maintenance
- `MANUTENCAO_VEICULO` — Vehicle maintenance
- `MANUTENCAO_ESCRITORIO` — Office maintenance
- `COMPRA_MATERIAL` — Material purchases
- `MO_CLT` — Formal labor (CLT)
- `MO_DIARISTA` — Day labor
- `ADMIN` — Administrative

### ProductCategory / FornecedorCategoryEnum
`tubos`, `conexoes`, `bombas`, `cabos`, `outros`

### ProductItemStatus — Inventory Flow
```
em_estoque → reservado (when assigned to a service)
reservado → utilizado (when service completes — stock deduction)
reservado → em_estoque (if service cancelled — stock return)
```

## Key Relationships

```
Client 1──N Service
Service 1──N ServiceItem
Service 1──N ServiceStatusLog
Service 1──N ProductItem (reserved/used stock)
Fornecedor 1──N FornecedorContato
Fornecedor 1──N FornecedorCategoria
Fornecedor 1──N Product
ProductType 1──N Product
Product 1──N ProductItem
Transacao N──1 Service (optional)
Transacao N──1 Client (optional, receita only)
Transacao N──1 Fornecedor (optional)
```

## Common SQL Query Patterns

### Monthly financial summary (receitas vs despesas)
```sql
SELECT
  EXTRACT(YEAR FROM data_competencia) AS ano,
  EXTRACT(MONTH FROM data_competencia) AS mes,
  SUM(CASE WHEN tipo = 'receita' THEN valor ELSE 0 END) AS total_receitas,
  SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END) AS total_despesas,
  SUM(CASE WHEN tipo = 'receita' THEN valor ELSE -valor END) AS resultado_liquido
FROM transacao
WHERE data_competencia >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY 1, 2
ORDER BY 1, 2;
```

### Services by status
```sql
SELECT
  s.status,
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE s.type = 'perfuração') AS perfuracao,
  COUNT(*) FILTER (WHERE s.type = 'reparo') AS reparo
FROM service s
GROUP BY s.status
ORDER BY s.status;
```

### Revenue per client
```sql
SELECT
  c.name,
  c.document_number,
  COUNT(DISTINCT t.id) AS num_transacoes,
  SUM(t.valor) AS total_receita
FROM transacao t
JOIN client c ON c.id = t.client_id
WHERE t.tipo = 'receita'
GROUP BY c.id, c.name, c.document_number
ORDER BY total_receita DESC;
```

### Current stock levels by product
```sql
SELECT
  pt.category,
  p.name AS product_name,
  pt.unit_of_measure,
  COALESCE(SUM(pi.quantity) FILTER (WHERE pi.status = 'em_estoque'), 0) AS em_estoque,
  COALESCE(SUM(pi.quantity) FILTER (WHERE pi.status = 'reservado'), 0) AS reservado,
  COALESCE(SUM(pi.quantity) FILTER (WHERE pi.status = 'utilizado'), 0) AS utilizado
FROM product p
JOIN producttype pt ON pt.id = p.product_type_id
LEFT JOIN productitem pi ON pi.product_id = p.id
GROUP BY pt.category, p.name, pt.unit_of_measure
ORDER BY pt.category, p.name;
```

### Service audit trail
```sql
SELECT
  ssl.changed_at,
  ssl.from_status,
  ssl.to_status,
  u.full_name AS changed_by_name,
  ssl.notes
FROM service_status_log ssl
LEFT JOIN "user" u ON u.id = ssl.changed_by
WHERE ssl.service_id = :service_id
ORDER BY ssl.changed_at;
```

### Expenses by category in a period
```sql
SELECT
  categoria,
  COUNT(*) AS num_transacoes,
  SUM(valor) AS total
FROM transacao
WHERE tipo = 'despesa'
  AND data_competencia BETWEEN :start_date AND :end_date
GROUP BY categoria
ORDER BY total DESC;
```

### Supplier spending
```sql
SELECT
  f.company_name,
  COUNT(t.id) AS num_transacoes,
  SUM(t.valor) AS total_gasto
FROM transacao t
JOIN fornecedor f ON f.id = t.fornecedor_id
WHERE t.tipo = 'despesa'
GROUP BY f.id, f.company_name
ORDER BY total_gasto DESC;
```

### Stock reserved for a service
```sql
SELECT
  p.name AS product_name,
  pi.quantity,
  pi.status
FROM productitem pi
JOIN product p ON p.id = pi.product_id
WHERE pi.service_id = :service_id
ORDER BY p.name;
```

## Domain Knowledge

### Service Lifecycle
1. A service starts as `requested` when created
2. Admin schedules it → `scheduled`
3. Field team begins work → `executing`
4. Work finishes → `completed` (requires stock deduction items)
5. At any non-terminal stage → `cancelled` (requires reason; reserved stock returns to `em_estoque`)

### Financial Rules
- `tipo` is immutable after creation (cannot change receita to despesa)
- `client_id` is only valid for `receita` (income) transactions
- `categoria` must match `tipo` (income categories for receita, expense categories for despesa)
- `valor` must always be > 0

### Inventory Flow
- Products are received into stock as `ProductItem` entries with status `em_estoque`
- When a service needs materials, items are `reservado` (linked via `service_id`)
- On service completion, reserved items become `utilizado`
- On service cancellation, reserved items return to `em_estoque`
- Stock warnings are generated when service items require more material than available

## PostgreSQL-Specific Notes

- All IDs are UUID type (use `uuid_generate_v4()` or `gen_random_uuid()` in raw SQL)
- The `user` table name is a PostgreSQL reserved word — always quote it: `"user"`
- Timestamps are all `TIMESTAMPTZ` (timezone-aware)
- Money values use `NUMERIC(12,2)` for transactions and `NUMERIC(10,2)` for product prices
- Quantity for product items uses `NUMERIC(12,4)` for precision with fractional units (e.g., meters of cable)
- Use `FILTER (WHERE ...)` for conditional aggregation instead of CASE expressions
- Use `COALESCE(..., 0)` for nullable aggregations
