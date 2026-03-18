## ADDED Requirements

### Requirement: User has a business role
Every user SHALL have a `role` field with one of the values: `admin`, `finance`, `client`.
The default value SHALL be `admin` to preserve access for existing users after migration.
`role` is independent of `is_superuser` — superuser status grants unrestricted system access regardless of role.

#### Scenario: New user is created with explicit role
- **WHEN** an admin creates a user with `role: "finance"`
- **THEN** the user is stored with `role = "finance"`

#### Scenario: New user is created without specifying role
- **WHEN** a user is created without a `role` value
- **THEN** the user defaults to `role = "admin"`

#### Scenario: User role is updated
- **WHEN** an admin updates a user's role to `"client"`
- **THEN** the user's role is changed to `"client"`

### Requirement: Routes can require a minimum role
The system SHALL provide a `require_role` dependency that protects API routes by role.
A request to a role-protected route from a user without the required role SHALL be rejected with HTTP 403.

#### Scenario: User with correct role accesses a protected route
- **WHEN** a user with `role = "admin"` accesses a route requiring `admin`
- **THEN** the request proceeds normally

#### Scenario: User with insufficient role accesses a protected route
- **WHEN** a user with `role = "client"` accesses a route requiring `admin` or `finance`
- **THEN** the system returns HTTP 403 Forbidden

#### Scenario: Superuser bypasses role checks
- **WHEN** a user with `is_superuser = true` accesses any role-protected route
- **THEN** the request proceeds regardless of the user's `role` value

## REMOVED Requirements

### Requirement: Item resource
**Reason**: The `Item` model is template boilerplate with no relevance to the water well drilling domain.
**Migration**: No migration needed — no production data exists. Remove all Item models, CRUD, routes, and frontend components.
