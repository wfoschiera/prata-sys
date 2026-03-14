## 1. Data Models

- [ ] 1.1 Add `FornecedorCategoryEnum(str, Enum)` to `backend/app/models.py` with values: `tubos`, `conexoes`, `bombas`, `cabos`, `outros`
- [ ] 1.2 Add `Fornecedor(SQLModel, table=True)` to `models.py` with fields: `id` (UUID PK), `company_name` (str, max 255, indexed), `cnpj` (str | None), `address` (str | None), `notes` (str | None)
- [ ] 1.3 Add `FornecedorContato(SQLModel, table=True)` with fields: `id` (UUID PK), `fornecedor_id` (FK → fornecedor.id, ondelete="CASCADE", indexed), `name` (str, max 255), `telefone` (str, max 20), `whatsapp` (str | None, max 20), `description` (str, max 100)
- [ ] 1.4 Add `FornecedorCategoria(SQLModel, table=True)` with fields: `id` (UUID PK), `fornecedor_id` (FK → fornecedor.id, ondelete="CASCADE", indexed), `category` (str, stores enum value); unique constraint on `(fornecedor_id, category)`
- [ ] 1.5 Add relationships on `Fornecedor`: `contatos: list["FornecedorContato"]` with `cascade_delete=True`; `categorias: list["FornecedorCategoria"]` with `cascade_delete=True`
- [ ] 1.6 Add back-reference `fornecedor: "Fornecedor"` on `FornecedorContato`

## 2. Pydantic Schemas

- [ ] 2.1 Add `FornecedorBase(SQLModel)` with `company_name`, `cnpj`, `address`, `notes`; add CNPJ validator using `@field_validator`: if provided, must match `^\d{14}$` else raise ValueError
- [ ] 2.2 Add `FornecedorCreate(FornecedorBase)` with `categories: list[FornecedorCategoryEnum] = []`
- [ ] 2.3 Add `FornecedorUpdate(FornecedorBase)` with all fields optional and `categories: list[FornecedorCategoryEnum] | None = None`
- [ ] 2.4 Add `FornecedorContatoBase(SQLModel)` with `name`, `telefone`, `whatsapp`, `description`
- [ ] 2.5 Add `FornecedorContatoCreate(FornecedorContatoBase)` and `FornecedorContatoUpdate(FornecedorContatoBase)` with all fields optional on Update
- [ ] 2.6 Add `FornecedorContatoPublic(FornecedorContatoBase)` with `id` and `fornecedor_id`
- [ ] 2.7 Add `FornecedorPublic(FornecedorBase)` with `id`, `categories: list[FornecedorCategoryEnum]`, `contatos: list[FornecedorContatoPublic]`

## 3. Alembic Migration

- [ ] 3.1 Run `alembic revision --autogenerate -m "add fornecedor tables"` from `backend/`
- [ ] 3.2 Review the generated migration: verify `fornecedor`, `fornecedor_contato`, `fornecedor_categoria` tables, the partial unique index on `fornecedor.cnpj` (where cnpj is not null), the unique constraint on `(fornecedor_id, category)`, and cascade delete constraints
- [ ] 3.3 Add partial unique index manually in migration if autogenerate does not produce it: `op.create_index("ix_fornecedor_cnpj_unique", "fornecedor", ["cnpj"], unique=True, postgresql_where=sa.text("cnpj IS NOT NULL"))`
- [ ] 3.4 Run `alembic upgrade head` in dev and verify tables exist
- [ ] 3.5 Add a second migration `alembic revision -m "add transacao fornecedor_id fk"` that adds the FK constraint from `transacao.fornecedor_id` → `fornecedor.id` (with `ondelete="SET NULL"`). This column was added in Phase 4 without a FK; now that `fornecedor` exists, the constraint can be enforced.

## 4. CRUD Functions

- [ ] 4.1 Add `get_fornecedores(session, search, category) -> list[Fornecedor]` to `crud.py`; use `selectinload(Fornecedor.contatos)` and `selectinload(Fornecedor.categorias)`; apply `ilike` filter on `company_name` if `search` provided; filter by `category` via join to `FornecedorCategoria` if `category` provided
- [ ] 4.2 Add `get_fornecedor(session, fornecedor_id) -> Fornecedor | None` with same selectinloads
- [ ] 4.3 Add `create_fornecedor(session, data: FornecedorCreate) -> Fornecedor`; create `Fornecedor`, then create `FornecedorCategoria` rows for each category in `data.categories`
- [ ] 4.4 Add `update_fornecedor(session, fornecedor, data: FornecedorUpdate) -> Fornecedor`; update scalar fields; if `data.categories is not None`, delete all existing `FornecedorCategoria` for this fornecedor and insert the new set
- [ ] 4.5 Add `delete_fornecedor(session, fornecedor) -> None`; cascade handled by DB, just delete the root record
- [ ] 4.6 Add `create_contato(session, fornecedor_id, data: FornecedorContatoCreate) -> FornecedorContato`
- [ ] 4.7 Add `update_contato(session, contato, data: FornecedorContatoUpdate) -> FornecedorContato`; update only provided (non-None) fields
- [ ] 4.8 Add `delete_contato(session, contato) -> None`

## 5. API Routes

- [ ] 5.1 Create `backend/app/api/routes/fornecedores.py` with `router = APIRouter(prefix="/fornecedores", tags=["fornecedores"])`
- [ ] 5.2 `GET /fornecedores` — returns `list[FornecedorPublic]`; guard `require_permission("view_fornecedores")`; accepts `search: str | None` and `category: FornecedorCategoryEnum | None` as query params
- [ ] 5.3 `POST /fornecedores` — returns `FornecedorPublic`; status 201; guard `require_permission("manage_fornecedores")`; return 409 if CNPJ already exists
- [ ] 5.4 `GET /fornecedores/{fornecedor_id}` — returns `FornecedorPublic`; 404 if not found; guard `require_permission("view_fornecedores")`
- [ ] 5.5 `PATCH /fornecedores/{fornecedor_id}` — returns `FornecedorPublic`; guard `require_permission("manage_fornecedores")`; 404 if not found; 409 if new CNPJ conflicts
- [ ] 5.6 `DELETE /fornecedores/{fornecedor_id}` — returns 204; guard `require_permission("manage_fornecedores")`; 404 if not found
- [ ] 5.7 `POST /fornecedores/{fornecedor_id}/contatos` — returns `FornecedorContatoPublic`; status 201; guard `require_permission("manage_fornecedores")`; 404 if fornecedor not found
- [ ] 5.8 `PATCH /fornecedores/{fornecedor_id}/contatos/{contato_id}` — returns `FornecedorContatoPublic`; guard `require_permission("manage_fornecedores")`; 404 if contato not found or does not belong to fornecedor
- [ ] 5.9 `DELETE /fornecedores/{fornecedor_id}/contatos/{contato_id}` — returns 204; guard `require_permission("manage_fornecedores")`; same 404 logic
- [ ] 5.10 Register the fornecedores router in `backend/app/api/main.py`

## 6. Permissions Update

- [ ] 6.1 Add `"view_fornecedores": "Visualizar Fornecedores"` and `"manage_fornecedores": "Gerenciar Fornecedores"` to `ALL_PERMISSIONS` in `backend/app/core/permissions.py`
- [ ] 6.2 Add `"view_fornecedores"` and `"manage_fornecedores"` to `ROLE_PERMISSIONS[UserRole.admin]`
- [ ] 6.3 Add `"view_fornecedores"` to `ROLE_PERMISSIONS[UserRole.finance]`

## 7. Frontend: Regenerate API Client

- [ ] 7.1 Run `bash ./scripts/generate-client.sh` to pick up new schemas (`FornecedorPublic`, `FornecedorContatoPublic`, `FornecedorCreate`, etc.) and all new `/fornecedores` endpoints

## 8. Frontend: Fornecedores List Page

- [ ] 8.1 Create route `frontend/src/routes/_layout/fornecedores/index.tsx`
- [ ] 8.2 Add `beforeLoad` guard: redirect to `/` if user lacks `view_fornecedores` permission
- [ ] 8.3 Fetch `GET /fornecedores` via TanStack Query; pass `search` and `category` as reactive query params
- [ ] 8.4 Render a search text input that updates `search` query param on change (debounced)
- [ ] 8.5 Render category filter pills/buttons for each `FornecedorCategoryEnum` value; clicking toggles the `category` query param
- [ ] 8.6 Render a table with columns: company name, CNPJ (or "—"), categories as badges, contacts count; clicking a row navigates to `/fornecedores/{id}`
- [ ] 8.7 Show "Novo Fornecedor" button only if user has `manage_fornecedores`; clicking navigates to `/fornecedores/new`
- [ ] 8.8 Show empty state message "Nenhum fornecedor cadastrado." when list is empty

## 9. Frontend: Fornecedor Detail / Form Page

- [ ] 9.1 Create route `frontend/src/routes/_layout/fornecedores/$fornecedorId.tsx` (handles both `/new` and `/{id}`)
- [ ] 9.2 On load for existing fornecedor: fetch `GET /fornecedores/{id}` and populate form
- [ ] 9.3 Section 1 — Dados da empresa: form fields for `company_name` (required), `cnpj` (optional, show hint "14 dígitos"), `address` (optional), `notes` (optional textarea)
- [ ] 9.4 Zod schema for the company form: `company_name: z.string().min(1)`, `cnpj: z.string().regex(/^\d{14}$/).optional().or(z.literal(""))`, others optional strings
- [ ] 9.5 Save button calls `POST /fornecedores` (new) or `PATCH /fornecedores/{id}` (existing); show success/error toast
- [ ] 9.6 Section 2 — Categorias: render a checkbox for each `FornecedorCategoryEnum` value; on change call `PATCH /fornecedores/{id}` with updated categories list
- [ ] 9.7 Section 3 — Contatos: render a table of existing contacts with columns: name, description, telefone, whatsapp; add/edit/delete actions (only if `manage_fornecedores`)
- [ ] 9.8 "Adicionar contato" opens an inline form or dialog with fields: name, description, telefone, whatsapp; on submit calls `POST /fornecedores/{id}/contatos`; invalidates the detail query
- [ ] 9.9 Edit contact: opens the same form pre-populated; on submit calls `PATCH /fornecedores/{id}/contatos/{contato_id}`
- [ ] 9.10 Delete contact: confirmation dialog "Remover este contato?"; on confirm calls `DELETE /fornecedores/{id}/contatos/{contato_id}`
- [ ] 9.11 "Excluir fornecedor" button at bottom (only if `manage_fornecedores` and editing existing); confirmation dialog with cascade warning; on confirm calls `DELETE /fornecedores/{id}` then redirects to `/fornecedores`
- [ ] 9.12 Show/hide all write controls based on `manage_fornecedores` permission (read-only view for finance)

## 10. Frontend: Sidebar

- [ ] 10.1 Add "Fornecedores" sidebar link pointing to `/fornecedores`; conditionally render only if user has `view_fornecedores` permission (or `is_superuser`)

## 11. Backend Tests

- [ ] 11.1 Create `backend/tests/test_fornecedores.py`
- [ ] 11.2 `test_create_fornecedor` — POST creates record, returns id, empty contatos, empty categories
- [ ] 11.3 `test_create_fornecedor_with_categories` — POST with categories, GET returns them
- [ ] 11.4 `test_create_fornecedor_duplicate_cnpj` — second POST with same CNPJ returns 409
- [ ] 11.5 `test_create_fornecedor_invalid_cnpj` — CNPJ with 13 digits or letters returns 422
- [ ] 11.6 `test_create_fornecedor_no_cnpj` — omitting CNPJ succeeds
- [ ] 11.7 `test_get_fornecedores_search` — search by partial company name returns matching only
- [ ] 11.8 `test_get_fornecedores_category_filter` — filter returns only fornecedores with that category
- [ ] 11.9 `test_update_fornecedor_replaces_categories` — PATCH with new categories list replaces old
- [ ] 11.10 `test_update_fornecedor_no_categories_field` — PATCH without categories field leaves them unchanged
- [ ] 11.11 `test_delete_fornecedor_cascades` — DELETE removes contatos; subsequent GET returns 404
- [ ] 11.12 `test_create_contato` — POST adds contact, appears in GET detail
- [ ] 11.13 `test_update_contato` — PATCH updates fields
- [ ] 11.14 `test_delete_contato` — DELETE removes contact, not present in detail
- [ ] 11.15 `test_contato_wrong_fornecedor` — PATCH/DELETE contato with mismatched fornecedor_id returns 404
- [ ] 11.16 `test_finance_can_read` — finance role: GET /fornecedores and GET /fornecedores/{id} return 200
- [ ] 11.17 `test_finance_cannot_write` — finance role: POST returns 403
- [ ] 11.18 `test_client_cannot_read` — client role without override: GET returns 403
- [ ] 11.19 `test_admin_full_access` — admin: all endpoints return 2xx
- [ ] 11.20 `test_superuser_bypass` — superuser with role=client: all endpoints return 2xx
- [ ] 11.21 `test_no_n_plus_one` — verify list query uses ≤3 SQL statements for N fornecedores with contacts (use `sqlalchemy.event` or assert statement count)

## 12. Verification

- [ ] 12.1 Run backend tests: `bash scripts/test.sh` — all pass
- [ ] 12.2 Run frontend lint + build: `cd frontend && bun run lint && bun run build`
- [ ] 12.3 Manual test: admin sees "Fornecedores" in sidebar; navigates to list; creates a fornecedor with CNPJ, address, two contacts, and three categories
- [ ] 12.4 Manual test: admin edits a fornecedor — changes company name, removes one category, adds a contact, deletes another contact
- [ ] 12.5 Manual test: finance user sees "Fornecedores" in sidebar; can view list and detail; "Novo Fornecedor" button is not visible; form fields are read-only
- [ ] 12.6 Manual test: admin deletes a fornecedor — confirmation dialog appears; after confirm, redirected to list and fornecedor is gone
- [ ] 12.7 Manual test: search by partial name and category filter work correctly
