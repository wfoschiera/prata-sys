import uuid
from datetime import date
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep, require_permission
from app.models import (
    Client,
    Orcamento,
    OrcamentoCreate,
    OrcamentoItem,
    OrcamentoItemCreate,
    OrcamentoItemRead,
    OrcamentoItemUpdate,
    OrcamentoRead,
    OrcamentosPublic,
    OrcamentoStatus,
    OrcamentoTransitionRequest,
    OrcamentoTransitionResponse,
    OrcamentoUpdate,
    Service,
    ServiceRead,
)

router = APIRouter(prefix="/orcamentos", tags=["orcamentos"])

ManageGuard = Depends(require_permission("manage_orcamentos"))


# ── Orçamento CRUD ─────────────────────────────────────────────────────────────


@router.get("/", response_model=OrcamentosPublic)
def list_orcamentos(
    session: SessionDep,
    search: str | None = None,
    status: OrcamentoStatus | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    skip: int = 0,
    limit: int = 20,
    _: None = ManageGuard,
) -> OrcamentosPublic:
    """List orçamentos with filters and pagination."""
    orcamentos, count = crud.get_orcamentos(
        session=session,
        search=search,
        status=status,
        data_inicio=data_inicio,
        data_fim=data_fim,
        skip=skip,
        limit=limit,
    )
    return OrcamentosPublic(data=orcamentos, count=count)


@router.post("/", response_model=OrcamentoRead, status_code=HTTPStatus.CREATED)
def create_orcamento(
    session: SessionDep,
    body: OrcamentoCreate,
    current_user: CurrentUser,
    _: None = ManageGuard,
) -> Orcamento:
    """Create a new orçamento."""
    client = session.get(Client, body.client_id)
    if not client:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Cliente não encontrado"
        )
    try:
        return crud.create_orcamento(
            session=session, orcamento_in=body, created_by_id=current_user.id
        )
    except ValueError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@router.get("/{orcamento_id}", response_model=OrcamentoRead)
def read_orcamento(
    session: SessionDep,
    orcamento_id: uuid.UUID,
    _: None = ManageGuard,
) -> Orcamento:
    """Get a single orçamento with full detail."""
    db_orc = crud.get_orcamento(session=session, orcamento_id=orcamento_id)
    if not db_orc:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Orçamento não encontrado"
        )
    return db_orc


@router.patch("/{orcamento_id}", response_model=OrcamentoRead)
def update_orcamento(
    session: SessionDep,
    orcamento_id: uuid.UUID,
    body: OrcamentoUpdate,
    _: None = ManageGuard,
) -> Orcamento:
    """Update an orçamento (only when rascunho or em_análise)."""
    db_orc = crud.get_orcamento(session=session, orcamento_id=orcamento_id)
    if not db_orc:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Orçamento não encontrado"
        )
    try:
        return crud.update_orcamento(
            session=session, db_orcamento=db_orc, orcamento_in=body
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@router.delete("/{orcamento_id}", status_code=HTTPStatus.NO_CONTENT)
def delete_orcamento(
    session: SessionDep,
    orcamento_id: uuid.UUID,
    _: None = ManageGuard,
) -> None:
    """Delete an orçamento (only when rascunho)."""
    db_orc = crud.get_orcamento(session=session, orcamento_id=orcamento_id)
    if not db_orc:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Orçamento não encontrado"
        )
    try:
        crud.delete_orcamento(session=session, db_orcamento=db_orc)
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc)
        )


# ── Status transitions ─────────────────────────────────────────────────────────


@router.post("/{orcamento_id}/transition", response_model=OrcamentoTransitionResponse)
def transition_orcamento(
    session: SessionDep,
    orcamento_id: uuid.UUID,
    body: OrcamentoTransitionRequest,
    current_user: CurrentUser,
    _: None = ManageGuard,
) -> OrcamentoTransitionResponse:
    """Change orçamento status."""
    db_orc = crud.get_orcamento(session=session, orcamento_id=orcamento_id)
    if not db_orc:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Orçamento não encontrado"
        )
    try:
        updated = crud.transition_orcamento_status(
            session=session,
            orcamento=db_orc,
            to_status=body.to_status,
            changed_by_id=current_user.id,
            reason=body.reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc)
        )
    return OrcamentoTransitionResponse(orcamento=updated)


# ── Convert to Service ─────────────────────────────────────────────────────────


@router.post("/{orcamento_id}/convert-to-service", response_model=ServiceRead)
def convert_to_service(
    session: SessionDep,
    orcamento_id: uuid.UUID,
    current_user: CurrentUser,
    _: None = ManageGuard,
) -> Service:
    """Create a Service from an approved orçamento (one-time only)."""
    db_orc = crud.get_orcamento(session=session, orcamento_id=orcamento_id)
    if not db_orc:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Orçamento não encontrado"
        )
    try:
        return crud.convert_orcamento_to_service(
            session=session, orcamento=db_orc, created_by_id=current_user.id
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc)
        )


# ── Duplicate ──────────────────────────────────────────────────────────────────


@router.post(
    "/{orcamento_id}/duplicate",
    response_model=OrcamentoRead,
    status_code=HTTPStatus.CREATED,
)
def duplicate_orcamento(
    session: SessionDep,
    orcamento_id: uuid.UUID,
    current_user: CurrentUser,
    _: None = ManageGuard,
) -> Orcamento:
    """Create a copy of an orçamento as a new rascunho."""
    db_orc = crud.get_orcamento(session=session, orcamento_id=orcamento_id)
    if not db_orc:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Orçamento não encontrado"
        )
    return crud.duplicate_orcamento(
        session=session, orcamento=db_orc, created_by_id=current_user.id
    )


# ── Orçamento Items ────────────────────────────────────────────────────────────


@router.post(
    "/{orcamento_id}/items",
    response_model=OrcamentoItemRead,
    status_code=HTTPStatus.CREATED,
)
def create_orcamento_item(
    session: SessionDep,
    orcamento_id: uuid.UUID,
    body: OrcamentoItemCreate,
    _: None = ManageGuard,
) -> OrcamentoItem:
    """Add an item to an orçamento."""
    try:
        return crud.create_orcamento_item(
            session=session, orcamento_id=orcamento_id, item_in=body
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@router.patch("/{orcamento_id}/items/{item_id}", response_model=OrcamentoItemRead)
def update_orcamento_item(
    session: SessionDep,
    orcamento_id: uuid.UUID,
    item_id: uuid.UUID,
    body: OrcamentoItemUpdate,
    _: None = ManageGuard,
) -> OrcamentoItem:
    """Update an orçamento item."""
    db_item = session.get(OrcamentoItem, item_id)
    if not db_item or db_item.orcamento_id != orcamento_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Item não encontrado"
        )
    try:
        return crud.update_orcamento_item(
            session=session, db_item=db_item, item_in=body
        )
    except ValueError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc)
        )


@router.delete("/{orcamento_id}/items/{item_id}", status_code=HTTPStatus.NO_CONTENT)
def delete_orcamento_item(
    session: SessionDep,
    orcamento_id: uuid.UUID,
    item_id: uuid.UUID,
    _: None = ManageGuard,
) -> None:
    """Remove an item from an orçamento."""
    db_item = session.get(OrcamentoItem, item_id)
    if not db_item or db_item.orcamento_id != orcamento_id:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Item não encontrado"
        )
    try:
        crud.delete_orcamento_item(session=session, db_item=db_item)
    except ValueError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc)
        )
