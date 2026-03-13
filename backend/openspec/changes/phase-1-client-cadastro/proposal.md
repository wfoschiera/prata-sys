## Why

The system needs to manage client records (individuals and legal entities) as business entities distinct from system users. Without a Client model, the company cannot track drilling contracts, associate jobs with customers, or run financial reports by client — all of which are required for day-to-day operations.

## What Changes

- Introduce a `Client` database model and table supporting both CPF (individual) and CNPJ (company) document types
- Add full CRUD operations for clients via REST API at `/api/v1/clients`
- Restrict client management to `admin` and `finance` roles using the existing `require_role` dependency
- Add an Alembic migration for the new `client` table
- Add a frontend Clients list page with add/edit/delete forms, visible only to `admin` and `finance` users
- Add a Clients entry in the sidebar navigation

## Capabilities

### New Capabilities

- `client-cadastro`: Full lifecycle management of client records (person or company), including CPF/CNPJ validation, CRUD API, role-gated access, and frontend UI

### Modified Capabilities

<!-- No existing spec-level requirements are changing -->

## Impact

- **Backend:** new `Client` SQLModel, new CRUD functions in `backend/app/crud.py`, new router at `backend/app/api/routes/clients.py`, registered in `backend/app/api/main.py`, Alembic migration
- **Frontend:** new route/page under `frontend/src/routes/clients/`, auto-generated API client from OpenAPI, sidebar link added
- **Auth:** reuses existing `require_role` dependency — no auth changes
- **DB:** one new table `client`; no changes to existing tables
