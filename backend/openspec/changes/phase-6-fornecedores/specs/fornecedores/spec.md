# Fornecedores Spec

## Overview

Introduce supplier management ("fornecedores") to the system. A fornecedor represents a company or individual that supplies materials or services used in water well drilling operations. Each fornecedor has:

- Core identity: company name, optional CNPJ, optional address, notes
- Multiple contacts: each with name, telefone, optional whatsapp, and a short description
- Product category associations: a many-to-many link to a fixed set of categories (`tubos`, `conexoes`, `bombas`, `cabos`, `outros`)

Read access is granted to `admin` and `finance` roles. Write access (create, update, delete) is restricted to `admin` only.

---

## Domain Rules

- **CNPJ** is optional (some suppliers are individuals). When provided, it must be exactly 14 numeric digits (stored as a plain string, validated in Pydantic schema).
- **address** is a free-text optional string — no structured CEP/street breakdown at MVP stage.
- **notes** is free text for anything that doesn't fit elsewhere (e.g., "fornece apenas para SP", "prazo de entrega 15 dias").
- A fornecedor with no contacts and no categories is valid.
- Deleting a fornecedor **cascades** to all its contacts and category associations.
- A category association is either present or absent — there is no quantity or date on it.
- The category enum is defined in code. Adding a new category requires a code change and a migration to update the enum type.

---

## Data Model

### `Fornecedor` table

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | `default_factory=uuid.uuid4` |
| `company_name` | str | max 255, required, indexed for search |
| `cnpj` | str \| None | 14 digits, unique when provided |
| `address` | str \| None | free text, optional |
| `notes` | str \| None | free text, optional |

### `FornecedorContato` table

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | `default_factory=uuid.uuid4` |
| `fornecedor_id` | UUID FK → fornecedor.id | CASCADE, indexed |
| `name` | str | max 255, required |
| `telefone` | str | max 20, required |
| `whatsapp` | str \| None | max 20, optional |
| `description` | str | max 100, e.g. "vendedor", "proprietário", "atendente" |

### `FornecedorCategoria` association table

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | `default_factory=uuid.uuid4` |
| `fornecedor_id` | UUID FK → fornecedor.id | CASCADE, indexed |
| `category` | str (enum values) | one of: `tubos`, `conexoes`, `bombas`, `cabos`, `outros` |

Unique constraint on `(fornecedor_id, category)` — a fornecedor cannot be assigned the same category twice.

### Category enum

```python
class FornecedorCategoryEnum(str, Enum):
    tubos = "tubos"
    conexoes = "conexoes"
    bombas = "bombas"
    cabos = "cabos"
    outros = "outros"
```

---

## Pydantic Schemas

### `FornecedorBase`

```python
class FornecedorBase(SQLModel):
    company_name: str = Field(min_length=1, max_length=255)
    cnpj: str | None = Field(default=None)          # validated: 14 numeric digits
    address: str | None = Field(default=None)
    notes: str | None = Field(default=None)
```

CNPJ validation: if provided, must match `^\d{14}$`. Return 422 otherwise.

### `FornecedorCreate` / `FornecedorUpdate`

- `FornecedorCreate(FornecedorBase)` — all fields from base; `categories: list[FornecedorCategoryEnum] = []`
- `FornecedorUpdate(FornecedorBase)` — same as Create, all fields optional (`| None` defaults)

### `FornecedorContatoBase`

```python
class FornecedorContatoBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    telefone: str = Field(min_length=1, max_length=20)
    whatsapp: str | None = Field(default=None, max_length=20)
    description: str = Field(min_length=1, max_length=100)
```

### `FornecedorContatoCreate` / `FornecedorContatoUpdate`

- `FornecedorContatoCreate(FornecedorContatoBase)` — no extra fields; `fornecedor_id` comes from path param
- `FornecedorContatoUpdate(FornecedorContatoBase)` — all fields optional

### `FornecedorPublic` (API response)

```python
class FornecedorPublic(FornecedorBase):
    id: uuid.UUID
    categories: list[FornecedorCategoryEnum]
    contatos: list[FornecedorContatoPublic]
```

The list endpoint returns `FornecedorPublic` with `contatos` and `categories` eagerly loaded (no N+1).

### `FornecedorContatoPublic`

```python
class FornecedorContatoPublic(FornecedorContatoBase):
    id: uuid.UUID
    fornecedor_id: uuid.UUID
```

---

## Backend API

### Fornecedores router — `backend/app/api/routes/fornecedores.py`

All routes under prefix `/api/v1/fornecedores`.

| Endpoint | Method | Guard | Description |
|---|---|---|---|
| `/fornecedores` | GET | `require_permission("view_fornecedores")` | List all fornecedores with contatos and categories; supports `?search=` (name) and `?category=` filter |
| `/fornecedores` | POST | `require_permission("manage_fornecedores")` | Create fornecedor; accepts categories list in body |
| `/fornecedores/{id}` | GET | `require_permission("view_fornecedores")` | Get single fornecedor with contatos and categories |
| `/fornecedores/{id}` | PATCH | `require_permission("manage_fornecedores")` | Update fornecedor fields and/or replace categories list |
| `/fornecedores/{id}` | DELETE | `require_permission("manage_fornecedores")` | Delete fornecedor (cascades to contatos and categories) |
| `/fornecedores/{id}/contatos` | POST | `require_permission("manage_fornecedores")` | Add a contact to a fornecedor |
| `/fornecedores/{id}/contatos/{contato_id}` | PATCH | `require_permission("manage_fornecedores")` | Update a contact |
| `/fornecedores/{id}/contatos/{contato_id}` | DELETE | `require_permission("manage_fornecedores")` | Remove a contact |

**Query parameters for `GET /fornecedores`:**
- `search` (optional string): case-insensitive match against `company_name`
- `category` (optional `FornecedorCategoryEnum`): filter to fornecedores that have this category

Both filters can be combined. Returns `list[FornecedorPublic]`.

**PATCH categories behavior:** When `categories` is included in a PATCH body, it **replaces** the full set of category associations (delete existing, insert new). If `categories` is omitted from the PATCH, categories are unchanged.

**Error cases:**
- 404 if fornecedor not found
- 404 if contato not found or does not belong to fornecedor
- 422 if CNPJ provided but not 14 digits
- 409 if CNPJ already exists for another fornecedor

### CRUD functions — `backend/app/crud.py`

```python
def get_fornecedores(
    session: Session,
    search: str | None = None,
    category: FornecedorCategoryEnum | None = None,
) -> list[Fornecedor]: ...

def get_fornecedor(session: Session, fornecedor_id: uuid.UUID) -> Fornecedor | None: ...

def create_fornecedor(session: Session, data: FornecedorCreate) -> Fornecedor: ...

def update_fornecedor(
    session: Session, fornecedor: Fornecedor, data: FornecedorUpdate
) -> Fornecedor: ...

def delete_fornecedor(session: Session, fornecedor: Fornecedor) -> None: ...

def create_contato(
    session: Session, fornecedor_id: uuid.UUID, data: FornecedorContatoCreate
) -> FornecedorContato: ...

def update_contato(
    session: Session, contato: FornecedorContato, data: FornecedorContatoUpdate
) -> FornecedorContato: ...

def delete_contato(session: Session, contato: FornecedorContato) -> None: ...
```

**N+1 prevention:** `get_fornecedores` and `get_fornecedor` must use `selectinload(Fornecedor.contatos)` and `selectinload(Fornecedor.categorias)` to avoid lazy-load on iteration.

---

## Permissions Changes

Add to `ALL_PERMISSIONS` in `backend/app/core/permissions.py`:

| Permission | PT-BR Label | Description |
|---|---|---|
| `view_fornecedores` | Visualizar Fornecedores | Read access to supplier list and detail |
| `manage_fornecedores` | Gerenciar Fornecedores | Full CRUD on suppliers and contacts |

Update `ROLE_PERMISSIONS`:

| Role | New Permissions Added |
|---|---|
| admin | `view_fornecedores`, `manage_fornecedores` |
| finance | `view_fornecedores` |
| client | *(none)* |

---

## Frontend Spec

### Fornecedores List Page — `/fornecedores`

Route: `frontend/src/routes/_layout/fornecedores/index.tsx`

**Access guard:** redirect to dashboard if user lacks `view_fornecedores`.

**Layout:**
- Page title "Fornecedores"
- Search input: filters by company name (client-side or triggers API call with `?search=`)
- Category filter: multi-select or pill buttons for `tubos`, `conexoes`, `bombas`, `cabos`, `outros` — triggers `?category=` API filter
- "Novo Fornecedor" button (visible only if user has `manage_fornecedores`)
- Table or card list showing: company name, CNPJ (or "—" if absent), categories as badges, number of contacts
- Click row → navigate to detail page

**Empty state:** "Nenhum fornecedor cadastrado." with a CTA to create one (if permitted).

### Fornecedor Detail / Form Page — `/fornecedores/$fornecedorId` and `/fornecedores/new`

Route: `frontend/src/routes/_layout/fornecedores/$fornecedorId.tsx`

**Tabs or sections:**
1. **Dados da empresa** — company name, CNPJ, address, notes; Edit/Save buttons (only if `manage_fornecedores`)
2. **Categorias** — checkboxes for each category value; Save on change
3. **Contatos** — sub-table listing all contacts with inline Add/Edit/Delete

**Contacts sub-table:**
- Columns: name, description, telefone, whatsapp (or "—"), actions
- "Adicionar contato" button opens an inline form row or a dialog
- Edit: click pencil icon → inline edit or dialog
- Delete: click trash icon → confirm, then call DELETE endpoint
- Require `manage_fornecedores` to show add/edit/delete controls

**Delete fornecedor:**
- "Excluir fornecedor" button at bottom (only if `manage_fornecedores`)
- Confirmation dialog: "Isso irá excluir o fornecedor e todos os contatos associados. Deseja continuar?"
- On confirm: call DELETE, redirect to `/fornecedores`

### Sidebar

Add "Fornecedores" link to sidebar, required permission `view_fornecedores`, PT-BR label "Fornecedores".

---

## Testing Requirements

### Backend unit tests (`test_fornecedores.py`)

- `test_create_fornecedor` — creates fornecedor, returns it with empty contatos and categories
- `test_create_fornecedor_with_categories` — categories are stored and returned
- `test_create_fornecedor_duplicate_cnpj` — returns 409
- `test_create_fornecedor_invalid_cnpj` — returns 422
- `test_get_fornecedores_search` — search by name returns matching, excludes non-matching
- `test_get_fornecedores_category_filter` — filter by category returns only matching
- `test_update_fornecedor_replaces_categories` — PATCH with new categories replaces old ones
- `test_update_fornecedor_no_categories_key` — PATCH without categories key leaves categories unchanged
- `test_delete_fornecedor_cascades` — delete removes contatos and categories
- `test_create_contato` — adds contact, returned in fornecedor detail
- `test_update_contato` — updates fields
- `test_delete_contato` — removes contact, not present in detail
- `test_contato_not_found` — 404 if contato_id does not belong to the fornecedor

### Backend permission tests

- `test_finance_can_read_fornecedores` — GET returns 200 for finance role
- `test_finance_cannot_write_fornecedores` — POST returns 403 for finance role
- `test_client_cannot_read_fornecedores` — GET returns 403 for client role
- `test_admin_full_access` — admin can create, update, delete
- `test_superuser_bypass` — superuser with role=client can access all fornecedor endpoints

### Frontend tests (Playwright)

- Admin sees "Fornecedores" in sidebar and can navigate to the list page
- Admin can create a new fornecedor with at least one contact and two categories
- Finance user can see the list but "Novo Fornecedor" button is not visible
- Admin can delete a contact inline without deleting the fornecedor
- Admin can delete a fornecedor; confirmation dialog appears; fornecedor is removed from list
