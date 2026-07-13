from http import HTTPStatus

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import User, UserCreate, UserUpdate
from tests.utils.user import user_authentication_headers
from tests.utils.utils import random_email, random_lower_string


def test_old_token_rejected_after_self_password_change(
    client: TestClient, db: Session
) -> None:
    """Changing a user's own password must bump token_version and
    invalidate previously-issued access tokens (SEC-003)."""
    email = random_email()
    old_password = random_lower_string()
    new_password = random_lower_string()
    user_in = UserCreate(email=email, password=old_password)
    crud.create_user(session=db, user_create=user_in)

    old_token_headers = user_authentication_headers(
        client=client, email=email, password=old_password
    )

    # Sanity check: the freshly issued token is valid before the password change.
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=old_token_headers
    )
    assert r.status_code == HTTPStatus.OK

    r = client.patch(
        f"{settings.API_V1_STR}/users/me/password",
        headers=old_token_headers,
        json={"current_password": old_password, "new_password": new_password},
    )
    assert r.status_code == HTTPStatus.OK

    r = client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=old_token_headers
    )
    assert r.status_code == HTTPStatus.FORBIDDEN

    # A fresh login with the new password issues a valid token again.
    new_token_headers = user_authentication_headers(
        client=client, email=email, password=new_password
    )
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=new_token_headers
    )
    assert r.status_code == HTTPStatus.OK


def test_old_token_rejected_after_reset_password(
    client: TestClient, db: Session
) -> None:
    """Resetting a password via the recovery flow (crud.update_user) must
    also bump token_version and invalidate previously-issued access tokens."""
    email = random_email()
    old_password = random_lower_string()
    new_password = random_lower_string()
    user_in = UserCreate(email=email, password=old_password)
    user = crud.create_user(session=db, user_create=user_in)

    old_token_headers = user_authentication_headers(
        client=client, email=email, password=old_password
    )

    crud.update_user(
        session=db, db_user=user, user_in=UserUpdate(password=new_password)
    )

    r = client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=old_token_headers
    )
    assert r.status_code == HTTPStatus.FORBIDDEN

    new_token_headers = user_authentication_headers(
        client=client, email=email, password=new_password
    )
    r = client.post(
        f"{settings.API_V1_STR}/login/test-token", headers=new_token_headers
    )
    assert r.status_code == HTTPStatus.OK


def test_user_model_defaults_token_version_to_zero(db: Session) -> None:
    email = random_email()
    password = random_lower_string()
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    assert user.token_version == 0

    stored = db.get(User, user.id)
    assert stored is not None
    assert stored.token_version == 0
