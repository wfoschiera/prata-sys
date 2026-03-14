## 1. Permissions Module

- [ ] 1.1 Create `backend/app/core/permissions.py` with `ALL_PERMISSIONS` dict (permission → PT-BR label) containing all 9 permissions
- [ ] 1.2 Add `ROLE_PERMISSIONS` dict mapping each `UserRole` to its default `set[str]` of permissions (admin: 5, finance: 3, client: empty)
- [ ] 1.3 Implement `get_role_defaults(role: UserRole) -> set[str]`
- [ ] 1.4 Implement `get_effective_permissions(session: Session, user: User) -> set[str]` that returns role defaults ∪ user DB overrides
- [ ] 1.5 Write unit tests: role defaults for each role, effective with overrides, no duplicates, all roles have mapping, all permissions in mapping exist in ALL_PERMISSIONS

## 2. UserPermission Model + Migration

- [ ] 2.1 Add `UserPermission` SQLModel table to `backend/app/models.py` with fields: `id` (UUID PK), `user_id` (FK → user.id, CASCADE, indexed), `permission` (str, max_length=100)
- [ ] 2.2 Add unique constraint on `(user_id, permission)` to prevent duplicate grants
- [ ] 2.3 Add `user_permissions: list[UserPermission]` relationship on `User` model with `cascade_delete=True`
- [ ] 2.4 Add `permissions: list[str] = []` field to `UserPublic` response schema
- [ ] 2.5 Run `alembic revision --autogenerate -m "add user_permission table"` and review the migration
- [ ] 2.6 Run `alembic upgrade head` in dev

## 3. Backend Dependency

- [ ] 3.1 Add `require_permission(*permissions: str)` dependency factory to `backend/app/api/deps.py` — loads user's `user_permissions` relationship, computes effective permissions, checks all required present
- [ ] 3.2 Superuser bypass: `is_superuser=True` passes all permission checks
- [ ] 3.3 Remove `require_role()` from `deps.py`
- [ ] 3.4 Remove `get_current_active_superuser()` from `deps.py` (replaced by `require_permission("manage_users")`)
- [ ] 3.5 Write tests: correct role default allowed, override allowed, wrong role denied, superuser bypass, AND logic for multiple permissions

## 4. Permissions CRUD

- [ ] 4.1 Add `get_user_permissions(session, user_id) -> list[UserPermission]` to `backend/app/crud.py`
- [ ] 4.2 Add `set_user_permissions(session, user_id, permissions: list[str]) -> list[UserPermission]` — deletes existing, inserts new, filters out role defaults, validates against ALL_PERMISSIONS
- [ ] 4.3 Add `clear_user_permissions(session, user_id)` — deletes all overrides (used when role changes)

## 5. Permissions API Routes

- [ ] 5.1 Create `backend/app/api/routes/permissions.py` with router prefix `/permissions`
- [ ] 5.2 `GET /permissions/available` — returns `ALL_PERMISSIONS` dict; requires `manage_permissions`
- [ ] 5.3 `GET /permissions/users` — returns all users with `role_defaults`, `overrides`, `effective` permissions; requires `manage_permissions`; use `selectinload(User.user_permissions)` to prevent N+1
- [ ] 5.4 `GET /permissions/users/{user_id}` — same as above for a single user; 404 if not found
- [ ] 5.5 `PUT /permissions/users/{user_id}` — replaces overrides; validates permission strings; requires `manage_permissions`
- [ ] 5.6 Register the permissions router in `backend/app/api/main.py`
- [ ] 5.7 Write API tests: get available, get users, get single user, set overrides, filter role defaults, invalid permission → 422, auth guard (finance → 403, superuser → 200)

## 6. Route Guard Migration

- [ ] 6.1 Replace `require_role("admin", "finance")` with `require_permission("manage_clients")` in `backend/app/api/routes/clients.py`
- [ ] 6.2 Replace `require_role("admin", "finance")` with `require_permission("manage_services")` in `backend/app/api/routes/services.py`
- [ ] 6.3 Replace `get_current_active_superuser` with `require_permission("manage_users")` in `backend/app/api/routes/users.py`
- [ ] 6.4 Update all user API routes to compute and include `permissions` in `UserPublic` responses
- [ ] 6.5 When a user's role is changed via `PATCH /users/{user_id}`, clear their permission overrides
- [ ] 6.6 Update existing backend tests (`test_clients.py`, `test_services.py`, `test_users.py`, `test_login.py`) to work with permission-based guards

## 7. Frontend: Regenerate API Client

- [ ] 7.1 Run `bash ./scripts/generate-client.sh` to pick up `UserPublic.permissions`, `UserPermission`, and new `/permissions` endpoints

## 8. Frontend: Admin User Table

- [ ] 8.1 Update `frontend/src/components/Admin/columns.tsx` to show user's `role` as a badge (admin → default, finance → secondary, client → outline)
- [ ] 8.2 Add a small superuser shield icon when `is_superuser` is true
- [ ] 8.3 Remove old "Superuser/User" badge logic

## 9. Frontend: Add User Form

- [ ] 9.1 Add a `role` select field to `AddUser.tsx` with options: Administrador, Financeiro, Cliente
- [ ] 9.2 Default role: `admin`
- [ ] 9.3 Zod validation using `z.enum()` with `error:` (not `required_error:`)
- [ ] 9.4 Verify form submits `role` to `POST /api/v1/users/`

## 10. Frontend: Edit User Form

- [ ] 10.1 Add `role` select to `EditUser.tsx`, pre-populated with current role
- [ ] 10.2 Verify form submits `role` to `PATCH /api/v1/users/{user_id}`
- [ ] 10.3 Show a warning when changing role: "Alterar o perfil irá redefinir as permissões personalizadas do usuário"

## 11. Frontend: Permissions Page

- [ ] 11.1 Create route `frontend/src/routes/_layout/permissions.tsx`
- [ ] 11.2 Add `beforeLoad` guard: redirect if user lacks `manage_permissions`
- [ ] 11.3 Fetch `GET /permissions/available` for column headers and `GET /permissions/users` for rows
- [ ] 11.4 Render a matrix table: rows = users, columns = permissions
- [ ] 11.5 Cell rendering: role default → filled non-toggleable checkbox with tooltip "Padrão do perfil"; override → toggleable switch; not granted → toggleable switch (off)
- [ ] 11.6 Superuser rows: all filled, label "Acesso total (superusuário)", non-toggleable
- [ ] 11.7 On toggle, call `PUT /permissions/users/{user_id}` with updated overrides list
- [ ] 11.8 Show success/error toast on save
- [ ] 11.9 Group permissions visually: "Gestão" (manage_*), "Visualização" (view_*)

## 12. Frontend: Sidebar Conditional Rendering

- [ ] 12.1 Read `permissions` from the `/users/me` response (TanStack Query cache)
- [ ] 12.2 Conditionally render sidebar links: Dashboard (`view_dashboard`), Clientes (`manage_clients`), Serviços (`manage_services`), Contas a Pagar (`view_contas_pagar`), Contas a Receber (`view_contas_receber`), Usuários (`manage_users`), Permissões (`manage_permissions`)
- [ ] 12.3 Superusers see all links
- [ ] 12.4 Hidden links are fully hidden (not grayed out)

## 13. Verification

- [ ] 13.1 Run backend tests: `bash scripts/test.sh` — all pass with ≥95% coverage
- [ ] 13.2 Run frontend lint + build: `cd frontend && bun run lint && bun run build`
- [ ] 13.3 Manual test: admin user can access Permissions page and toggle permissions for other users
- [ ] 13.4 Manual test: finance user sees Dashboard + Contas a Pagar + Contas a Receber; cannot access Permissions or Admin
- [ ] 13.5 Manual test: client user sees empty sidebar; admin grants `view_well_status` → client sees well status link
- [ ] 13.6 Manual test: change user's role → overrides are cleared
- [ ] 13.7 Manual test: superuser with `role=client` sees all sidebar links and can access everything
