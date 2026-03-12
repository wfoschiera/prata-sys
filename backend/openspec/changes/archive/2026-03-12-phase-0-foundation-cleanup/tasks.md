## 1. Remove Item from backend

- [x] 1.1 Delete `Item`, `ItemCreate`, `ItemUpdate`, `ItemPublic`, `ItemsPublic` models and schemas from `backend/app/models.py`
- [x] 1.2 Delete `create_item` and any other Item CRUD functions from `backend/app/crud.py`
- [x] 1.3 Delete `backend/app/api/routes/items.py`
- [x] 1.4 Remove items router registration from `backend/app/main.py`

## 2. Add role field to User

- [x] 2.1 Add `UserRole` enum (`admin`, `finance`, `client`) to `backend/app/models.py`
- [x] 2.2 Add `role: UserRole` field to `User` model with default `admin`
- [x] 2.3 Add `role` to `UserCreate`, `UserUpdate`, `UserPublic` schemas as appropriate
- [x] 2.4 Generate Alembic migration: `alembic revision --autogenerate -m "add role to user"`
- [x] 2.5 Review generated migration, then apply: `alembic upgrade head`

## 3. Add role-checking dependency

- [x] 3.1 Add `require_role(*roles)` dependency to `backend/app/api/deps.py` — superusers bypass role checks

## 4. Remove Item from frontend

- [x] 4.1 Delete `frontend/src/routes/_layout/items.tsx`
- [x] 4.2 Delete `frontend/src/components/Items/` directory
- [x] 4.3 Remove items link from sidebar (`frontend/src/components/ui/sidebar` or `AppSidebar`)

## 5. Regenerate client and verify

- [x] 5.1 Regenerate OpenAPI client: `bash scripts/generate-client.sh`
- [x] 5.2 Run backend tests: `bash scripts/test.sh`
- [x] 5.3 Verify frontend builds without errors: `cd frontend && bun run build`
