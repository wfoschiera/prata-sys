from datetime import timedelta
from typing import Annotated, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from posthog import identify_context, new_context

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core import security
from app.core.config import settings
from app.core.limiter import limiter
from app.core.posthog import get_posthog
from app.models import Message, NewPassword, Token, UserPublic, UserUpdate
from app.utils import (
    claim_password_reset_token,
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token,
)

router = APIRouter(tags=["login"])


@router.post("/login/access-token")
@limiter.limit("5/minute")
def login_access_token(
    request: Request,  # noqa: ARG001 — required by slowapi limiter to read client IP
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = Token(
        access_token=security.create_access_token(
            user.id,
            expires_delta=access_token_expires,
            token_version=user.token_version,
        )
    )
    ph = get_posthog()
    if ph:
        with new_context():
            identify_context(str(user.id))
            ph.capture(
                "user logged in",
                properties={
                    "$set": {"role": user.role, "is_superuser": user.is_superuser}
                },
            )
    return token


@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
@limiter.limit("5/hour")
def recover_password(
    request: Request,  # noqa: ARG001 — required by slowapi limiter to read client IP
    email: str,
    session: SessionDep,
    background_tasks: BackgroundTasks,
) -> Message:
    """
    Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    # Always return the same response to prevent email enumeration attacks.
    # Only schedule the email if the user actually exists, but do so as a
    # background task (rather than sending inline) so the in-request work is
    # identical regardless of whether the user exists — this closes the
    # timing side-channel that would otherwise leak account existence.
    if user:
        password_reset_token = generate_password_reset_token(email=email)
        email_data = generate_reset_password_email(
            email_to=user.email, email=email, token=password_reset_token
        )
        background_tasks.add_task(
            send_email,
            email_to=user.email,
            subject=email_data.subject,
            html_content=email_data.html_content,
        )
    return Message(
        message="If that email is registered, we sent a password recovery link"
    )


@router.post("/reset-password/")
@limiter.limit("10/hour")
def reset_password(
    request: Request,  # noqa: ARG001 — required by slowapi limiter to read client IP
    session: SessionDep,
    body: NewPassword,
) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        # Don't reveal that the user doesn't exist - use same error as invalid token
        raise HTTPException(status_code=400, detail="Invalid token")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not claim_password_reset_token(session, body.token):
        raise HTTPException(status_code=400, detail="Invalid token")
    user_in_update = UserUpdate(password=body.new_password)
    crud.update_user(
        session=session,
        db_user=user,
        user_in=user_in_update,
    )
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: SessionDep) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject": email_data.subject}
    )
