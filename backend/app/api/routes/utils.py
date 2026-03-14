from fastapi import APIRouter, Depends
from pydantic import BaseModel
from pydantic.networks import EmailStr
from sqlmodel import text

from app.api.deps import SessionDep, get_current_active_superuser
from app.models import Message
from app.utils import generate_test_email, send_email

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


class ReadinessResponse(BaseModel):
    status: str
    db: str


@router.get("/readiness/", response_model=ReadinessResponse)
def readiness_check(session: SessionDep) -> ReadinessResponse:
    """Readiness probe: verifies DB connectivity.

    Returns 200 when the DB is reachable, 503 otherwise.
    Use this for Kubernetes readinessProbe (not livenessProbe).
    """
    from fastapi import HTTPException

    try:
        session.exec(text("SELECT 1"))  # type: ignore[call-overload]
        return ReadinessResponse(status="ok", db="ok")
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=503, detail="Database unreachable")
