from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from app import crud
from app.api.deps import SessionDep, require_permission
from app.models import YearlyOperationalDashboard

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

ViewGuard = Depends(require_permission("view_dashboard"))


@router.get("/operational", response_model=YearlyOperationalDashboard)
def get_operational_dashboard(
    session: SessionDep,
    ano: int = Query(default_factory=lambda: datetime.now(timezone.utc).year),
    _: None = ViewGuard,
) -> YearlyOperationalDashboard:
    """Weekly operational KPIs for the given year.

    Returns a list of WeeklyOperationalSummary, one entry per ISO week
    from week 1 through the current week (or week 52 for past years).
    """
    return crud.get_yearly_operational_summary(session=session, ano=ano)
