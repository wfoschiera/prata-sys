from fastapi import APIRouter, Depends

import app.crud as crud
from app.api.deps import SessionDep, require_permission
from app.models import CategoryDashboardItem

router = APIRouter(prefix="/estoque", tags=["estoque"])

ViewGuard = Depends(require_permission("view_estoque"))


@router.get("/dashboard", response_model=list[CategoryDashboardItem])
def get_dashboard(
    session: SessionDep,
    _: None = ViewGuard,
) -> list[CategoryDashboardItem]:
    return crud.get_stock_dashboard(session=session)
