from http import HTTPStatus

from fastapi.testclient import TestClient

from app.core.config import settings


def test_cors_preflight_allowed_origin_and_method(client: TestClient) -> None:
    """SEC-009: an allowed origin/method preflight is reflected with the
    restricted (non-wildcard) methods/headers lists."""
    origin = settings.all_cors_origins[0]
    r = client.options(
        f"{settings.API_V1_STR}/login/access-token",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert r.status_code == HTTPStatus.OK
    assert r.headers["access-control-allow-origin"] == origin
    assert "POST" in r.headers["access-control-allow-methods"]
    assert "authorization" in r.headers["access-control-allow-headers"].lower()


def test_cors_preflight_disallowed_method_not_reflected(client: TestClient) -> None:
    """A method outside the explicit allow-list is not granted by the preflight."""
    origin = settings.all_cors_origins[0]
    r = client.options(
        f"{settings.API_V1_STR}/login/access-token",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "TRACE",
        },
    )
    assert "access-control-allow-methods" not in r.headers or "TRACE" not in (
        r.headers.get("access-control-allow-methods", "")
    )


def test_cors_preflight_disallowed_origin_not_reflected(client: TestClient) -> None:
    """An origin outside the configured allow-list gets no CORS headers."""
    r = client.options(
        f"{settings.API_V1_STR}/login/access-token",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in r.headers
