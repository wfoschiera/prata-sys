"""Tests for /api/v1/settings endpoints (company settings)."""

from http import HTTPStatus

from fastapi.testclient import TestClient

from app.core.config import settings

PREFIX = f"{settings.API_V1_STR}/settings"


# ── GET /settings/empresa ─────────────────────────────────────────────────────


def test_get_company_settings_returns_default(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """When no settings exist yet, return defaults."""
    r = client.get(f"{PREFIX}/empresa", headers=superuser_token_headers)
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert "company_name" in data


def test_get_company_settings_admin_can_view(
    client: TestClient, admin_token_headers: dict[str, str]
) -> None:
    """Admin role (view_dashboard) can read company settings."""
    r = client.get(f"{PREFIX}/empresa", headers=admin_token_headers)
    assert r.status_code == HTTPStatus.OK


def test_get_company_settings_finance_can_view(
    client: TestClient, finance_token_headers: dict[str, str]
) -> None:
    """Finance role (view_dashboard) can read company settings."""
    r = client.get(f"{PREFIX}/empresa", headers=finance_token_headers)
    assert r.status_code == HTTPStatus.OK


def test_get_company_settings_client_forbidden(
    client: TestClient, client_token_headers: dict[str, str]
) -> None:
    """Client role does NOT have view_dashboard, should be 403."""
    r = client.get(f"{PREFIX}/empresa", headers=client_token_headers)
    assert r.status_code == HTTPStatus.FORBIDDEN


# ── PUT /settings/empresa ─────────────────────────────────────────────────────


def test_update_company_settings_creates_first_time(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """First PUT creates the singleton settings row."""
    r = client.put(
        f"{PREFIX}/empresa",
        headers=superuser_token_headers,
        json={
            "company_name": "Prata Poços Artesianos",
            "cnpj": "49.508.087/0001-00",
            "phone": "66 9 9985-0535",
        },
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["company_name"] == "Prata Poços Artesianos"
    assert data["cnpj"] == "49.508.087/0001-00"
    assert data["phone"] == "66 9 9985-0535"


def test_update_company_settings_updates_existing(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    """Second PUT updates the existing settings row."""
    # Create first
    client.put(
        f"{PREFIX}/empresa",
        headers=superuser_token_headers,
        json={"company_name": "Original Name"},
    )
    # Update
    r = client.put(
        f"{PREFIX}/empresa",
        headers=superuser_token_headers,
        json={"company_name": "Updated Name", "email": "contato@prata.com.br"},
    )
    assert r.status_code == HTTPStatus.OK
    data = r.json()
    assert data["company_name"] == "Updated Name"
    assert data["email"] == "contato@prata.com.br"

    # Verify via GET
    r2 = client.get(f"{PREFIX}/empresa", headers=superuser_token_headers)
    assert r2.json()["company_name"] == "Updated Name"


def test_update_company_settings_non_superuser_forbidden(
    client: TestClient, admin_token_headers: dict[str, str]
) -> None:
    """Only superusers can update company settings; admin gets 403."""
    r = client.put(
        f"{PREFIX}/empresa",
        headers=admin_token_headers,
        json={"company_name": "Should Fail"},
    )
    assert r.status_code == HTTPStatus.FORBIDDEN


def test_update_company_settings_finance_forbidden(
    client: TestClient, finance_token_headers: dict[str, str]
) -> None:
    """Finance role cannot update company settings."""
    r = client.put(
        f"{PREFIX}/empresa",
        headers=finance_token_headers,
        json={"company_name": "Should Fail"},
    )
    assert r.status_code == HTTPStatus.FORBIDDEN


def test_update_company_settings_unauthenticated(
    client: TestClient,
) -> None:
    """Unauthenticated request should return 401."""
    r = client.put(
        f"{PREFIX}/empresa",
        json={"company_name": "No Auth"},
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED
