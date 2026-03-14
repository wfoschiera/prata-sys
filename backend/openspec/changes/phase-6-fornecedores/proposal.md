## Why

The system currently has no way to track suppliers ("fornecedores"). When a service order requires materials (tubes, pumps, connections, cables), the team has no structured place to record which companies supply them, how to reach them, or what categories of goods they provide. This information lives in notebooks, group chats, and memory.

Without a fornecedores module, three problems compound:

1. **Contact lookup is slow and error-prone** — field teams ask other people for a supplier's phone number instead of checking a single source of truth.
2. **Category-based search is impossible** — there is no way to quickly find "which suppliers carry bombas?" without asking someone who knows from memory.
3. **Finance is blocked on future features** — contas a pagar and outgoing purchase orders (planned for Phase 7+) require a structured supplier reference to attach payments to.

## What Changes

- Introduce a **Fornecedores** section: CRUD for supplier companies with optional CNPJ, optional address, and free-text notes
- Each fornecedor can have **multiple contacts** (name, telefone, whatsapp, role description) managed as a sub-resource
- Each fornecedor is linked to one or more **product categories** via an association table using a fixed enum (`tubos`, `conexoes`, `bombas`, `cabos`, `outros`)
- Frontend gains a **Fornecedores list page** with search by name or category, and a **detail/form page** with inline contact management and category checkboxes
- Permissions: read access for `admin` and `finance`; write access for `admin` only

## Capabilities

### New Capabilities

- `fornecedores-crud`: Full CRUD on supplier records — company name, optional CNPJ (14-digit string), optional address, notes
- `fornecedor-contatos`: Sub-resource CRUD for contacts per fornecedor — name, telefone, optional whatsapp, description (e.g., "vendedor", "proprietário")
- `fornecedor-categorias`: Many-to-many association between a fornecedor and product categories (`tubos`, `conexoes`, `bombas`, `cabos`, `outros`) — stored in a separate association table
- `fornecedores-page`: Frontend list page at `/fornecedores` with search by name and filter by category
- `fornecedor-detail-page`: Frontend detail/form page with company info, contacts sub-table (add/edit/remove inline), and category checkboxes; delete with cascade confirmation

### Modified Capabilities

- `rbac-permissions`: Add `manage_fornecedores` and `view_fornecedores` to `ALL_PERMISSIONS`; add `manage_fornecedores` + `view_fornecedores` to admin role defaults; add `view_fornecedores` to finance role defaults; add "Fornecedores" link to sidebar

## Impact

- **Backend:** new `Fornecedor`, `FornecedorContato`, `FornecedorCategoria` SQLModel tables in `models.py`; new CRUD functions in `crud.py`; new router `backend/app/api/routes/fornecedores.py` at `/api/v1/fornecedores`; new Alembic migration
- **Frontend:** new page `frontend/src/routes/_layout/fornecedores/index.tsx` (list) and `frontend/src/routes/_layout/fornecedores/$fornecedorId.tsx` (detail/form); sidebar link added; regenerated API client
- **Permissions:** two new permission strings added to `ALL_PERMISSIONS` and role defaults in `permissions.py`
- **DB:** three new tables — `fornecedor`, `fornecedor_contato`, `fornecedor_categoria`; Alembic migration required; cascade delete from fornecedor → contatos and categorias
