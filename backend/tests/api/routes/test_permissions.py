import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.core.permissions import ALL_PERMISSIONS, ROLE_PERMISSIONS, get_role_defaults
from app.models import UserCreate, UserPermission, UserRole
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_lower_string

# ── Unit tests for permissions module ────────────────────────────────────────


def test_role_defaults_admin() -> None:
    defaults = get_role_defaults(UserRole.admin)
    assert "manage_permissions" in defaults
    assert "manage_users" in defaults
    assert "manage_clients" in defaults
    assert "manage_services" in defaults
    assert "view_dashboard" in defaults


def test_role_defaults_finance() -> None:
    defaults = get_role_defaults(UserRole.finance)
    assert defaults == {"view_dashboard", "view_contas_pagar", "view_contas_receber"}


def test_role_defaults_client() -> None:
    defaults = get_role_defaults(UserRole.client)
    assert defaults == set()


def test_all_roles_in_mapping() -> None:
    for role in UserRole:
        assert role in ROLE_PERMISSIONS


def test_all_permissions_in_role_defaults_are_valid() -> None:
    for role, perms in ROLE_PERMISSIONS.items():
        for p in perms:
            assert p in ALL_PERMISSIONS, f"{p} (from {role}) not in ALL_PERMISSIONS"


def test_effective_with_overrides(db: Session) -> None:
    from app.core.permissions import get_effective_permissions

    user_in = UserCreate(
        email=f"{random_lower_string()}@example.com",
        password=random_lower_string(),
        role=UserRole.client,
    )
    user = crud.create_user(session=db, user_create=user_in)

    # Add an override
    up = UserPermission(user_id=user.id, permission="view_well_status")
    db.add(up)
    db.commit()

    effective = get_effective_permissions(db, user)
    assert "view_well_status" in effective


def test_effective_no_duplicate(db: Session) -> None:
    from app.core.permissions import get_effective_permissions

    user_in = UserCreate(
        email=f"{random_lower_string()}@example.com",
        password=random_lower_string(),
        role=UserRole.admin,
    )
    user = crud.create_user(session=db, user_create=user_in)

    # Add override that matches a role default
    up = UserPermission(user_id=user.id, permission="manage_users")
    db.add(up)
    db.commit()

    effective = get_effective_permissions(db, user)
    # Should still contain manage_users exactly once (it's a set)
    assert "manage_users" in effective
    assert isinstance(effective, set)


# ── API tests for permissions endpoints ──────────────────────────────────────


def _admin_headers(client: TestClient, db: Session) -> dict[str, str]:
    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, role=UserRole.admin)
    crud.create_user(session=db, user_create=user_in)
    return user_authentication_headers(client=client, email=email, password=password)


def _finance_headers(client: TestClient, db: Session) -> dict[str, str]:
    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, role=UserRole.finance)
    crud.create_user(session=db, user_create=user_in)
    return user_authentication_headers(client=client, email=email, password=password)


def test_get_available_permissions(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/permissions/available",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data == ALL_PERMISSIONS


def test_get_available_permissions_admin(client: TestClient, db: Session) -> None:
    """Admin role has manage_permissions by default."""
    headers = _admin_headers(client, db)
    r = client.get(f"{settings.API_V1_STR}/permissions/available", headers=headers)
    assert r.status_code == 200


def test_get_available_permissions_finance_forbidden(
    client: TestClient, db: Session
) -> None:
    headers = _finance_headers(client, db)
    r = client.get(f"{settings.API_V1_STR}/permissions/available", headers=headers)
    assert r.status_code == 403


def test_get_users_permissions(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/permissions/users",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) > 0
    user_data = data[0]
    assert "role_defaults" in user_data
    assert "overrides" in user_data
    assert "effective" in user_data


def test_set_user_overrides(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    # Create a client-role user
    user_in = UserCreate(
        email=f"{random_lower_string()}@example.com",
        password=random_lower_string(),
        role=UserRole.client,
    )
    user = crud.create_user(session=db, user_create=user_in)

    # Set overrides
    r = client.put(
        f"{settings.API_V1_STR}/permissions/users/{user.id}",
        headers=superuser_token_headers,
        json={"permissions": ["view_well_status", "view_reports"]},
    )
    assert r.status_code == 200
    data = r.json()
    assert "view_well_status" in data["overrides"]
    assert "view_reports" in data["overrides"]
    assert "view_well_status" in data["effective"]
    assert "view_reports" in data["effective"]


def test_set_overrides_filters_role_defaults(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    """Overrides that match role defaults are not stored."""
    user_in = UserCreate(
        email=f"{random_lower_string()}@example.com",
        password=random_lower_string(),
        role=UserRole.admin,
    )
    user = crud.create_user(session=db, user_create=user_in)

    # Try to set an override that's already a role default
    r = client.put(
        f"{settings.API_V1_STR}/permissions/users/{user.id}",
        headers=superuser_token_headers,
        json={"permissions": ["manage_users", "view_well_status"]},
    )
    assert r.status_code == 200
    data = r.json()
    # manage_users is a role default, so it shouldn't be in overrides
    assert "manage_users" not in data["overrides"]
    assert "view_well_status" in data["overrides"]
    # But both should be in effective
    assert "manage_users" in data["effective"]
    assert "view_well_status" in data["effective"]


def test_set_overrides_invalid_permission(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    user_in = UserCreate(
        email=f"{random_lower_string()}@example.com",
        password=random_lower_string(),
        role=UserRole.client,
    )
    user = crud.create_user(session=db, user_create=user_in)

    r = client.put(
        f"{settings.API_V1_STR}/permissions/users/{user.id}",
        headers=superuser_token_headers,
        json={"permissions": ["nonexistent_permission"]},
    )
    assert r.status_code == 422


def test_get_single_user_permissions(
    client: TestClient, superuser_token_headers: dict[str, str], db: Session
) -> None:
    user_in = UserCreate(
        email=f"{random_lower_string()}@example.com",
        password=random_lower_string(),
        role=UserRole.finance,
    )
    user = crud.create_user(session=db, user_create=user_in)

    r = client.get(
        f"{settings.API_V1_STR}/permissions/users/{user.id}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["role"] == "finance"
    assert "view_dashboard" in data["role_defaults"]


def test_get_single_user_permissions_not_found(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    r = client.get(
        f"{settings.API_V1_STR}/permissions/users/{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert r.status_code == 404


# ── Route guard tests ────────────────────────────────────────────────────────


def test_require_permission_allows_role_default(
    client: TestClient, db: Session
) -> None:
    """Admin can access manage_clients endpoint (role default)."""
    headers = _admin_headers(client, db)
    r = client.get(f"{settings.API_V1_STR}/clients/", headers=headers)
    assert r.status_code == 200


def test_require_permission_allows_override(client: TestClient, db: Session) -> None:
    """Client with manage_clients override can access clients endpoint."""
    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, role=UserRole.client)
    user = crud.create_user(session=db, user_create=user_in)

    # Grant override
    up = UserPermission(user_id=user.id, permission="manage_clients")
    db.add(up)
    db.commit()

    headers = user_authentication_headers(client=client, email=email, password=password)
    r = client.get(f"{settings.API_V1_STR}/clients/", headers=headers)
    assert r.status_code == 200


def test_require_permission_denies_no_permission(
    client: TestClient, db: Session
) -> None:
    """Client without override gets 403."""
    email = f"{random_lower_string()}@example.com"
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password, role=UserRole.client)
    crud.create_user(session=db, user_create=user_in)
    headers = user_authentication_headers(client=client, email=email, password=password)

    r = client.get(f"{settings.API_V1_STR}/clients/", headers=headers)
    assert r.status_code == 403


def test_require_permission_superuser_bypass(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Superuser can access any endpoint regardless of role."""
    r = client.get(f"{settings.API_V1_STR}/clients/", headers=superuser_token_headers)
    assert r.status_code == 200
