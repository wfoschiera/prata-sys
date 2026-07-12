from collections.abc import Generator
from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api.deps import get_db
from app.core.config import settings
from app.main import app
from tests.utils.utils import random_email


def test_health_check(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/utils/health-check/")
    assert r.status_code == HTTPStatus.OK
    assert r.json() is True


def test_readiness_ok(client: TestClient) -> None:
    r = client.get(f"{settings.API_V1_STR}/utils/readiness/")
    assert r.status_code == HTTPStatus.OK
    assert r.json() == {"message": "ready"}


def test_readiness_db_down_returns_503(client: TestClient) -> None:
    class _BrokenSession:
        def exec(self, *args: object, **kwargs: object) -> None:
            msg = "connection refused"
            raise RuntimeError(msg)

    def _broken_get_db() -> Generator[_BrokenSession, None, None]:
        yield _BrokenSession()

    app.dependency_overrides[get_db] = _broken_get_db
    try:
        r = client.get(f"{settings.API_V1_STR}/utils/readiness/")
    finally:
        # Restore the client fixture's own get_db override.
        app.dependency_overrides.pop(get_db, None)
    assert r.status_code == HTTPStatus.SERVICE_UNAVAILABLE
    assert r.json()["detail"] == "database unavailable"


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
    assert r.status_code == HTTPStatus.CREATED
    assert r.json() == {"message": "Test email sent"}


def test_test_email_requires_superuser(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/utils/test-email/",
        params={"email_to": "x@example.com"},
    )
    assert r.status_code == HTTPStatus.UNAUTHORIZED


def test_invalid_token_returns_403(client: TestClient) -> None:
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token",
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert r.status_code == HTTPStatus.FORBIDDEN
