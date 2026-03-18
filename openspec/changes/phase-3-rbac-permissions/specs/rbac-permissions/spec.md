# RBAC Permissions Spec

## Overview

Replace the current role-based route guards (`require_role`) with a two-tier permission system:

1. **Role defaults** — each role has a baseline set of permissions defined in code
2. **Per-user overrides** — admins can grant additional permissions to individual users via a DB table

Effective permissions = role defaults ∪ user overrides. Route guards check permissions via `require_permission()`, never role names. Superusers bypass all checks.

## Permission Registry

All known permissions with their PT-BR labels:

| Permission | PT-BR Label | Description |
|---|---|---|
| `manage_permissions` | Gerenciar Permissões | Access the Permissions page and modify user permissions |
| `manage_users` | Gerenciar Usuários | Create, update, delete user accounts |
| `manage_clients` | Gerenciar Clientes | Full CRUD on client records |
| `manage_services` | Gerenciar Serviços | Full CRUD on service orders and line items |
| `view_dashboard` | Visualizar Dashboard | Access the main dashboard |
| `view_contas_pagar` | Visualizar Contas a Pagar | Access accounts payable page |
| `view_contas_receber` | Visualizar Contas a Receber | Access accounts receivable page |
| `view_well_status` | Visualizar Status do Poço | View water well status (future client portal) |
| `view_reports` | Visualizar Relatórios | Access financial and operational reports |

## Role Default Permissions

| Role | PT-BR | Default Permissions |
|---|---|---|
| admin | Administrador | `manage_permissions`, `manage_users`, `manage_clients`, `manage_services`, `view_dashboard` |
| finance | Financeiro | `view_dashboard`, `view_contas_pagar`, `view_contas_receber` |
| client | Cliente | *(none)* — admin must explicitly grant permissions |

**Key principle:** Roles provide baseline permissions. Admins can grant any additional permission to any user without changing their role.

**Examples:**
- A `client` user needs to see their well status → admin grants `view_well_status` via the Permissions page
- A `finance` user also manages clients → admin grants `manage_clients` via the Permissions page
- An `admin` user needs to see contas a pagar → admin grants `view_contas_pagar` via the Permissions page

**Superuser bypass:** Users with `is_superuser=True` have all permissions regardless of role or overrides.

## Backend Spec

### `backend/app/core/permissions.py` (new file)

```python
from app.models import UserRole

ALL_PERMISSIONS: dict[str, str] = {
    "manage_permissions": "Gerenciar Permissões",
    "manage_users": "Gerenciar Usuários",
    "manage_clients": "Gerenciar Clientes",
    "manage_services": "Gerenciar Serviços",
    "view_dashboard": "Visualizar Dashboard",
    "view_contas_pagar": "Visualizar Contas a Pagar",
    "view_contas_receber": "Visualizar Contas a Receber",
    "view_well_status": "Visualizar Status do Poço",
    "view_reports": "Visualizar Relatórios",
}

ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.admin: {
        "manage_permissions", "manage_users", "manage_clients",
        "manage_services", "view_dashboard",
    },
    UserRole.finance: {
        "view_dashboard", "view_contas_pagar", "view_contas_receber",
    },
    UserRole.client: set(),
}

def get_role_defaults(role: UserRole) -> set[str]:
    """Return the default permission set for a role."""
    return ROLE_PERMISSIONS.get(role, set())

def get_effective_permissions(session: Session, user: User) -> set[str]:
    """Return role defaults ∪ per-user DB overrides."""
    defaults = get_role_defaults(user.role)
    overrides = {up.permission for up in user.user_permissions}
    return defaults | overrides
```

### `backend/app/models.py` (modified)

New table model:

```python
class UserPermission(SQLModel, table=True):
    __tablename__ = "user_permission"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE", index=True)
    permission: str = Field(max_length=100)

    user: "User" = Relationship(back_populates="user_permissions")
```

Add to `User` model:
```python
user_permissions: list["UserPermission"] = Relationship(
    back_populates="user",
    cascade_delete=True,
)
```

Add to `UserPublic`:
```python
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None
    permissions: list[str] = []
```

**Unique constraint:** `(user_id, permission)` to prevent duplicate grants.

### `backend/app/api/deps.py` (modified)

```python
def require_permission(*permissions: str) -> Any:
    """Dependency factory. Checks that the current user has ALL listed
    permissions (from role defaults + DB overrides). Superusers bypass."""

    def permission_checker(current_user: CurrentUser, session: SessionDep) -> User:
        if current_user.is_superuser:
            return current_user
        effective = get_effective_permissions(session, current_user)
        if not all(p in effective for p in permissions):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return permission_checker
```

- `require_role()` is **removed** (not deprecated — replaced entirely)
- `get_current_active_superuser()` is **removed** — replaced by `require_permission("manage_users")`

### Permissions API routes (`backend/app/api/routes/permissions.py`, new file)

| Endpoint | Method | Guard | Description |
|---|---|---|---|
| `/api/v1/permissions/available` | GET | `require_permission("manage_permissions")` | Returns `ALL_PERMISSIONS` dict (permission → PT-BR label) |
| `/api/v1/permissions/users` | GET | `require_permission("manage_permissions")` | Returns all users with their effective permissions, role defaults, and overrides |
| `/api/v1/permissions/users/{user_id}` | GET | `require_permission("manage_permissions")` | Returns one user's effective permissions, role defaults, and overrides |
| `/api/v1/permissions/users/{user_id}` | PUT | `require_permission("manage_permissions")` | Replaces all permission overrides for a user |

**PUT request body:**
```json
{
  "permissions": ["view_well_status", "manage_clients"]
}
```

**PUT behavior:**
1. Delete all existing `UserPermission` rows for the user
2. Insert new rows for each permission in the request
3. Filter out permissions that are already in the user's role defaults (no need to store redundant overrides)
4. Validate that all permission strings exist in `ALL_PERMISSIONS`

**GET `/permissions/users` response:**
```json
[
  {
    "id": "...",
    "email": "carlos@example.com",
    "full_name": "Carlos Silva",
    "role": "client",
    "is_superuser": false,
    "role_defaults": [],
    "overrides": ["view_well_status", "manage_services"],
    "effective": ["view_well_status", "manage_services"]
  }
]
```

### Route guard migration

| File | Before | After |
|---|---|---|
| `clients.py` | `require_role("admin", "finance")` | `require_permission("manage_clients")` |
| `services.py` | `require_role("admin", "finance")` | `require_permission("manage_services")` |
| `users.py` | `get_current_active_superuser` | `require_permission("manage_users")` |
| `permissions.py` | *(new)* | `require_permission("manage_permissions")` |

### API response changes

All endpoints returning `UserPublic` now include computed `permissions` (effective = role defaults ∪ overrides).

Example for a `finance` user with an override:
```json
{
  "id": "...",
  "email": "maria@example.com",
  "role": "finance",
  "is_superuser": false,
  "permissions": ["view_dashboard", "view_contas_pagar", "view_contas_receber", "manage_clients"]
}
```

## Frontend Spec

### Permissions Page (`/permissions`) — NEW

Route: `frontend/src/routes/_layout/permissions.tsx`

**Layout:** A table/matrix with:
- Rows = users (fetched from `GET /permissions/users`)
- Columns = all available permissions (fetched from `GET /permissions/available`)
- Cells = toggle switches

**Cell states:**
- **Role default (locked):** permission comes from the role — shown as a filled, non-toggleable checkbox with a tooltip "Padrão do perfil {role}"
- **Override (granted):** permission was explicitly granted — shown as a toggleable switch, ON
- **Not granted:** shown as a toggleable switch, OFF

**Behavior:**
- Toggling a switch calls `PUT /permissions/users/{user_id}` with the updated override list
- Superusers are shown with all permissions filled and a label "Acesso total (superusuário)"
- The table should group permissions visually (e.g., "Gestão" section for manage_*, "Visualização" for view_*)

**Access guard:** Only users with `manage_permissions` can access this page. Redirect others to dashboard.

### Admin User Table (`columns.tsx`)

- Replace the "Superuser/User" badge with the actual role name
- Show role as a colored badge: admin → default, finance → secondary, client → outline
- Keep a small superuser indicator (shield icon) when `is_superuser` is true

### Add User Form (`AddUser.tsx`)

Add a `role` select field:

```
[Email]
[Full Name]
[Role: admin ▾]        ← NEW
[Password]
[Confirm Password]
☐ Superuser
☐ Active
```

- Default role: `admin`
- Options: Administrador, Financeiro, Cliente
- Note: when a new user is created, they start with only their role's default permissions. Additional permissions are granted later via the Permissions page.

### Edit User Form (`EditUser.tsx`)

Same as AddUser — add role selector, pre-populated with the user's current role.

**Important:** When a user's role is changed, their permission overrides should be cleared (handled by the backend — the PUT to update user triggers override cleanup).

### Sidebar conditional rendering

Use the `permissions` array from the `/users/me` response:

| Sidebar Link | Required Permission | PT-BR Label |
|---|---|---|
| Dashboard | `view_dashboard` | Dashboard |
| Clientes | `manage_clients` | Clientes |
| Serviços | `manage_services` | Serviços |
| Contas a Pagar | `view_contas_pagar` | Contas a Pagar |
| Contas a Receber | `view_contas_receber` | Contas a Receber |
| Usuários | `manage_users` | Usuários |
| Permissões | `manage_permissions` | Permissões |

Superusers see all links. Links are hidden (not grayed out) if the user lacks the permission.

## Testing Requirements

### Backend unit tests (`test_permissions.py`)

- `test_role_defaults_admin` — admin defaults include `manage_permissions`, `manage_users`, etc.
- `test_role_defaults_finance` — finance defaults include `view_dashboard`, `view_contas_pagar`, `view_contas_receber`
- `test_role_defaults_client` — client defaults are empty
- `test_effective_with_overrides` — user with role=client + override `view_well_status` → effective includes `view_well_status`
- `test_effective_no_duplicate` — role default + same override doesn't duplicate
- `test_all_roles_in_mapping` — every `UserRole` value has an entry in `ROLE_PERMISSIONS`
- `test_all_permissions_valid` — every permission in `ROLE_PERMISSIONS` exists in `ALL_PERMISSIONS`

### Backend API tests (`test_permissions_api.py`)

- `test_get_available_permissions` — returns all permissions with labels
- `test_get_users_permissions` — returns users with role_defaults, overrides, effective
- `test_set_user_overrides` — PUT sets overrides, GET reflects them
- `test_set_overrides_filters_role_defaults` — overrides that match role defaults are not stored
- `test_set_overrides_validates_permissions` — invalid permission string returns 422
- `test_permissions_api_requires_manage_permissions` — finance user gets 403
- `test_permissions_api_superuser_bypass` — superuser can access

### Backend route guard tests

- `test_require_permission_allows_role_default` — admin accesses `manage_clients` endpoint
- `test_require_permission_allows_override` — client with `manage_clients` override accesses endpoint
- `test_require_permission_denies_no_permission` — client without override gets 403
- `test_require_permission_superuser_bypass` — superuser with role=client accesses everything
- `test_user_public_includes_permissions` — API response includes effective permissions

### Frontend tests (Playwright)

- Admin can see and access the Permissions page
- Admin can toggle a permission for a client user
- Client user without permissions sees empty sidebar
- Client user with `manage_clients` override sees "Clientes" sidebar link
- Role default permissions are shown as non-toggleable in the matrix
