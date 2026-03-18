## ADDED Requirements

### Requirement: Client record has required identity fields

The system SHALL store each client with the following fields:
- `id`: UUID, primary key, auto-generated
- `name`: non-empty string, max 255 characters
- `document_type`: enum — `cpf` or `cnpj`
- `document_number`: plain digit string — exactly 11 digits for CPF, exactly 14 digits for CNPJ; unique across all clients
- `email`: optional valid email address, max 255 characters
- `phone`: optional plain string, max 20 characters
- `address`: optional plain string, max 500 characters
- `created_at`: UTC timestamp, auto-set on creation
- `updated_at`: UTC timestamp, auto-updated on every write

The system SHALL reject a client record whose `document_number` length does not match the declared `document_type`.

#### Scenario: Create individual client with valid CPF

- **WHEN** a POST request is made to `/api/v1/clients` with `document_type=cpf` and an 11-digit `document_number`
- **THEN** the system creates the record and returns HTTP 201 with the client JSON including `id` and `created_at`

#### Scenario: Create company client with valid CNPJ

- **WHEN** a POST request is made to `/api/v1/clients` with `document_type=cnpj` and a 14-digit `document_number`
- **THEN** the system creates the record and returns HTTP 201 with the client JSON

#### Scenario: Reject CPF with wrong digit count

- **WHEN** a POST request is made with `document_type=cpf` and a `document_number` that is not exactly 11 digits
- **THEN** the system returns HTTP 422 with a validation error identifying the `document_number` field

#### Scenario: Reject CNPJ with wrong digit count

- **WHEN** a POST request is made with `document_type=cnpj` and a `document_number` that is not exactly 14 digits
- **THEN** the system returns HTTP 422 with a validation error identifying the `document_number` field

#### Scenario: Reject non-digit characters in document_number

- **WHEN** a POST request is made with a `document_number` that contains non-digit characters (e.g., dots, dashes, slashes)
- **THEN** the system returns HTTP 422 with a validation error identifying the `document_number` field

#### Scenario: Create client without optional fields

- **WHEN** a POST request is made with only `name`, `document_type`, and `document_number` provided
- **THEN** the system creates the record with `email`, `phone`, and `address` set to null and returns HTTP 201

### Requirement: Document number is unique per client

The system SHALL reject creating or updating a client if the resulting `document_number` is already assigned to another client record.

#### Scenario: Duplicate document number on create

- **WHEN** a POST request is made with a `document_number` that already exists in the system
- **THEN** the system returns HTTP 409 with an error message indicating the document number is already registered

#### Scenario: Duplicate document number on update

- **WHEN** a PATCH request is made on client A attempting to set `document_number` to a value already held by client B
- **THEN** the system returns HTTP 409 with an error message indicating the document number is already registered

#### Scenario: Update to same document number is allowed

- **WHEN** a PATCH request is made on a client with a `document_number` equal to the client's own current value
- **THEN** the system accepts the update and returns HTTP 200

### Requirement: Client CRUD API is accessible only to admin and finance roles

The system SHALL require authentication for all `/api/v1/clients` endpoints. The system SHALL restrict access to users whose `role` is `admin` or `finance` (or `is_superuser=true`). All other authenticated users SHALL receive HTTP 403.

#### Scenario: Admin user lists clients

- **WHEN** an authenticated request with `role=admin` is made to GET `/api/v1/clients`
- **THEN** the system returns HTTP 200 with a paginated list of clients

#### Scenario: Finance user creates a client

- **WHEN** an authenticated request with `role=finance` is made to POST `/api/v1/clients` with valid data
- **THEN** the system returns HTTP 201 with the created client

#### Scenario: Client-role user is forbidden

- **WHEN** an authenticated request with `role=client` is made to GET `/api/v1/clients`
- **THEN** the system returns HTTP 403

#### Scenario: Unauthenticated request is rejected

- **WHEN** a request is made to any `/api/v1/clients` endpoint without a valid Bearer token
- **THEN** the system returns HTTP 401 or HTTP 403

### Requirement: Client list supports pagination

The system SHALL support `skip` (default 0) and `limit` (default 100, max 100) query parameters on GET `/api/v1/clients`. The response SHALL include a `count` field with the total number of client records.

#### Scenario: Paginate client list

- **WHEN** a GET request is made to `/api/v1/clients?skip=0&limit=10`
- **THEN** the system returns at most 10 client objects and a `count` reflecting the total number of clients in the database

#### Scenario: Default pagination applies when no parameters given

- **WHEN** a GET request is made to `/api/v1/clients` with no query parameters
- **THEN** the system returns up to 100 clients and the total `count`

### Requirement: Client record can be retrieved by ID

The system SHALL expose GET `/api/v1/clients/{client_id}` returning a single client. The system SHALL return HTTP 404 if no client with that UUID exists.

#### Scenario: Get existing client

- **WHEN** a GET request is made to `/api/v1/clients/{id}` with a valid existing UUID
- **THEN** the system returns HTTP 200 with the full client JSON

#### Scenario: Get non-existent client

- **WHEN** a GET request is made to `/api/v1/clients/{id}` with a UUID that does not exist
- **THEN** the system returns HTTP 404

### Requirement: Client record can be updated partially

The system SHALL expose PATCH `/api/v1/clients/{client_id}` accepting a partial client payload. Only supplied fields SHALL be updated. The system SHALL return HTTP 404 if the client does not exist.

#### Scenario: Update client name

- **WHEN** a PATCH request is made with only `{"name": "New Name"}` for an existing client
- **THEN** the system updates only the `name` field, leaves all other fields unchanged, and returns HTTP 200 with the updated client

#### Scenario: Update non-existent client

- **WHEN** a PATCH request is made to `/api/v1/clients/{id}` with a non-existent UUID
- **THEN** the system returns HTTP 404

### Requirement: Client record can be deleted

The system SHALL expose DELETE `/api/v1/clients/{client_id}` that permanently removes the client record. The system SHALL return HTTP 200 with a confirmation message on success, and HTTP 404 if the client does not exist.

#### Scenario: Delete existing client

- **WHEN** a DELETE request is made to `/api/v1/clients/{id}` with a valid existing UUID
- **THEN** the system permanently removes the record and returns HTTP 200 with a success message
- **AND** a subsequent GET request to the same URL returns HTTP 404

#### Scenario: Delete non-existent client

- **WHEN** a DELETE request is made to `/api/v1/clients/{id}` with a UUID that does not exist
- **THEN** the system returns HTTP 404

### Requirement: Frontend displays a Clients list page

The system SHALL provide a frontend page at `/clients` that lists all clients in a table. The page SHALL be accessible only when the logged-in user has `role=admin` or `role=finance`. The table SHALL display at minimum: name, document type, document number, email, and phone.

#### Scenario: Admin user sees clients list

- **WHEN** an admin user navigates to `/clients`
- **THEN** the page renders a table of clients fetched from the API

#### Scenario: Finance user sees clients list

- **WHEN** a finance user navigates to `/clients`
- **THEN** the page renders a table of clients fetched from the API

#### Scenario: Unauthorized user is redirected

- **WHEN** a user with `role=client` navigates to `/clients`
- **THEN** the system redirects the user away from the page (e.g., to the dashboard or a 403 page)

### Requirement: Frontend provides add and edit client forms

The system SHALL provide a modal or page form to create a new client and edit an existing client. The form SHALL include all client fields (name, document_type, document_number, email, phone, address). The form SHALL display validation errors returned by the API.

#### Scenario: Create client via form

- **WHEN** an admin or finance user submits the add-client form with valid data
- **THEN** the new client appears in the list without a full page reload
- **AND** the form closes

#### Scenario: Edit client via form

- **WHEN** an admin or finance user clicks edit on a client and submits the form with changed data
- **THEN** the updated client data is reflected in the list without a full page reload

#### Scenario: Form shows validation error

- **WHEN** a user submits the form with a CPF that does not have 11 digits
- **THEN** the form displays an error message on the `document_number` field without navigating away

### Requirement: Frontend provides delete client action

The system SHALL provide a delete action on each client row. The action SHALL require confirmation before sending the DELETE request to the API. After successful deletion, the client SHALL be removed from the list.

#### Scenario: Delete client with confirmation

- **WHEN** a user clicks delete on a client row and confirms the dialog
- **THEN** the system calls DELETE `/api/v1/clients/{id}` and removes the row from the list

#### Scenario: Cancel delete aborts action

- **WHEN** a user clicks delete on a client row but cancels the confirmation dialog
- **THEN** no API request is made and the client remains in the list

### Requirement: Sidebar includes a Clients navigation link

The system SHALL display a "Clientes" link in the sidebar navigation. The link SHALL be visible only to users with `role=admin` or `role=finance`.

#### Scenario: Admin sees Clients link

- **WHEN** an admin user views the sidebar
- **THEN** a "Clientes" navigation link is visible and navigates to `/clients`

#### Scenario: Client-role user does not see Clients link

- **WHEN** a user with `role=client` views the sidebar
- **THEN** no "Clientes" link is visible in the sidebar
