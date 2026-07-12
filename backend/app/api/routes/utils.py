import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic.networks import EmailStr
from sqlmodel import select

from app.api.deps import SessionDep, get_current_active_superuser
from app.models import Message
from app.utils import generate_test_email, send_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True


@router.get("/readiness/")
def readiness(session: SessionDep) -> Message:
    """Readiness probe: verify the database is reachable.

    Returns 200 when a trivial query succeeds, 503 otherwise. Unlike
    ``health-check`` (liveness), this confirms the app can actually serve
    database-backed requests.
    """
    try:
        session.exec(select(1))
    except Exception as exc:
        logger.error("readiness check failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        ) from exc
    return Message(message="ready")
