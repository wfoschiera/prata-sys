## Why

The current system has a simple `UserRole` enum (admin, finance, client) and a `require_role()` dependency, but no granular permissions. This creates three problems:

1. **The frontend admin panel ignores roles** — Add/Edit user forms only expose `is_superuser`, making it impossible to assign roles through the UI.
2. **Roles are hardcoded in route guards** — every endpoint checks role names directly (`require_role("admin", "finance")`). Adding features or roles requires changing code in every route file.
3. **No per-user flexibility** — a `client` user who needs access to view services cannot get it without changing their role entirely. An admin must be able to grant or revoke individual permissions per user.

Without this change, every new feature (client portal, reports, contas a pagar/receber) requires hardcoding role names into route guards and redeploying.

## What Changes

- Introduce a **permissions system** with two layers:
  - **Role defaults:** each role comes with a default set of permissions defined in code (e.g., `admin` gets everything, `client` gets nothing by default, `finance` gets dashboard + contas a pagar + contas a receber)
  - **Per-user overrides:** admins can grant additional permissions to any specific user, stored in a `user_permission` DB table
- Create a **Permissions management page** (`/permissions`) accessible only to users with `manage_permissions` — shows a user × permission matrix with toggles
- Replace `require_role()` with `require_permission()` throughout the backend — route guards check permissions, never role names
- Keep `is_superuser` as a global bypass flag
- Expose the **effective permissions** (role defaults ∪ user overrides) in the API response

## Capabilities

### New Capabilities

- `rbac-permissions`: Permission-based access control with role defaults, per-user DB overrides, `require_permission()` dependency
- `permissions-page`: Admin-only UI page to view and edit permissions per user — matrix of users × permissions with toggles

### Modified Capabilities

- `user-management`: Admin forms gain a role selector dropdown; user table displays role badge
- `client-cadastro`: Route guards migrate from `require_role` to `require_permission`
- `servicos`: Route guards migrate from `require_role` to `require_permission`

## Impact

- **Backend:** new `permissions.py` module (role defaults + effective permissions); new `UserPermission` SQLModel table; new `require_permission()` dependency; new `/api/v1/permissions` routes; updated guards in `clients.py`, `services.py`, `users.py`
- **Frontend:** new Permissions page (`/permissions`); updated AddUser/EditUser forms with role selector; sidebar conditional rendering based on effective permissions; regenerated API client
- **Auth:** `is_superuser` remains as bypass; all role-based logic replaced by permission checks
- **DB:** new `user_permission` table (user_id FK, permission string, granted bool); Alembic migration required
