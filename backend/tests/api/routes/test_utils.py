from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import settings
from tests.utils.utils import random_email


def test_health_check(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert r.status_code == 200
    assert r.json() is True


def test_test_email(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    email = random_email()
    with (
        patch("app.core.config.settings.SMTP_HOST", "smtp.example.com"),
        patch("app.core.config.settings.SMTP_USER", "admin@example.com"),
    ):
        r = client.post(
            f"{settings.API_V1_STR}/utils/test-email/",
            params={"email_to": email},
            headers=superuser_token_headers,
        )
    assert r.status_code == 201
    assert r.json() == {"message": "Test email sent"}


def test_test_email_requires_superuser(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        params={"email_to": "x@example.com"},
    )
    assert r.status_code == 401


def test_invalid_token_returns_403(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert r.status_code == 403
