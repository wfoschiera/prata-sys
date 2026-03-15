# Tasks: Phase 9 — Orçamento

## 1. Data model + migrations

- [x] 1.1 Add `OrcamentoStatus` enum (`rascunho`, `em_analise`, `aprovado`, `cancelado`) to `models.py`
- [x] 1.2 Add `VALID_ORCAMENTO_TRANSITIONS` dict to `models.py`
- [x] 1.3 Define `Orcamento` SQLModel table: id (UUID PK), ref_code (unique 6-char hex), client_id (FK), service_type (ServiceType), status (OrcamentoStatus), execution_address (required), city, cep, description, notes, forma_pagamento, validade_proposta (date), vendedor, created_by (FK → User), service_id (FK → Service, nullable), created_at, updated_at
- [x] 1.4 Define `OrcamentoItem` SQLModel table: id (UUID PK), orcamento_id (FK, cascade), product_id (FK → Product, RESTRICT), description, quantity (Decimal 12,4), unit_price (Decimal 10,2), show_unit_price (bool), created_at
- [x] 1.5 Define `OrcamentoStatusLog` table: id (UUID PK), orcamento_id (FK, cascade), from_status, to_status, changed_by (FK → User), changed_at, notes
- [x] 1.6 Add Pydantic schemas: OrcamentoCreate, OrcamentoUpdate, OrcamentoRead, OrcamentoListRead, OrcamentosPublic, OrcamentoItemCreate, OrcamentoItemUpdate, OrcamentoItemRead, OrcamentoTransitionRequest, OrcamentoStatusLogRead
- [x] 1.7 Add relationships: Orcamento.client, Orcamento.items, Orcamento.status_logs, Orcamento.created_by_user, Orcamento.service, OrcamentoItem.product
- [x] 1.8 Generate Alembic migration for orcamento, orcamento_item, orcamento_status_log tables
- [x] 1.9 Review and clean migration (remove autogenerate noise)

## 2. Client model expansion

- [x] 2.1 Add `bairro: str | None`, `city: str | None`, `state: str | None`, `cep: str | None` to `ClientBase` in models.py
- [x] 2.2 Add same fields to `ClientCreate`, `ClientUpdate`, `ClientPublic` schemas
- [x] 2.3 Generate Alembic migration: ADD COLUMN × 4, all nullable
- [x] 2.4 Update frontend client form to include new fields (bairro, city, state, cep)
- [x] 2.5 Regenerate OpenAPI client

## 3. Company settings (Empresa)

- [x] 3.1 Define `CompanySettings` SQLModel table (singleton, id=1)
- [x] 3.2 Define `CompanySettingsRead` and `CompanySettingsUpdate` schemas
- [x] 3.3 Add CRUD: `get_company_settings`, `update_company_settings` in crud.py
- [x] 3.4 Add route file: `backend/app/api/routes/settings.py` with GET/PUT `/settings/empresa`
- [x] 3.5 Register route in api_router (main.py)
- [x] 3.6 Generate Alembic migration for company_settings table
- [x] 3.7 Seed default company settings in init_db or migration
- [x] 3.8 Add frontend Settings > Empresa page with form

## 4. Backend — Orçamento CRUD

- [x] 4.1 Add `generate_ref_code()` helper (secrets.token_hex(3).upper(), retry on collision)
- [x] 4.2 Add `create_orcamento(session, orcamento_in, created_by_id)` in crud.py
- [x] 4.3 Add `get_orcamento(session, orcamento_id)` with selectinload for client, items.product, status_logs
- [x] 4.4 Add `get_orcamentos(session, search, status, data_inicio, data_fim, skip, limit)` — list with filters, pagination, count
- [x] 4.5 Add `update_orcamento(session, db_orcamento, orcamento_in)` — guard: only rascunho/em_análise
- [x] 4.6 Add `delete_orcamento(session, db_orcamento)` — guard: only rascunho
- [x] 4.7 Add `transition_orcamento_status(session, orcamento, to_status, changed_by_id, reason)` — validate transitions, create log, enforce guards (see specs)
- [x] 4.8 Add `create_orcamento_item(session, orcamento_id, item_in)` — validate product_id exists, guard status
- [x] 4.9 Add `update_orcamento_item(session, db_item, item_in)` — guard status
- [x] 4.10 Add `delete_orcamento_item(session, db_item)` — guard status
- [x] 4.11 Add `convert_orcamento_to_service(session, orcamento, created_by_id)` — create Service + ServiceItems, set service_id
- [x] 4.12 Add `duplicate_orcamento(session, orcamento, created_by_id)` — deep copy with new ref_code

## 5. Backend — Routes

- [x] 5.1 Create `backend/app/api/routes/orcamentos.py` with all endpoints from specs
- [x] 5.2 Add permission guards: `manage_orcamentos` for all, `view_orcamentos` for GET (if needed)
- [x] 5.3 Register in `backend/app/api/main.py`
- [x] 5.4 Add `manage_orcamentos` and `view_orcamentos` to `ALL_PERMISSIONS` in permissions.py
- [x] 5.5 Add both permissions to admin and finance role defaults

## 6. Backend — Tests

- [x] 6.1 Add `tests/api/routes/test_orcamentos.py` — CRUD operations (create, read, list, update, delete)
- [x] 6.2 Add transition tests: valid forward/backward, invalid, cancellation, terminal guard
- [x] 6.3 Add item CRUD tests with status guards
- [x] 6.4 Add convert-to-service test: happy path, already-converted guard, not-approved guard
- [x] 6.5 Add duplicate test: copy correctness, ref_code uniqueness, status reset
- [x] 6.6 Add filter tests: search by name, CPF/CNPJ, date range, status
- [x] 6.7 Add permission tests: finance can manage, client role denied

## 7. Frontend — OpenAPI client regeneration

- [x] 7.1 Run `bash ./scripts/generate-client.sh` after backend API changes
- [x] 7.2 Verify OrcamentoService, OrcamentoItemCreate, etc. are generated

## 8. Frontend — Orçamento list page

- [x] 8.1 Create `frontend/src/routes/_layout/orcamentos/index.tsx` — list page
- [x] 8.2 Add filter bar: client search (name/CPF/CNPJ), status filter, date range picker
- [x] 8.3 Add paginated table: ref_code, client name, description, status badge, created date
- [x] 8.4 Add "Novo Orçamento" button → navigates to /orcamentos/new
- [x] 8.5 Row click → navigate to /orcamentos/:id
- [x] 8.6 Add PaginationBar (reuse existing component)

## 9. Frontend — Orçamento form (create/edit)

- [x] 9.1 Create `frontend/src/routes/_layout/orcamentos/new.tsx` — create form
- [x] 9.2 Create `frontend/src/routes/_layout/orcamentos/$orcamentoId/edit.tsx` — edit form
- [x] 9.3 Form fields: client dropdown, service_type, execution_address, city, cep, description, notes, forma_pagamento, validade_proposta (date picker), vendedor
- [x] 9.4 Items section: add/remove items, product dropdown (search), quantity, unit_price (default from product), show_unit_price toggle
- [x] 9.5 Item total calculated live (qty × unit_price)
- [x] 9.6 Grand total calculated at bottom

## 10. Frontend — Orçamento detail page

- [x] 10.1 Create `frontend/src/routes/_layout/orcamentos/$orcamentoId/index.tsx` — detail page
- [x] 10.2 Display: company header (from /settings/empresa), client info block, items table
- [x] 10.3 Status badge with transition buttons (based on current status + valid transitions)
- [x] 10.4 "Criar Serviço" button (only when aprovado + service_id is null)
- [x] 10.5 "Serviço criado: #ID" link (when service_id is set, links to service detail)
- [x] 10.6 "Duplicar Orçamento" button (always available)
- [x] 10.7 "Imprimir" button → opens print view or triggers window.print()
- [x] 10.8 Status log timeline (who changed what, when)

## 11. Frontend — Print view

- [x] 11.1 Create print-optimized CSS for the orçamento detail page
- [x] 11.2 @media print: hide nav, sidebar, action buttons; show company header, client block, items table, footer
- [x] 11.3 Handle show_unit_price: show "—" when hidden
- [x] 11.4 Test print output matches the paper document format

## 12. Navigation + sidebar

- [x] 12.1 Add "Orçamentos" item to the sidebar navigation (between Clientes and Serviços)
- [x] 12.2 Gate visibility by manage_orcamentos or view_orcamentos permission
