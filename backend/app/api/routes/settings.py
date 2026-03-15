from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, get_current_active_superuser, require_permission
from app.models import CompanySettings, CompanySettingsRead, CompanySettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])

ViewGuard = Depends(require_permission("view_dashboard"))


@router.get("/empresa", response_model=CompanySettingsRead)
def get_company_settings(
    session: SessionDep,
    _: None = ViewGuard,
) -> CompanySettingsRead:
    """Get company settings for document headers."""
    settings = session.get(CompanySettings, 1)
    if settings is None:
        # Return defaults if not yet configured
        return CompanySettingsRead(company_name="Empresa não configurada")
    return CompanySettingsRead.model_validate(settings)


@router.put(
    "/empresa",
    response_model=CompanySettingsRead,
    dependencies=[Depends(get_current_active_superuser)],
)
def update_company_settings(
    session: SessionDep,
    body: CompanySettingsUpdate,
) -> CompanySettingsRead:
    """Update company settings. Admin only."""
    settings = session.get(CompanySettings, 1)
    if settings is None:
        # First time — create
        update_data = body.model_dump(exclude_unset=True)
        settings = CompanySettings(
            id=1, company_name=update_data.get("company_name", "")
        )
        for key, value in update_data.items():
            setattr(settings, key, value)
        session.add(settings)
    else:
        update_data = body.model_dump(exclude_unset=True)
        settings.sqlmodel_update(update_data)
        session.add(settings)
    session.commit()
    session.refresh(settings)
    return CompanySettingsRead.model_validate(settings)
