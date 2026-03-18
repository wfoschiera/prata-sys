## Context

The application has three roles (`admin`, `finance`, `client`) stored as a `UserRole` enum on the `User` model. Route protection uses `require_role("admin", "finance")`, which checks the role directly. The frontend admin panel does not expose the role field at all — users can only toggle `is_superuser`.

This design introduces a **permissions layer** with two tiers:

1. **Role defaults** — each role has a default permission set defined in code (the baseline)
2. **Per-user overrides** — admins can grant additional permissions to individual users via a DB table and a dedicated Permissions page

This is inspired by Django-role-permissions but goes further: roles are templates, not ceilings. A `client` user starts with no permissions, but an admin can grant them `view_services` or `view_well_status` through the UI.

## Goals / Non-Goals

**Goals:**
- Define role default permissions in code (`permissions.py`) — the baseline for each role
- Store per-user permission grants in a `user_permission` DB table
- Compute **effective permissions** as: `role_defaults ∪ user_grants`
- Create a `require_permission()` FastAPI dependency that replaces `require_role()`
- Build a **Permissions page** (`/permissions`) where admins manage user permissions via a matrix UI
- Expose effective permissions in the API response so the frontend renders conditionally
- Add role selector to the admin Add/Edit user forms
- Prepare for future roles and pages without modifying route guards

**Non-Goals:**
- Multi-role per user (each user has exactly one role)
- Permission "deny" overrides (overrides can only grant, not revoke role defaults)
- Group-based permissions (no "permission groups" — roles serve that purpose)
- Self-service permission requests (only admins manage permissions)

## Decisions

### 1. Two-tier permission model: role defaults + user overrides

**Role defaults** live in `backend/app/core/permissions.py` as a Python dict:

```python
ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.admin: {
        "manage_permissions",
        "manage_users",
        "manage_clients",
        "manage_services",
        "view_dashboard",
    },
    UserRole.finance: {
        "view_dashboard",
        "view_contas_pagar",
        "view_contas_receber",
    },
    UserRole.client: set(),  # no permissions by default — admin must grant
}
```

**Per-user overrides** are stored in a `user_permission` table:

```python
class UserPermission(SQLModel, table=True):
    __tablename__ = "user_permission"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    permission: str = Field(max_length=100)
```

**Effective permissions** = `ROLE_PERMISSIONS[user.role] ∪ {up.permission for up in user.user_permissions}`

*Why code defaults + DB overrides:* Role defaults should be version-controlled and deploy with code (like Django-role-permissions). Per-user overrides need to be admin-editable at runtime without code changes. This hybrid gives both benefits.

*Alternative considered:* All permissions in DB (no code defaults). Rejected — new deployments would start with empty permissions, requiring manual setup. Code defaults guarantee a working baseline.

### 2. Permission registry: all known permissions

A single `ALL_PERMISSIONS` dict in `permissions.py` serves as the registry. The Permissions page reads this to know what toggles to show:

```python
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
```

Adding a new permission = add one entry here + optionally add it to a role's defaults. No migration, no DB change.

### 3. `require_permission()` dependency

```python
def require_permission(*permissions: str) -> Any:
    def permission_checker(
        current_user: CurrentUser, session: SessionDep
    ) -> User:
        if current_user.is_superuser:
            return current_user
        effective = get_effective_permissions(session, current_user)
        if not all(p in effective for p in permissions):
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return permission_checker
```

Key differences from the old `require_role`:
- Checks **permissions**, not role names — routes never reference roles
- Queries the DB for user overrides (single query, cached per request)
- Superuser bypass remains
- AND logic: all listed permissions must be present

### 4. Permissions API (`/api/v1/permissions`)

| Endpoint | Method | Permission Required | Description |
|---|---|---|---|
| `/permissions` | GET | `manage_permissions` | List all users with their effective permissions |
| `/permissions/{user_id}` | GET | `manage_permissions` | Get a single user's effective permissions + which are from role vs. override |
| `/permissions/{user_id}` | PUT | `manage_permissions` | Set user's permission overrides (replaces all overrides) |
| `/permissions/available` | GET | `manage_permissions` | List all available permissions with labels |

The PUT endpoint receives a list of permission strings to grant as overrides. It replaces all existing overrides for that user (idempotent).

### 5. Keep `is_superuser` separate from roles

`is_superuser` is an orthogonal flag, not a role. A user can be `role=finance` AND `is_superuser=True`. Superusers bypass all permission checks. This mirrors Django's `User.is_superuser`.

### 6. Frontend Permissions page

A new route `/permissions` renders a matrix:

```
              | Dashboard | Clientes | Serviços | Contas Pagar | Contas Receber | ...
─────────────┼───────────┼──────────┼──────────┼──────────────┼────────────────┼────
João (admin) | ■ ●       | ■ ●      | ■ ●      | □            | □              |
Maria (fin.) | ■ ●       | □        | □        | ■ ●          | ■ ●            |
Carlos (cli.)| □ ◉       | □        | □ ◉      | □            | □              |
```

- `■ ●` = from role default (shown but not toggleable — it's the baseline)
- `□ ◉` = user override (granted by admin, toggleable)
- `□` = not granted (toggleable to add)

When a toggle is flipped, it calls `PUT /permissions/{user_id}` with the updated override set.

### 7. Role defaults for each role (Brazilian labels)

| Role | PT-BR | Default Permissions |
|---|---|---|
| admin | Administrador | `manage_permissions`, `manage_users`, `manage_clients`, `manage_services`, `view_dashboard` |
| finance | Financeiro | `view_dashboard`, `view_contas_pagar`, `view_contas_receber` |
| client | Cliente | *(none — admin must grant)* |

### 8. Sidebar conditional rendering

The sidebar reads the user's effective permissions from the `/users/me` response:

| Sidebar Link | Required Permission | PT-BR Label |
|---|---|---|
| Dashboard | `view_dashboard` | Dashboard |
| Clientes | `manage_clients` | Clientes |
| Serviços | `manage_services` | Serviços |
| Contas a Pagar | `view_contas_pagar` | Contas a Pagar |
| Contas a Receber | `view_contas_receber` | Contas a Receber |
| Admin (Usuários) | `manage_users` | Usuários |
| Permissões | `manage_permissions` | Permissões |

Superusers see all links.

## Risks / Trade-offs

- **DB query per request** — `get_effective_permissions` queries `user_permission` on every protected request. Mitigation: single indexed query by `user_id`; can add per-request caching later if needed.
- **Override-only grants (no deny)** — an admin cannot remove a role-default permission from a specific user without changing their role. Mitigation: keeps the model simple; if deny is needed later, add a `granted: bool` column.
- **Single role per user** — a user who needs both `finance` and `admin` defaults must be `admin` with no overrides, or `finance` with overrides. Mitigation: overrides make this workable without multi-role.
- **Frontend permission checks are advisory** — the frontend hides UI but cannot enforce access. All enforcement is server-side via `require_permission()`.

## Migration Plan

1. Create `backend/app/core/permissions.py` with `ALL_PERMISSIONS`, `ROLE_PERMISSIONS`, and `get_effective_permissions()`
2. Add `UserPermission` model to `models.py` + Alembic migration
3. Add `require_permission()` to `deps.py`
4. Add `/api/v1/permissions` routes
5. Migrate route guards in `clients.py`, `services.py`, `users.py`
6. Remove `require_role()` from `deps.py`
7. Update frontend: Add/Edit user forms, user table, sidebar
8. Build Permissions page
9. Regenerate API client
10. Add/update backend tests

## Open Questions

- Should changing a user's role automatically clear their overrides? **Proposed: yes** — if you change someone from `client` to `finance`, their old overrides (which were granted to compensate for the `client` baseline) are likely stale.
- Should the Permissions page show superusers? **Proposed: show them but mark as "full access"** — they bypass all checks, so toggles are informational only.
