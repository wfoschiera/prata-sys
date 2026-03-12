## Why

The project is being repurposed from the generic FastAPI template into a domain-specific water well drilling management system. The template's placeholder `Item` model is irrelevant to this domain and adds noise, and the existing `User` model lacks business-level role control needed to differentiate `admin`, `finance`, and `client` users.

## What Changes

- **BREAKING** Remove `Item` model, CRUD functions, and API routes (`/api/v1/items`)
- **BREAKING** Remove `Item`-related frontend page, components, and sidebar link
- Add `role` field (`admin`, `finance`, `client`) to the `User` model — keeps `is_superuser` for dev/system access
- Add Alembic migration for the new `role` column
- Add role-checking dependency functions for route protection (`require_role`)
- Regenerate OpenAPI frontend client after backend changes

## Capabilities

### New Capabilities
- `user-roles`: Business-level role field on User model with role-checking route dependencies

### Modified Capabilities
- (none)

## Impact

- `backend/app/models.py`: Remove Item models/schemas, add `role` field to User
- `backend/app/crud.py`: Remove item CRUD functions
- `backend/app/api/routes/items.py`: Delete file
- `backend/app/api/deps.py`: Add `require_role` dependency
- `backend/app/main.py`: Remove items router registration
- `backend/alembic/versions/`: New migration for `role` column
- `frontend/src/routes/_layout/items.tsx`: Delete file
- `frontend/src/components/Items/`: Delete directory
- `frontend/src/client/`: Regenerate after backend changes
