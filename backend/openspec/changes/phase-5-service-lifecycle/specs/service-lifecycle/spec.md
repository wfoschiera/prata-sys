## ADDED Requirements

### Requirement: Service status follows an enforced lifecycle with a cancelled terminal state
The system SHALL enforce that service status transitions follow the sequence `requested` → `scheduled` → `executing` → `completed`. The `cancelled` state SHALL be reachable from any non-terminal state (`requested`, `scheduled`, `executing`). Transitions that skip intermediate states, or that attempt to leave a terminal state (`completed`, `cancelled`), SHALL be rejected. Only users with the `admin` role may trigger transitions; `finance` users may view status history but cannot change status.

#### Scenario: Valid forward transition by admin
- **WHEN** an `admin` user POSTs to `/api/v1/services/{id}/transition` with `{"to_status": "scheduled"}`  on a service currently in `requested`
- **THEN** the system updates the service status to `scheduled`
- **AND** returns HTTP 200 with the updated service payload
- **AND** creates a new `ServiceStatusLog` record capturing `from_status`, `to_status`, `changed_by`, and `changed_at`

#### Scenario: Invalid status jump is rejected
- **WHEN** an `admin` user POSTs to `/api/v1/services/{id}/transition` with `{"to_status": "completed"}` on a service in `requested`
- **THEN** the system returns HTTP 422 Unprocessable Entity with a message indicating the transition is not allowed

#### Scenario: Finance user cannot trigger a transition
- **WHEN** a `finance` user POSTs to `/api/v1/services/{id}/transition`
- **THEN** the system returns HTTP 403 Forbidden

#### Scenario: Transition out of terminal state is rejected
- **WHEN** an `admin` user POSTs to `/api/v1/services/{id}/transition` with any `to_status` on a service in `completed` or `cancelled`
- **THEN** the system returns HTTP 422 Unprocessable Entity indicating the service has reached a terminal state

#### Scenario: PATCH endpoint rejects direct status change
- **WHEN** any user sends a PATCH to `/api/v1/services/{id}` with a `status` field in the body
- **THEN** the system returns HTTP 422 Unprocessable Entity with a message directing the caller to use the `/transition` endpoint

---

### Requirement: Cancellation requires a reason
The system SHALL require a non-empty `cancelled_reason` string when transitioning a service to `cancelled`. The reason SHALL be stored on the `Service` record and returned in subsequent GET responses.

#### Scenario: Cancellation with reason succeeds
- **WHEN** an `admin` user POSTs to `/api/v1/services/{id}/transition` with `{"to_status": "cancelled", "reason": "Cliente desistiu da perfuração"}`
- **THEN** the system transitions the service to `cancelled`, persists the reason in `cancelled_reason`, and returns HTTP 200

#### Scenario: Cancellation without reason is rejected
- **WHEN** an `admin` user POSTs to `/api/v1/services/{id}/transition` with `{"to_status": "cancelled"}` and no `reason` (or an empty string)
- **THEN** the system returns HTTP 422 Unprocessable Entity indicating `reason` is required for cancellation

---

### Requirement: Every status transition is recorded in an audit log
The system SHALL create a `ServiceStatusLog` entry for every successful status transition. Each entry SHALL record `service_id`, `from_status`, `to_status`, `changed_by` (the `User.id` of the requesting user), and `changed_at` (UTC timestamp). Audit log entries are immutable — they cannot be updated or deleted via the API.

#### Scenario: Log entry created on transition
- **WHEN** a status transition succeeds
- **THEN** a new `ServiceStatusLog` row exists with the correct `from_status`, `to_status`, `changed_by`, and a `changed_at` value equal to approximately the time of the request

#### Scenario: Status log is returned with service detail
- **WHEN** a GET request is sent to `/api/v1/services/{id}`
- **THEN** the response includes a `status_logs` array containing all log entries for that service in chronological order

---

### Requirement: Service model gains description and cancelled_reason fields
The `Service` model SHALL include an optional `description` Text field for free-form notes about the service (distinct from `notes` which may be repurposed or deprecated) and a nullable `cancelled_reason` String field that is only populated when the service is `cancelled`.

#### Scenario: Service created with description
- **WHEN** an `admin` or `finance` user creates a service including a `description` field
- **THEN** the `description` is persisted and returned in GET responses

#### Scenario: cancelled_reason is null on non-cancelled service
- **WHEN** a GET is made on a service that is not in the `cancelled` state
- **THEN** `cancelled_reason` in the response SHALL be `null`

---

### Requirement: Material items are flagged as reservado when a service is scheduled
The system SHALL cross-reference the material `ServiceItem` records of a service against `StockItem` quantities when the service transitions to `scheduled`. Items whose required quantity exceeds available stock SHALL be flagged with a `stock_warning` indicator. Insufficient stock SHALL NOT block the transition — it is informational only. A `reservado` quantity SHALL be incremented on each affected `StockItem`.

#### Scenario: Transition to scheduled succeeds even with insufficient stock
- **WHEN** an `admin` user transitions a service to `scheduled` and one material item exceeds available stock
- **THEN** the system completes the transition
- **AND** the response payload includes a `stock_warnings` array listing the item descriptions and shortfall quantities

#### Scenario: Available stock items are marked reservado
- **WHEN** a service transitions to `scheduled` and a material item has sufficient stock
- **THEN** the `StockItem.reservado` quantity is incremented by the `ServiceItem.quantity`

#### Scenario: Service detail shows stock warning badge
- **WHEN** a service is in `scheduled` state and has material items with quantities that exceed available stock
- **THEN** the service detail API response includes a `has_stock_warning: true` flag

---

### Requirement: Manual stock deduction is available when service is executing
The system SHALL expose a `POST /api/v1/services/{id}/deduct-stock` endpoint, accessible only to `admin` users, that deducts the reserved material quantities from `StockItem` records. This endpoint is only valid when the service is in `executing` status.

#### Scenario: Deduct stock succeeds
- **WHEN** an `admin` user POSTs to `/api/v1/services/{id}/deduct-stock` on a service in `executing`
- **THEN** each material `ServiceItem` quantity is subtracted from the corresponding `StockItem.quantity`
- **AND** `StockItem.reservado` is decremented accordingly
- **AND** the endpoint returns HTTP 200 with a summary of deductions

#### Scenario: Deduct stock rejected for non-executing service
- **WHEN** an `admin` user POSTs to `/api/v1/services/{id}/deduct-stock` on a service not in `executing` status
- **THEN** the system returns HTTP 422 Unprocessable Entity

#### Scenario: Finance user cannot deduct stock
- **WHEN** a `finance` user POSTs to `/api/v1/services/{id}/deduct-stock`
- **THEN** the system returns HTTP 403 Forbidden

---

### Requirement: Completing a service confirms material deductions
The system SHALL require the caller to submit a `deduction_items` list when transitioning a service to `completed`. The list identifies which material items to deduct from stock and in what quantity, allowing the user to review and adjust before confirming. The transition SHALL NOT proceed without this confirmation payload.

#### Scenario: Completion with confirmed deduction items succeeds
- **WHEN** an `admin` user POSTs to `/api/v1/services/{id}/transition` with `{"to_status": "completed", "deduction_items": [{"service_item_id": "...", "quantity": 5}]}`
- **THEN** the system deducts the specified quantities from `StockItem`, transitions the service to `completed`, releases any remaining `reservado` amounts, and returns HTTP 200

#### Scenario: Completion without deduction_items is rejected
- **WHEN** an `admin` user POSTs to `/api/v1/services/{id}/transition` with `{"to_status": "completed"}` and no `deduction_items`
- **THEN** the system returns HTTP 422 Unprocessable Entity requiring the deduction confirmation

---

### Requirement: Frontend displays a status timeline on the service detail page
The system SHALL render a visual status timeline (progress indicator) on the service detail page showing the ordered states `requested → scheduled → executing → completed`, with the current state highlighted and `cancelled` shown as a divergent terminal branch when applicable.

#### Scenario: Status timeline renders current state
- **WHEN** a logged-in user views a service detail page for a service in `executing` status
- **THEN** the timeline component shows `requested`, `scheduled`, and `executing` as completed steps, and `completed` as a future step

#### Scenario: Cancelled state is shown distinctly
- **WHEN** a logged-in user views a service detail page for a `cancelled` service
- **THEN** the timeline shows the last reached state followed by the `cancelled` terminal state, and the `cancelled_reason` is displayed

---

### Requirement: Frontend shows contextual transition buttons for valid next states
The system SHALL render transition action buttons on the service detail page only for states that are valid next transitions from the current state. Buttons are only visible to `admin` users.

#### Scenario: Only valid transitions are shown
- **WHEN** an `admin` user views a service in `scheduled` status
- **THEN** the page shows a button to advance to `executing` and a button to `cancel`, but no button to move to `requested` or `completed`

#### Scenario: No transition buttons on terminal states
- **WHEN** any user views a service in `completed` or `cancelled` status
- **THEN** no transition buttons are rendered

#### Scenario: Finance user sees no transition buttons
- **WHEN** a `finance` user views any service detail page
- **THEN** no transition action buttons are rendered

---

### Requirement: Frontend presents a cancellation modal with a required reason field
The system SHALL display a modal dialog when the user clicks the "Cancelar serviço" button. The modal SHALL contain a required text field for the cancellation reason. The confirm button SHALL be disabled until the reason is non-empty.

#### Scenario: Cancellation modal requires reason before confirming
- **WHEN** an `admin` user opens the cancellation modal and leaves the reason field empty
- **THEN** the confirm button remains disabled and no API call is made

#### Scenario: Cancellation modal submits with reason
- **WHEN** an `admin` user fills in the reason and clicks confirm
- **THEN** the modal calls `POST /transition` with `to_status: cancelled` and the provided reason, then closes and refreshes the service detail page

---

### Requirement: Frontend presents a completion confirmation modal listing products to deduct
The system SHALL display a modal dialog when the user clicks the "Concluir serviço" button. The modal SHALL list all material `ServiceItem` records and allow the user to adjust quantities before confirming deduction. The confirm action submits the `deduction_items` payload.

#### Scenario: Completion modal pre-fills item quantities
- **WHEN** an `admin` user opens the completion modal
- **THEN** each material `ServiceItem` is listed with its description and quantity pre-filled, and the user may adjust individual quantities

#### Scenario: Completion modal submits deduction payload
- **WHEN** the user reviews items and clicks confirm
- **THEN** the modal calls `POST /transition` with `to_status: completed` and the reviewed `deduction_items` list

---

### Requirement: Frontend shows a stock warning badge on scheduled services with insufficient stock
The system SHALL render a visible warning indicator on the service detail page (and in the services list) when a service in `scheduled` status has the `has_stock_warning: true` flag from the API.

#### Scenario: Warning badge is visible on scheduled service with stock shortfall
- **WHEN** a user views the service detail for a scheduled service where `has_stock_warning` is `true`
- **THEN** a warning badge or alert is displayed indicating that one or more materials are below required stock levels

#### Scenario: No warning badge when stock is sufficient
- **WHEN** a user views a scheduled service where `has_stock_warning` is `false`
- **THEN** no stock warning indicator is rendered
