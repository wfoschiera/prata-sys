# prata-sys — Domain Model & Feature Inventory

Reference for the business domain and what's implemented. Load this on demand;
the root [`CLAUDE.md`](../CLAUDE.md) keeps only a one-line overview and links here.

**prata-sys** is a business management system for a **water well drilling company**
in Brazil. It manages clients, service orders, suppliers, inventory, quotes, and
finances.

## Domain Concepts

- **Cliente**: Can be a person (CPF) or company (CNPJ). Located in Brazil. Has
  structured address fields (address, bairro, city, state, CEP).
- **Orçamento**: A commercial quote/proposal linked to a client. Status:
  `rascunho` ⇄ `em_análise` ⇄ `aprovado` → `cancelado`. Items linked to product
  catalog with per-item price visibility. Can be converted to a Serviço (one-time).
  Has company letterhead from CompanySettings.
- **Serviço**: A service order linked to a client. Two top-level types:
  - `perfuração` (water well drilling)
  - `manutenção/reparo` (repair service)
  - Each service can have line items of type `material` or `serviço`, optionally
    linked to a Product
  - Status lifecycle: `requested` → `scheduled` → `executing` → `completed`
    (or `cancelled` from any non-terminal)
  - Stock is reserved on `scheduled`, deducted on `completed`, released on `cancelled`
- **Endereço de execução**: The site where the service is performed — may differ
  from the client's address.
- **Fornecedor**: Supplier with contact info and bank account details for payment.
- **Estoque**: Product types → Products → ProductItems (physical stock units).
  Status: `em_estoque` → `reservado` → `utilizado`. Stock prediction with a 90-day
  consumption window.
- **Entrada de estoque**: One physical delivery from one supplier on one date.
  Groups the ProductItem lots received and owns the cost adjustments applying to the
  delivery as a whole.
- **Custo de aquisição**: `Product.unit_price` is a *sale* price. Real acquisition
  cost is tracked separately: `ProductItem.custo_unitario_nf` (the invoice unit price,
  write-once) plus typed `CustoAjuste` rows (frete, seguro, ICMS-ST, IPI, desconto
  comercial, devolução, correção de documento, …), each carrying a reference to its
  supporting document. Adjustments are apportioned across a delivery's lots by value
  share to derive `custo_unitario_real`, and averaged per product into
  `custo_medio_ponderado`. Lots predating the feature have no cost and are reported
  via `lotes_sem_custo` rather than silently averaged.
- **CompanySettings**: Singleton table for company letterhead (name, CNPJ, address,
  phone, email, logo) used in orçamento documents.
- **Roles**: `admin`, `finance`, `client` (implemented); `technician`, `geologist`,
  `supervisor` (planned).

## Implemented (Phases 1–9)

- **Cadastro** (registration) for Admins, Finance users, and Clients (CPF/CNPJ) with
  structured address fields (bairro, city, state, CEP)
- **Serviços** (service orders): full lifecycle (requested → scheduled → executing →
  completed / cancelled), stock reservation/deduction on transitions, status audit
  log, deletion/item mutation guards
- **RBAC**: role-based permissions (`admin`, `finance`, `client`) with per-user
  overrides, per-request caching
- **Financeiro**: transaction management (receitas/despesas), finance dashboard with
  KPI cards and 6-month chart
- **Fornecedores**: supplier management with contacts, categories, and bank account info
- **Estoque**: product types, products, product items (stock entries), stock
  prediction (green/yellow/red), reservation with `SELECT FOR UPDATE`, dashboard
- **Orçamentos** (quotes): full document lifecycle (rascunho ⇄ em_análise ⇄ aprovado
  → cancelado), items linked to product catalog, per-item price visibility toggle,
  convert-to-service (one-time), duplicate, browser print, company letterhead settings
- **Security**: login rate limiting (slowapi, 5/min), password reset token
  invalidation, readiness endpoint with DB probe
- **Frontend**: paginated lists (20 items/page), structured logging on service
  transitions

## Roadmap

- Orçamento edit form + inline item management (Phase 9 Wave D)
- Company settings admin page in frontend
- Client portal: clients monitor water well status and fill well data
- Roles: field technician ("técnico de campo"), geologist ("geólogo"), supervisor
- PDF generation for orçamentos (server-side)
- Billing from completed services

For a deeper architecture and code-map walkthrough, see [`../ONBOARDING.md`](../ONBOARDING.md).
