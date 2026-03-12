import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import func, select

from app import crud
from app.api.deps import SessionDep, require_role
from app.models import (
    Client,
    ClientCreate,
    ClientPublic,
    ClientsPublic,
    ClientUpdate,
    Message,
)

router = APIRouter(prefix="/clients", tags=["clients"])

RoleGuard = Depends(require_role("admin", "finance"))


@router.get("/", response_model=ClientsPublic)
def read_clients(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    _: None = RoleGuard,
) -> ClientsPublic:
    """List clients (admin and finance only)."""
    clients, count = crud.get_clients(session=session, skip=skip, limit=limit)
    return ClientsPublic(data=clients, count=count)


@router.post("/", response_model=ClientPublic, status_code=201)
def create_client(
    *,
    session: SessionDep,
    client_in: ClientCreate,
    _: None = RoleGuard,
) -> Client:
    """Create a new client."""
    existing = crud.get_client_by_document(
        session=session, document_number=client_in.document_number
    )
    if existing:
        raise HTTPException(status_code=409, detail="Document number already registered")
    return crud.create_client(session=session, client_in=client_in)


@router.get("/{client_id}", response_model=ClientPublic)
def read_client(
    *,
    session: SessionDep,
    client_id: uuid.UUID,
    _: None = RoleGuard,
) -> Client:
    """Get a client by ID."""
    db_client = crud.get_client(session=session, client_id=client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client


@router.patch("/{client_id}", response_model=ClientPublic)
def update_client(
    *,
    session: SessionDep,
    client_id: uuid.UUID,
    client_in: ClientUpdate,
    _: None = RoleGuard,
) -> Client:
    """Update a client."""
    db_client = crud.get_client(session=session, client_id=client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    if client_in.document_number and client_in.document_number != db_client.document_number:
        existing = crud.get_client_by_document(
            session=session, document_number=client_in.document_number
        )
        if existing:
            raise HTTPException(status_code=409, detail="Document number already registered")
    return crud.update_client(session=session, db_client=db_client, client_in=client_in)


@router.delete("/{client_id}", response_model=Message)
def delete_client(
    *,
    session: SessionDep,
    client_id: uuid.UUID,
    _: None = RoleGuard,
) -> Message:
    """Delete a client."""
    db_client = crud.get_client(session=session, client_id=client_id)
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    crud.delete_client(session=session, db_client=db_client)
    return Message(message="Client deleted successfully")
