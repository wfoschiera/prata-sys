## Context

The system already has a `User` model with `UserRole` enum (admin, finance, client) and a `require_role` dependency. Clients are business entities that receive drilling services — they are distinct from system users who log in. A client may be an individual (CPF) or a company (CNPJ). The backend follows a standard pattern: SQLModel table classes in `models.py`, CRUD helpers in `crud.py`, and FastAPI routers in `api/routes/`. The frontend uses TanStack Router file-based routing and auto-generates API client code from the OpenAPI spec.

## Goals / Non-Goals

**Goals:**
- Introduce a `Client` table and model in the existing SQLModel/PostgreSQL stack
- Expose full CRUD at `/api/v1/clients` gated to `admin` and `finance` roles
- Generate an Alembic migration for the new table
- Provide a frontend list + form UI under a `/clients` route
- Reuse all existing patterns (crud.py helpers, require_role, auto-generated API client)

**Non-Goals:**
- Linking clients to drilling jobs or contracts (future phase)
- Authenticating as a client (the `client` UserRole is a separate concern)
- Advanced address handling (city/state breakdown) — plain string for now
- Duplicate document-number detection across soft-deleted records
- Bulk import or export of clients

## Decisions

### D1: `Client` is a standalone table, not a subtype of `User`

**Decision:** Create a new `client` table with its own primary key (UUID), not a foreign key into `user`.

**Rationale:** Clients are business entities managed by staff. They do not log in. Merging them with `User` would pollute the auth model and complicate role logic. A clean separation also makes it straightforward to link a client to a `User` account later if self-service access is ever needed.

**Alternative considered:** Add a `client_profile` FK on `User` — rejected because it forces a user account to exist for every client, which is not the case.

### D2: Document type stored as an enum column; document number as a plain string

**Decision:** Use a `DocumentType` string enum (`cpf` / `cnpj`) and store `document_number` as `VARCHAR(14)` (max CNPJ length). Validation (digit count, format) happens in Pydantic schemas, not at the DB level.

**Rationale:** DB-level check constraints for CPF/CNPJ format are fragile to migrate and add no benefit over Pydantic validation which already runs on every request. Storing the raw digits (no punctuation) keeps queries simple.

**Alternative considered:** Store formatted string with punctuation — rejected because it complicates equality checks and indexing.

### D3: Unique index on `document_number`

**Decision:** Add a unique constraint on `document_number` at the DB level.

**Rationale:** Two clients with the same CPF/CNPJ is a data integrity error, not a business rule that ever needs to be bypassed. A DB-level unique constraint is the safest enforcement point.

### D4: Follow existing CRUD pattern — no service layer

**Decision:** CRUD functions go directly in `crud.py` (same pattern as users), with no intermediate service class.

**Rationale:** The codebase has no service layer; introducing one for a single resource would be inconsistent and add unnecessary abstraction.

### D5: Frontend uses auto-generated API client only

**Decision:** Never hand-write fetch/axios calls. All API calls use the auto-generated client from the OpenAPI spec.

**Rationale:** Maintains a single source of truth for API shape and avoids drift between frontend and backend.

## Risks / Trade-offs

- **Unique constraint on `document_number` blocks soft-delete re-registration** → If soft-delete is added later, the unique index must be partial (`WHERE deleted_at IS NULL`). Document this as a known follow-up.
- **Plain address string is too coarse for geo queries** → Accepted for Phase 1; a structured address model is a future enhancement.
- **CNPJ/CPF validation in Pydantic only** → An invalid document number stored via a direct DB insert would pass silently. Acceptable since all writes go through the API.

## Migration Plan

1. Run `alembic revision --autogenerate -m "add client table"` after adding the `Client` model
2. Review generated migration for correctness (enum type creation, unique constraint)
3. Run `alembic upgrade head` on staging, verify table creation
4. Deploy backend, regenerate frontend API client (`openapi-ts` or equivalent)
5. Deploy frontend
6. Rollback: `alembic downgrade -1` drops the table; no data migration needed for rollback in Phase 1

## Open Questions

- Should `phone` be stored as a plain string or validated (e.g., Brazilian mobile format)? → Assume plain string for Phase 1, consistent with `address`.
- Is `email` required for a client? → No — some clients may communicate only by phone. Make it optional.
