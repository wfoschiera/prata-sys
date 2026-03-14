import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request

from app import crud
from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models import (
    Service,
    ServiceCreate,
    ServiceItem,
    ServiceItemCreate,
    ServiceItemRead,
    ServiceRead,
    ServicesPublic,
    ServiceTransitionRequest,
    ServiceTransitionResponse,
    ServiceUpdate,
)

router = APIRouter(prefix="/services", tags=["services"])

PermGuard = Depends(require_permission("manage_services"))
AdminDep = Depends(require_permission("manage_services"))


@router.get("/", response_model=ServicesPublic)
def read_services(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    _: None = PermGuard,
) -> ServicesPublic:
    """List all services (admin and finance only)."""
    services, count = crud.get_services(session=session, skip=skip, limit=limit)
    return ServicesPublic(data=services, count=count)


@router.post("/", response_model=ServiceRead, status_code=201)
def create_service(
    *,
    session: SessionDep,
    service_in: ServiceCreate,
    _: None = PermGuard,
) -> Service:
    """Create a new service order."""
    from app.models import Client

    client = session.get(Client, service_in.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return crud.create_service(session=session, service_in=service_in)


@router.get("/{service_id}", response_model=ServiceRead)
def read_service(
    *,
    session: SessionDep,
    service_id: uuid.UUID,
    _: None = PermGuard,
) -> Service:
    """Get a service order by ID."""
    db_service = crud.get_service(session=session, service_id=service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    return db_service


@router.patch("/{service_id}", response_model=ServiceRead)
async def update_service(
    *,
    request: Request,
    session: SessionDep,
    service_id: uuid.UUID,
    service_in: ServiceUpdate,
    _: None = PermGuard,
) -> Service:
    """Update a service order (status transitions are enforced)."""
    raw_body = await request.json()
    if "status" in raw_body:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail=f"Use POST /services/{service_id}/transition to change service status",
        )
    db_service = crud.get_service(session=session, service_id=service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    try:
        return crud.update_service(
            session=session, db_service=db_service, service_in=service_in
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/{service_id}/transition", response_model=ServiceTransitionResponse)
def transition_service(
    *,
    session: SessionDep,
    service_id: uuid.UUID,
    transition_in: ServiceTransitionRequest,
    current_user: CurrentUser,
    _: None = AdminDep,
) -> ServiceTransitionResponse:
    """Advance or cancel a service order status.

    Only admin users may trigger status transitions. Valid transitions:
    requested → scheduled → executing → completed (or cancelled from any non-terminal state).
    Cancellation requires a reason. Completion requires deduction_items.
    """
    db_service = crud.get_service(session=session, service_id=service_id)
    if not db_service:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Service not found"
        )
    try:
        updated_service, stock_warnings = crud.transition_service_status(
            session=session,
            service=db_service,
            to_status=transition_in.to_status,
            changed_by_id=current_user.id,
            reason=transition_in.reason,
            deduction_items=transition_in.deduction_items,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    service_read = ServiceRead.model_validate(updated_service)
    return ServiceTransitionResponse(
        service=service_read, stock_warnings=stock_warnings
    )


@router.post("/{service_id}/deduct-stock")
def deduct_stock(
    *,
    session: SessionDep,
    service_id: uuid.UUID,
    current_user: CurrentUser,
    _: None = AdminDep,
) -> list[dict]:  # type: ignore[type-arg]
    """Manually deduct material quantities from stock for a service in 'executing' status.

    Only valid when the service is in the executing state. Fully implemented in Phase 7.
    """
    db_service = crud.get_service(session=session, service_id=service_id)
    if not db_service:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Service not found"
        )
    try:
        return crud.deduct_stock(session, db_service, current_user.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@router.delete("/{service_id}", status_code=204)
def delete_service(
    *,
    session: SessionDep,
    service_id: uuid.UUID,
    _: None = PermGuard,
) -> None:
    """Delete a service order and all its items (cascade)."""
    db_service = crud.get_service(session=session, service_id=service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    crud.delete_service(session=session, db_service=db_service)


@router.post("/{service_id}/items", response_model=ServiceItemRead, status_code=201)
def create_service_item(
    *,
    session: SessionDep,
    service_id: uuid.UUID,
    item_in: ServiceItemCreate,
    _: None = PermGuard,
) -> ServiceItem:
    """Add a line item to a service order."""
    db_service = crud.get_service(session=session, service_id=service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    return crud.create_service_item(
        session=session, service_id=service_id, item_in=item_in
    )


@router.delete("/{service_id}/items/{item_id}", status_code=204)
def delete_service_item(
    *,
    session: SessionDep,
    service_id: uuid.UUID,
    item_id: uuid.UUID,
    _: None = PermGuard,
) -> None:
    """Remove a line item from a service order."""
    db_item = crud.get_service_item(session=session, item_id=item_id)
    if not db_item or db_item.service_id != service_id:
        raise HTTPException(status_code=404, detail="Item not found")
    crud.delete_service_item(session=session, db_item=db_item)
