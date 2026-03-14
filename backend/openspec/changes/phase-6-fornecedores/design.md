## Context

The application tracks clients, service orders, and permissions. Service orders require materials (tubes, connections, pumps, cables), but there is currently nowhere to record where those materials come from. Suppliers ("fornecedores") are the missing link between inventory/purchasing (Phase 7+) and the people the company actually calls to order goods.

Fornecedores are operationally different from clients: they may or may not be legal entities (CNPJ optional), they have multiple contacts with distinct roles, and they are classified by what they supply. Finance users need to look up suppliers to process payments; admins need to manage the records.

This design introduces three new tables (`fornecedor`, `fornecedor_contato`, `fornecedor_categoria`), a new router, two new permissions, and two new frontend pages, following the same patterns established in Phase 2 (Serviços) and Phase 3 (RBAC).

## Goals / Non-Goals

**Goals:**
- Store supplier company info with optional CNPJ and address
- Store multiple contacts per supplier with role descriptions
- Associate suppliers with product categories via a dedicated table using a fixed enum
- Expose list + detail CRUD via the existing permission system
- Frontend pages: list with search/filter, detail with inline contact management and category checkboxes

**Non-Goals:**
- Bank account / payment info on fornecedores (deferred to a future "contas a pagar" phase)
- Linking fornecedores directly to service orders or purchase orders (Phase 7+)
- Supplier portal or self-service (not in scope)
- Tracking pricing per category/fornecedor (future catalog feature)
- CNPJ format validation beyond "14 numeric digits" (no check digit validation at MVP)

## Decisions

### 1. Three separate tables instead of embedding

Contacts are a true one-to-many child resource (a supplier has 0–N contacts, each with their own identity). An array column (JSONB) would be simpler to query but would prevent indexing, foreign key integrity, and future additions (e.g., marking a contact as primary). Categories are many-to-many and must be queryable for filtering — an array column would require unnest tricks to filter efficiently. The association table approach is standard relational design and consistent with how the project already models relationships.

*Alternative considered:* JSONB array for contacts. Rejected — too rigid for a real-world contact list that needs to be updated per-item.

### 2. Fixed enum for categories, stored as string

Categories are domain-specific and change rarely. Using a Python `str` enum (`FornecedorCategoryEnum`) with Pydantic validation keeps the type safe without requiring a separate DB lookup table. The enum values are stored as strings in the `fornecedor_categoria.category` column, which avoids PostgreSQL ENUM type migration friction when adding new values.

*Adding a new category later:* add to the Python enum, add a Pydantic validator note, and update the frontend checkboxes. No DB migration needed for the column itself (it's just a string).

*Alternative considered:* A separate `categoria` table with FK. Rejected at MVP — over-engineered for a short, stable list that does not need its own management UI.

### 3. PATCH replaces the full categories set

When a PATCH request includes a `categories` field, the handler deletes all existing `FornecedorCategoria` rows for that fornecedor and inserts the new set. This is simpler for the frontend (send the desired final state) and avoids the complexity of add/remove delta operations. If `categories` is absent from the PATCH body, categories are left unchanged. This mirrors how the RBAC permissions PUT works.

### 4. Contacts as a sub-resource with their own endpoints

Contacts are managed via `POST /fornecedores/{id}/contatos`, `PATCH /fornecedores/{id}/contatos/{contato_id}`, and `DELETE /fornecedores/{id}/contatos/{contato_id}`. This keeps the main PATCH endpoint clean (no contact mutations in the fornecedor body) and makes it clear that contacts are child resources. The detail GET response always includes the full `contatos` list eagerly loaded.

*Alternative considered:* Include contacts array in the PATCH body (replace-all semantics). Rejected — the UX requires adding/editing/deleting individual contacts inline, which maps better to individual sub-resource endpoints.

### 5. Two permissions: `view_fornecedores` and `manage_fornecedores`

Finance needs read access to look up supplier contacts and categories, but should not be able to create or delete supplier records (that is an admin-level data management concern). Two separate permissions (`view_` and `manage_`) follow the existing pattern from the RBAC phase and allow per-user overrides if needed later.

### 6. `selectinload` on both relationships in all read queries

`Fornecedor.contatos` and `Fornecedor.categorias` are always returned in the API response. Loading them lazily would cause N+1 queries on the list endpoint. Both `get_fornecedores` and `get_fornecedor` must include `selectinload(Fornecedor.contatos)` and `selectinload(Fornecedor.categorias)`. This is consistent with the N+1 rule established in the project conventions.

### 7. CNPJ: optional, stored as 14-digit string, unique when present

CNPJ is optional because some suppliers are individuals (without a company registration). When provided, it is validated as exactly 14 numeric digits (no check digit algorithm — consistent with how CPF/CNPJ are handled for clients). Uniqueness is enforced at the DB level with a partial unique index on non-null values, preventing duplicate supplier registrations.

## Risks / Trade-offs

- **Category enum growth:** If the category list grows significantly, the inline checkbox UI becomes unwieldy. Mitigation: the five MVP categories are sufficient for now; if it grows, move to a scrollable multi-select.
- **No CNPJ check digit validation:** Invalid CNPJs can be saved as long as they are 14 digits. Mitigation: acceptable at MVP; a Pydantic validator using the check digit algorithm can be added later without a migration.
- **Replace-all categories on PATCH:** A race condition could occur if two users edit categories simultaneously. Mitigation: last write wins, which is acceptable for internal admin tools with low concurrent usage.
- **Contacts not linked to users:** Contacts are free-text entries. There is no way to link a contact to a prata-sys user account. Mitigation: this is intentional — suppliers' contacts are external people who do not have system accounts.

## Migration Plan

1. Add `Fornecedor`, `FornecedorContato`, `FornecedorCategoria` models and schemas to `backend/app/models.py`
2. Run `alembic revision --autogenerate -m "add fornecedor tables"` and review
3. Run `alembic upgrade head` in dev
4. Add CRUD functions to `backend/app/crud.py`
5. Create `backend/app/api/routes/fornecedores.py` and register in `backend/app/api/main.py`
6. Add `view_fornecedores` and `manage_fornecedores` to `ALL_PERMISSIONS` and `ROLE_PERMISSIONS` in `backend/app/core/permissions.py`
7. Run `bash ./scripts/generate-client.sh` to regenerate the frontend API client
8. Build frontend list page and detail/form page
9. Add "Fornecedores" to sidebar with `view_fornecedores` guard
10. Write backend tests, run `bash scripts/test.sh`
11. Run `cd frontend && bun run lint && bun run build`

## Open Questions

- Should finance users be allowed to add/edit contacts only (but not create/delete the fornecedor itself)? **Proposed: no for MVP** — keeping it simple with two permissions (view vs. manage all) is sufficient; a third `manage_fornecedor_contatos` permission can be added later if the business requests it.
- Should a unique index on CNPJ be a DB-level partial unique index (ignoring NULLs) or enforced only in application code? **Proposed: DB-level partial unique index** — more reliable, prevents duplicates even from direct DB writes.
- Is `outros` a sufficient catch-all, or should there be a free-text "other" description? **Proposed: `outros` enum value is sufficient for MVP** — if the team needs to distinguish sub-types of `outros`, that signals it should become a proper enum value in a future iteration.
