## 1. Backend Model and Migration

- [x] 1.1 Add `DocumentType` string enum (`cpf`, `cnpj`) to `backend/app/models.py`
- [x] 1.2 Add `ClientBase`, `ClientCreate`, `ClientUpdate`, `Client` (table=True), `ClientPublic`, and `ClientsPublic` SQLModel classes to `backend/app/models.py`; include `document_number` unique constraint and `created_at`/`updated_at` fields
- [x] 1.3 Add Pydantic validators on `ClientBase` (or `ClientCreate`/`ClientUpdate`) that enforce `document_number` contains only digits and has length 11 for CPF / 14 for CNPJ
- [x] 1.4 Run `alembic revision --autogenerate -m "add client table"` from the backend directory and verify the generated migration creates the `client` table with the unique constraint on `document_number`
- [x] 1.5 Run `alembic upgrade head` against the local dev database and confirm the `client` table exists

## 2. Backend CRUD Functions

- [x] 2.1 Add `get_client(session, client_id)` to `backend/app/crud.py` — returns `Client | None`
- [x] 2.2 Add `get_clients(session, skip, limit)` to `backend/app/crud.py` — returns `(list[Client], total_count)` using a single count query and a single data query (avoid N+1)
- [x] 2.3 Add `get_client_by_document(session, document_number)` to `backend/app/crud.py` — used for duplicate-document checks
- [x] 2.4 Add `create_client(session, client_in: ClientCreate)` to `backend/app/crud.py`
- [x] 2.5 Add `update_client(session, db_client: Client, client_in: ClientUpdate)` to `backend/app/crud.py`
- [x] 2.6 Add `delete_client(session, db_client: Client)` to `backend/app/crud.py`

## 3. Backend API Router

- [x] 3.1 Create `backend/app/api/routes/clients.py` with an `APIRouter(prefix="/clients", tags=["clients"])`
- [x] 3.2 Implement GET `/` (list clients) with `skip`/`limit` query params, response model `ClientsPublic`, dependency `Depends(require_role("admin", "finance"))`
- [x] 3.3 Implement POST `/` (create client): check for duplicate `document_number` via `get_client_by_document`, return 409 if found, else create and return 201
- [x] 3.4 Implement GET `/{client_id}` (get by ID): return 404 if not found
- [x] 3.5 Implement PATCH `/{client_id}` (update client): return 404 if not found; check duplicate `document_number` if it is being changed; return 409 on conflict
- [x] 3.6 Implement DELETE `/{client_id}` (delete client): return 404 if not found; return `Message` on success
- [x] 3.7 Register the clients router in `backend/app/api/main.py`

## 4. Frontend API Client Regeneration

- [ ] 4.1 Start the backend dev server and regenerate the frontend API client (run the project's `openapi-ts` / codegen script) so `Client*` types and request functions are available in the frontend

## 5. Frontend Clients List Page

- [ ] 5.1 Create `frontend/src/routes/_layout/clients.tsx` as the Clients list page using TanStack Router file-based routing conventions
- [ ] 5.2 Add a TanStack Query `useQuery` hook that calls the generated `getClients` API function to fetch the paginated client list — ensure the query fetches count and data in a single call (no extra per-row queries)
- [ ] 5.3 Render a table (shadcn/ui `Table`) with columns: Name, Document Type, Document Number, Email, Phone, and an Actions column
- [ ] 5.4 Add route-level auth guard: redirect users with `role=client` away from `/clients` (to dashboard or 403 page)

## 6. Frontend Add/Edit Client Form

- [ ] 6.1 Create a `ClientForm` component (modal or drawer, using shadcn/ui) with fields: name, document_type (select), document_number, email, phone, address
- [ ] 6.2 Add client-side validation: `document_number` must be digits only; length must be 11 (CPF) or 14 (CNPJ) based on selected `document_type`
- [ ] 6.3 Wire the "Add Client" button on the list page to open `ClientForm` in create mode; on success, invalidate the clients query so the list refreshes without a full page reload
- [ ] 6.4 Wire the edit action in each table row to open `ClientForm` pre-filled with the client's data; on success, invalidate the clients query
- [ ] 6.5 Display API validation errors (422, 409) inline in the form on the relevant fields

## 7. Frontend Delete Client Action

- [ ] 7.1 Add a delete button per row that opens a shadcn/ui confirmation dialog (AlertDialog)
- [ ] 7.2 On confirmation, call the generated `deleteClient` API function; on success, invalidate the clients query and dismiss the dialog
- [ ] 7.3 On cancel, close the dialog without making any API request

## 8. Frontend Sidebar Link

- [ ] 8.1 Locate the sidebar navigation component and add a "Clientes" link pointing to `/clients`
- [ ] 8.2 Conditionally render the link only when the current user's role is `admin` or `finance` (hide for `role=client`)

## 9. Verification

- [ ] 9.1 Manually test create/read/update/delete flows via the UI as an admin user
- [ ] 9.2 Manually verify that a user with `role=client` cannot access `/clients` in the frontend and receives 403 from the API
- [ ] 9.3 Verify duplicate document number returns 409 on both create and update
- [ ] 9.4 Verify CPF with wrong digit count returns a validation error in the form and 422 from the API
- [ ] 9.5 Confirm the Alembic migration is reversible: run `alembic downgrade -1` and then `alembic upgrade head` without errors
