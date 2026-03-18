# Specs: Phase 9 — Orçamento

## Data model

### Orcamento table

```python
class OrcamentoStatus(str, enum.Enum):
    rascunho = "rascunho"
    em_analise = "em_analise"
    aprovado = "aprovado"
    cancelado = "cancelado"

VALID_ORCAMENTO_TRANSITIONS: dict[OrcamentoStatus, list[OrcamentoStatus]] = {
    OrcamentoStatus.rascunho:   [OrcamentoStatus.em_analise, OrcamentoStatus.cancelado],
    OrcamentoStatus.em_analise: [OrcamentoStatus.rascunho, OrcamentoStatus.aprovado, OrcamentoStatus.cancelado],
    OrcamentoStatus.aprovado:   [OrcamentoStatus.em_analise, OrcamentoStatus.cancelado],
    OrcamentoStatus.cancelado:  [],
}
```

### ref_code generation

```python
import secrets
def generate_ref_code() -> str:
    """6-char uppercase hex. Retry on collision (16^6 = ~16M combinations)."""
    return secrets.token_hex(3).upper()
```

Stored as `ref_code: str = Field(unique=True, index=True, max_length=6)` on the Orcamento model.

### OrcamentoItem

Each item links to a Product from the catalog:

```
OrcamentoItem:
  product_id: UUID (FK → Product, required, ondelete=RESTRICT)
  description: str (max 500, defaults to product.name but overridable)
  quantity: Decimal(12,4) > 0
  unit_price: Decimal(10,2) >= 0 (defaults to product.unit_price but overridable)
  show_unit_price: bool = True
```

Calculated `total = quantity × unit_price` is NOT stored — computed in the schema/frontend.

### Client model expansion

Add to ClientBase:

```python
bairro: str | None = Field(default=None, max_length=100)
city: str | None = Field(default=None, max_length=100)
state: str | None = Field(default=None, max_length=2)  # UF (e.g. "MT")
cep: str | None = Field(default=None, max_length=9)     # 00000-000
```

Alembic migration: ADD COLUMN × 4, all nullable.

### Company settings (Empresa)

New table `CompanySettings` (singleton — only 1 row):

```python
class CompanySettings(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)  # singleton
    company_name: str
    cnpj: str | None
    inscricao_municipal: str | None
    address: str | None
    phone: str | None
    email: str | None
    logo_url: str | None
```

## API endpoints

### Orçamento CRUD

| Method | Path | Response | Auth |
|--------|------|----------|------|
| GET    | /orcamentos | OrcamentosPublic (paginated) | manage_orcamentos |
| POST   | /orcamentos | OrcamentoRead | manage_orcamentos |
| GET    | /orcamentos/{id} | OrcamentoRead (full detail) | manage_orcamentos |
| PATCH  | /orcamentos/{id} | OrcamentoRead | manage_orcamentos |
| DELETE | /orcamentos/{id} | 204 | manage_orcamentos |
| POST   | /orcamentos/{id}/transition | OrcamentoTransitionResponse | manage_orcamentos |
| POST   | /orcamentos/{id}/convert-to-service | ServiceRead | manage_orcamentos |
| POST   | /orcamentos/{id}/duplicate | OrcamentoRead | manage_orcamentos |

### Orçamento Items

| Method | Path | Response | Auth |
|--------|------|----------|------|
| POST   | /orcamentos/{id}/items | OrcamentoItemRead | manage_orcamentos |
| PATCH  | /orcamentos/{id}/items/{item_id} | OrcamentoItemRead | manage_orcamentos |
| DELETE | /orcamentos/{id}/items/{item_id} | 204 | manage_orcamentos |

### Company Settings

| Method | Path | Response | Auth |
|--------|------|----------|------|
| GET    | /settings/empresa | CompanySettingsRead | any authenticated |
| PUT    | /settings/empresa | CompanySettingsRead | admin only |

### Filters on GET /orcamentos

Query params:
- `search: str` — matches client.name, client.document_number (CPF/CNPJ)
- `status: OrcamentoStatus` — filter by status
- `data_inicio: date` — created_at >= date
- `data_fim: date` — created_at <= date
- `skip: int`, `limit: int` — pagination

## State machine behavior

### Transition rules

```
rascunho ⇄ em_análise:
  - No restrictions beyond valid status check

em_análise ⇄ aprovado:
  - To approve: orçamento must have at least 1 item
  - To un-approve (back to em_análise): only if service_id is NULL

Any → cancelado:
  - Only if service_id is NULL (can't cancel a converted quote)
  - Cancelado is terminal — no transitions out

Guards on item mutation:
  - Items can be added/edited/removed only when status is rascunho or em_análise
  - Aprovado and cancelado are locked
```

### Convert to Serviço

```
POST /orcamentos/{id}/convert-to-service

Preconditions:
  - status == aprovado
  - service_id IS NULL (not yet converted)

Creates:
  Service:
    type = orcamento.service_type
    client_id = orcamento.client_id
    execution_address = orcamento.execution_address
    description = orcamento.description
    notes = orcamento.notes

  For each OrcamentoItem:
    ServiceItem:
      item_type = ItemType.material
      product_id = orcamento_item.product_id
      description = orcamento_item.description
      quantity = orcamento_item.quantity
      unit_price = orcamento_item.unit_price

Sets orcamento.service_id = new_service.id
Returns: ServiceRead
```

### Duplicate

```
POST /orcamentos/{id}/duplicate

Creates a new Orcamento:
  - Copies: client_id, service_type, execution_address, city, cep,
    description, notes, forma_pagamento, vendedor, items
  - Resets: status=rascunho, ref_code=new, service_id=NULL,
    validade_proposta=NULL, created_by=current_user
  - Does NOT copy: status_logs
Returns: OrcamentoRead (the new copy)
```

## Frontend routes

```
/orcamentos              → OrcamentoList (paginated, filtered)
/orcamentos/new          → OrcamentoForm (create)
/orcamentos/:id          → OrcamentoDetail (full document view + actions)
/orcamentos/:id/edit     → OrcamentoForm (edit)
/orcamentos/:id/print    → OrcamentoPrintView (print-optimized, @media print)
```

## Print view layout

Matches the paper document structure:

```
┌─────────────────────────────────────────────────┐
│ [LOGO]  FOSCHIERA E FOSCHIERA...                │
│         CNPJ: ... | Inscrição: ...              │
│         Endereço | Fone | Email                 │
├─────────────────────────────────────────────────┤
│ Nome:           │ CPF/CNPJ:                     │
│ Endereço:       │ Bairro:                       │
│ Cidade:         │ CEP:                          │
│ Telefone:       │ E-mail:                       │
├─────────────────────────────────────────────────┤
│ ORÇAMENTO                    Data: DD/MM/YYYY   │
├──────┬──────────────────┬──────────┬────────────┤
│ Qtde │ Descrição        │ R$ Unit. │ R$ Total   │
├──────┼──────────────────┼──────────┼────────────┤
│ 100  │ Mão de obra...   │   —      │ 18.000,00  │
│ 17   │ Bomba submersa   │ 8.731,00 │ 148.427,00 │
│ ...  │ ...              │ ...      │ ...        │
├──────┴──────────────────┴──────────┼────────────┤
│                                    │ R$ TOTAL   │
├────────────────────────────────────┴────────────┤
│ Forma de pagamento: à vista desconto...         │
│ Validade da proposta: DD/MM/YYYY                │
│ Vendedor: Luciele Foschiera                     │
└─────────────────────────────────────────────────┘
```

When `show_unit_price = false` on an item, the R$ Unit. cell shows "—".
