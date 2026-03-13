## ADDED Requirements

### Requirement: Service order can be created by authorized users
The system SHALL allow users with the `admin` or `finance` role to create a service order by providing a valid `client_id`, a `type` (perfuração | reparo), an `execution_address`, and optional `notes`. The initial status SHALL be set to `requested`.

#### Scenario: Successful service creation
- **WHEN** an `admin` or `finance` user submits a POST to `/api/v1/services` with a valid `client_id`, `type`, and `execution_address`
- **THEN** the system creates a new `Service` record with status `requested`
- **AND** returns HTTP 201 with the created service payload including `id`, `client_id`, `type`, `status`, `execution_address`, and `notes`

#### Scenario: Unauthorized user cannot create service
- **WHEN** a user with the `client` role submits a POST to `/api/v1/services`
- **THEN** the system returns HTTP 403 Forbidden

#### Scenario: Missing required field
- **WHEN** a POST to `/api/v1/services` omits `execution_address`
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Non-existent client
- **WHEN** a POST to `/api/v1/services` references a `client_id` that does not exist
- **THEN** the system returns HTTP 404 Not Found

---

### Requirement: Service status follows a defined lifecycle
The system SHALL enforce that service status transitions follow the sequence: `requested` → `scheduled` → `executing` → `completed`. Direct jumps that skip intermediate states SHALL be rejected.

#### Scenario: Valid sequential status update
- **WHEN** an `admin` or `finance` user updates a service from `requested` to `scheduled`
- **THEN** the system accepts the update and returns HTTP 200 with the updated status

#### Scenario: Invalid status jump is rejected
- **WHEN** an `admin` or `finance` user attempts to update a service status from `requested` to `completed`
- **THEN** the system returns HTTP 422 Unprocessable Entity with a message indicating the transition is invalid

#### Scenario: Unauthorized user cannot update status
- **WHEN** a user with the `client` role sends a PATCH to `/api/v1/services/{id}`
- **THEN** the system returns HTTP 403 Forbidden

---

### Requirement: Services list is returned without N+1 queries
The system SHALL return all service orders from `GET /api/v1/services` with `client` and `items` data eagerly loaded using `selectinload()` so that the query count does not grow with the number of services.

#### Scenario: Services list loads related data in bounded queries
- **WHEN** a user sends GET to `/api/v1/services` and there are N services each with items and a linked client
- **THEN** the system returns all services with `client` and `items` embedded in the response
- **AND** the total number of SQL queries issued SHALL be at most 3 (one for services, one for clients, one for items) regardless of N

#### Scenario: Empty services list
- **WHEN** a user sends GET to `/api/v1/services` and no services exist
- **THEN** the system returns HTTP 200 with an empty array `[]`

---

### Requirement: Service line items can be managed
The system SHALL allow `admin` and `finance` users to add, update, and remove `ServiceItem` records on a service. Each item MUST have `item_type` (material | serviço), `description`, `quantity` (positive number), and `unit_price` (non-negative number). Items are owned by a service and deleted when the service is deleted.

#### Scenario: Add item to service
- **WHEN** an `admin` or `finance` user POSTs to `/api/v1/services/{id}/items` with valid `item_type`, `description`, `quantity`, and `unit_price`
- **THEN** the system creates the item linked to the service and returns HTTP 201 with the item payload

#### Scenario: Item quantity must be positive
- **WHEN** a POST to `/api/v1/services/{id}/items` provides `quantity` of `0` or negative
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Item unit_price must be non-negative
- **WHEN** a POST to `/api/v1/services/{id}/items` provides a negative `unit_price`
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Deleting a service cascades to items
- **WHEN** a DELETE request is sent to `/api/v1/services/{id}` by an authorized user
- **THEN** the system deletes the service and all associated `ServiceItem` records
- **AND** returns HTTP 204 No Content

---

### Requirement: Service detail view is accessible
The system SHALL return the full detail of a single service order, including the linked client and all line items, from `GET /api/v1/services/{id}`.

#### Scenario: Existing service is retrieved
- **WHEN** a GET request is sent to `/api/v1/services/{id}` for an existing service
- **THEN** the system returns HTTP 200 with the service object including `client` (full object) and `items` (array)

#### Scenario: Non-existent service returns 404
- **WHEN** a GET request is sent to `/api/v1/services/{id}` for an id that does not exist
- **THEN** the system returns HTTP 404 Not Found

---

### Requirement: Frontend services list page displays all service orders
The system SHALL provide a frontend page at `/services` that lists all service orders showing client name, type, status, and execution address.

#### Scenario: Services list renders with data
- **WHEN** a logged-in user navigates to `/services`
- **THEN** the page displays a table or list of service orders with columns for client name, type, status, and execution address

#### Scenario: Empty state is shown when no services exist
- **WHEN** a logged-in user navigates to `/services` and no service orders exist
- **THEN** the page displays an empty-state message indicating no services have been created

---

### Requirement: Frontend new service form allows creating a service with line items
The system SHALL provide a frontend form at `/services/new` where authorized users can select a client, choose a type, enter an execution address, add optional notes, and add one or more line items before submitting.

#### Scenario: Successful form submission creates service
- **WHEN** an authorized user fills in all required fields and adds at least one line item, then submits the form
- **THEN** the system calls the API, creates the service and items, and redirects to the service detail page

#### Scenario: Form prevents submission with missing required fields
- **WHEN** the user submits the form without selecting a client or entering an execution address
- **THEN** the form displays inline validation errors and does not call the API

---

### Requirement: Sidebar navigation includes a Services link
The system SHALL display a "Serviços" link in the main application sidebar that navigates to `/services`.

#### Scenario: Sidebar link navigates to services list
- **WHEN** a logged-in user clicks "Serviços" in the sidebar
- **THEN** the browser navigates to `/services` and the services list page is rendered
