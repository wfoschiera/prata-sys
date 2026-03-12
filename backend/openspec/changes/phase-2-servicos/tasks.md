## 1. Database Models

- [x] 1.1 Add `ServiceType` string enum (`perfuração`, `reparo`) to `backend/app/models.py`
- [x] 1.2 Add `ServiceStatus` string enum (`requested`, `scheduled`, `executing`, `completed`) to `backend/app/models.py`
- [x] 1.3 Add `ItemType` string enum (`material`, `serviço`) to `backend/app/models.py`
- [x] 1.4 Define `Service` SQLModel table with fields: `id`, `client_id` (FK → `client.id`), `type` (ServiceType), `status` (ServiceStatus, default `requested`), `execution_address` (String, not null), `notes` (optional Text), `created_at`, `updated_at`
- [x] 1.5 Define `ServiceItem` SQLModel table with fields: `id`, `service_id` (FK → `service.id`, cascade delete), `item_type` (ItemType), `description` (String, not null), `quantity` (Float, > 0), `unit_price` (Float, >= 0)
- [x] 1.6 Add `items` relationship on `Service` (one-to-many to `ServiceItem`, cascade="all, delete-orphan")
- [x] 1.7 Add `client` relationship on `Service` (many-to-one to `Client`)

## 2. Alembic Migration

- [x] 2.1 Run `alembic revision --autogenerate -m "add service and service_item tables"` and verify the generated file creates both tables with correct FK constraints
- [x] 2.2 Confirm `service_item.service_id` FK has `ondelete="CASCADE"` in the migration
- [ ] 2.3 Run `alembic upgrade head` in the development environment and verify no errors

## 3. Backend Schemas

- [x] 3.1 Add `ServiceItemCreate` / `ServiceItemRead` Pydantic schemas to `backend/app/schemas.py` (or models if colocated)
- [x] 3.2 Add `ServiceCreate` schema with `client_id`, `type`, `execution_address`, `notes`; validate `type` against `ServiceType` enum
- [x] 3.3 Add `ServiceRead` schema embedding `ServiceItemRead` list and client reference (id + name minimum)
- [x] 3.4 Add `ServiceUpdate` schema with optional fields for `type`, `status`, `execution_address`, `notes`; include status transition validation logic

## 4. Backend CRUD

- [x] 4.1 Add `create_service(db, service_in: ServiceCreate) -> Service` in `backend/app/crud.py`
- [x] 4.2 Add `get_service(db, service_id) -> Service | None` with `selectinload(Service.client)` and `selectinload(Service.items)` to prevent N+1
- [x] 4.3 Add `get_services(db) -> list[Service]` with `selectinload(Service.client)` and `selectinload(Service.items)` — N+1 guard is critical here
- [x] 4.4 Add `update_service(db, service, service_in: ServiceUpdate) -> Service` with status transition validation (rejected transitions return `ValueError`)
- [x] 4.5 Add `delete_service(db, service_id) -> None`
- [x] 4.6 Add `create_service_item(db, service_id, item_in: ServiceItemCreate) -> ServiceItem`
- [x] 4.7 Add `delete_service_item(db, item_id) -> None`

## 5. Backend API Routes

- [x] 5.1 Create `backend/app/api/routes/services.py` with an `APIRouter` prefixed `/services`
- [x] 5.2 Implement `POST /services` → creates service; requires `admin` or `finance` via `require_role`; returns 201
- [x] 5.3 Implement `GET /services` → returns list using `get_services` (with selectinload); open to all authenticated users
- [x] 5.4 Implement `GET /services/{service_id}` → returns detail using `get_service`; returns 404 if missing
- [x] 5.5 Implement `PATCH /services/{service_id}` → updates service; requires `admin` or `finance`; returns 422 on invalid status transition
- [x] 5.6 Implement `DELETE /services/{service_id}` → deletes service and cascades to items; requires `admin` or `finance`; returns 204
- [x] 5.7 Implement `POST /services/{service_id}/items` → adds line item; requires `admin` or `finance`; returns 201
- [x] 5.8 Implement `DELETE /services/{service_id}/items/{item_id}` → removes line item; requires `admin` or `finance`; returns 204
- [x] 5.9 Register the services router in `backend/app/api/main.py`

## 6. Frontend API Client Regeneration

- [x] 6.1 Regenerate the typed API client from the updated OpenAPI schema (run the project's codegen script) so that service endpoints and types are available in the frontend

## 7. Frontend Services List Page

- [x] 7.1 Create route file `frontend/src/routes/_layout/services.tsx` using TanStack Router file-based routing
- [x] 7.2 Implement a `useQuery` call (via generated client) to fetch `/api/v1/services`
- [x] 7.3 Render a table with columns: Client Name, Type, Status, Execution Address
- [x] 7.4 Implement empty-state message when the services array is empty
- [x] 7.5 Add a "New Service" button that links to `/services/new`

## 8. Frontend New Service Form

- [x] 8.1 Create route file `frontend/src/routes/services/new.tsx`
- [x] 8.2 Implement a client selector (dropdown populated from `/api/v1/clients`) using the generated client
- [x] 8.3 Implement type selector (perfuração | reparo) and execution_address text input with required field validation
- [x] 8.4 Implement dynamic line-items section: add/remove rows for item_type, description, quantity, unit_price
- [x] 8.5 Validate that `quantity > 0` and `unit_price >= 0` client-side before submission
- [x] 8.6 On successful submission, call `POST /api/v1/services` (then `POST /api/v1/services/{id}/items` for each item) and redirect to `/services/{id}`
- [x] 8.7 Display inline validation errors for missing required fields without calling the API

## 9. Frontend Service Detail View

- [x] 9.1 Create route file `frontend/src/routes/services/$serviceId.tsx`
- [x] 9.2 Implement a `useQuery` to fetch `/api/v1/services/{serviceId}`, returning 404 page if not found
- [x] 9.3 Render service header: client name, type, status badge, execution address, notes
- [x] 9.4 Render line items table: item_type, description, quantity, unit_price, line total (quantity × unit_price)
- [x] 9.5 Display grand total (sum of all line totals)

## 10. Frontend Sidebar Navigation

- [x] 10.1 Add a "Serviços" link to the main sidebar component pointing to `/services`
