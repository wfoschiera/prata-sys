import pytest

from app.core.config import Settings


def _base_kwargs(**overrides: object) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "PROJECT_NAME": "Test",
        "POSTGRES_SERVER": "localhost",
        "POSTGRES_USER": "postgres",
        "POSTGRES_PASSWORD": "some-strong-password",
        "FIRST_SUPERUSER": "admin@example.com",
        "FIRST_SUPERUSER_PASSWORD": "some-strong-password",
    }
    kwargs.update(overrides)
    return kwargs


def test_missing_secret_key_raises_outside_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SEC-010: an unset SECRET_KEY must fail closed outside local dev,
    instead of silently falling back to a random per-process value."""
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValueError, match="SECRET_KEY must be set explicitly"):
        Settings(**_base_kwargs(ENVIRONMENT="production"))  # type: ignore[arg-type]


def test_explicit_secret_key_allowed_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    settings = Settings(
        **_base_kwargs(ENVIRONMENT="production", SECRET_KEY="a-real-secret-key")  # type: ignore[arg-type]
    )
    assert settings.SECRET_KEY == "a-real-secret-key"


def test_missing_secret_key_allowed_in_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    settings = Settings(**_base_kwargs(ENVIRONMENT="local"))  # type: ignore[arg-type]
    assert settings.SECRET_KEY
