import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

from app import crud
from app.api.deps import SessionDep, require_role
from app.models import (
    Message,
    Service,
    ServiceCreate,
    ServiceItem,
    ServiceItemCreate,
    ServiceItemRead,
    ServiceRead,
    ServicesPublic,
    ServiceUpdate,
)

router = APIRouter(prefix="/services", tags=["services"])

RoleGuard = Depends(require_role("admin", "finance"))


@router.get("/", response_model=ServicesPublic)
def read_services(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    _: None = RoleGuard,
) -> ServicesPublic:
    """List all services (admin and finance only)."""
    services, count = crud.get_services(session=session, skip=skip, limit=limit)
    return ServicesPublic(data=services, count=count)


@router.post("/", response_model=ServiceRead, status_code=201)
def create_service(
    *,
    session: SessionDep,
    service_in: ServiceCreate,
    _: None = RoleGuard,
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
    _: None = RoleGuard,
) -> Service:
    """Get a service order by ID."""
    db_service = crud.get_service(session=session, service_id=service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    return db_service


@router.patch("/{service_id}", response_model=ServiceRead)
def update_service(
    *,
    session: SessionDep,
    service_id: uuid.UUID,
    service_in: ServiceUpdate,
    _: None = RoleGuard,
) -> Service:
    """Update a service order (status transitions are enforced)."""
    db_service = crud.get_service(session=session, service_id=service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    try:
        return crud.update_service(session=session, db_service=db_service, service_in=service_in)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.delete("/{service_id}", status_code=204)
def delete_service(
    *,
    session: SessionDep,
    service_id: uuid.UUID,
    _: None = RoleGuard,
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
    _: None = RoleGuard,
) -> ServiceItem:
    """Add a line item to a service order."""
    db_service = crud.get_service(session=session, service_id=service_id)
    if not db_service:
        raise HTTPException(status_code=404, detail="Service not found")
    return crud.create_service_item(session=session, service_id=service_id, item_in=item_in)


@router.delete("/{service_id}/items/{item_id}", status_code=204)
def delete_service_item(
    *,
    session: SessionDep,
    service_id: uuid.UUID,
    item_id: uuid.UUID,
    _: None = RoleGuard,
) -> None:
    """Remove a line item from a service order."""
    db_item = crud.get_service_item(session=session, item_id=item_id)
    if not db_item or db_item.service_id != service_id:
        raise HTTPException(status_code=404, detail="Item not found")
    crud.delete_service_item(session=session, db_item=db_item)
