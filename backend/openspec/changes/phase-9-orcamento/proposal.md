# Proposal: Phase 9 — Orçamento (Quotes)

## Problem

The company currently produces quotes (orçamentos) on paper using a spreadsheet template. There is no traceability, no status tracking, no search, and no way to convert a quote into a service order without re-entering all the data.

## Proposed solution

Add a full Orçamento (quote) module with:

1. **List page** — paginated list with filters (client name, CPF/CNPJ, date range)
2. **Detail page** — complete document view matching the paper format, with print support
3. **Status machine** — rascunho ⇄ em_análise ⇄ aprovado, with cancellation from any state
4. **Convert to Serviço** — one-click creation of a Service from an approved quote (one conversion only)
5. **Duplicate** — copy an existing orçamento as a new rascunho
6. **Per-item price visibility** — toggle unit price display per line item
7. **Browser print** — @media print CSS for professional document output

## Data model overview

```
Orcamento
  ├── client_id (FK → Client, required)
  ├── service_type (perfuração / reparo)
  ├── ref_code (6-char hex, unique, internal)
  ├── status (rascunho / em_análise / aprovado / cancelado)
  ├── execution_address (required)
  ├── city, cep (optional)
  ├── description (short text, shown in list)
  ├── notes (long text, optional)
  ├── forma_pagamento (text)
  ├── validade_proposta (date)
  ├── vendedor (text)
  ├── created_by (FK → User)
  ├── service_id (FK → Service, nullable, set on conversion)
  ├── created_at, updated_at
  └── items: list[OrcamentoItem]

OrcamentoItem
  ├── orcamento_id (FK → Orcamento, cascade)
  ├── product_id (FK → Product, required)
  ├── description (text, defaults to product.name)
  ├── quantity (Decimal > 0)
  ├── unit_price (Decimal >= 0, defaults to product.unit_price)
  ├── show_unit_price (bool, default True)
  └── created_at

OrcamentoStatusLog
  ├── orcamento_id (FK → Orcamento, cascade)
  ├── from_status, to_status
  ├── changed_by (FK → User)
  ├── changed_at
  └── notes (optional reason)
```

## State machine

```
rascunho ⇄ em_análise ⇄ aprovado
    ↓           ↓           ↓
 cancelado   cancelado   cancelado

After aprovado:
  - "Criar Serviço" button appears (one conversion only)
  - "Duplicar Orçamento" button always available
  - If service_id is set, button shows "Serviço criado" (disabled)
```

## Supporting changes

- **Client model expansion**: Add bairro, city, state, cep fields (migration)
- **Company settings**: Add Empresa config (company_name, cnpj, address, phone, email, logo_url) to system settings
- **Permissions**: `manage_orcamentos` (admin + finance), `view_orcamentos` (admin + finance)

## Non-goals

- PDF generation (server-side) — deferred, browser print is sufficient for now
- E-signature or WhatsApp send — future feature
- Stock reservation from orçamento — quotes never touch stock
- Client portal access to quotes — admin/finance only for now
- Discount calculation — covered by free-text forma_pagamento

## Success criteria

1. Admin/finance can create, edit, and manage orçamento lifecycle
2. Converting an approved orçamento to a service pre-fills all fields
3. The print view matches the paper document format shown in the reference image
4. Items are linked to products from the catalog
5. Per-item price visibility toggle works in both screen and print views
