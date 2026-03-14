import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app import crud
from app.api.deps import SessionDep, require_permission
from app.models import (
    CategoriaTransacao,
    ResumoMensal,
    TipoTransacao,
    Transacao,
    TransacaoCreate,
    TransacaoPublic,
    TransacaoUpdate,
    TransacoesPublic,
)

router = APIRouter(prefix="/transacoes", tags=["transacoes"])

ViewGuard = Depends(require_permission("view_financeiro"))
ManageGuard = Depends(require_permission("manage_financeiro"))


@router.get("/resumo", response_model=ResumoMensal)
def get_resumo_mensal(
    session: SessionDep,
    ano: int = Query(default=datetime.now(timezone.utc).year),
    mes: int = Query(default=datetime.now(timezone.utc).month, ge=1, le=12),
    _: None = ViewGuard,
) -> ResumoMensal:
    """Monthly financial summary: total receitas, total despesas, resultado líquido."""
    return crud.get_resumo_mensal(session=session, ano=ano, mes=mes)


@router.get("/", response_model=TransacoesPublic)
def read_transacoes(
    session: SessionDep,
    tipo: TipoTransacao | None = None,
    categoria: CategoriaTransacao | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    service_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    _: None = ViewGuard,
) -> TransacoesPublic:
    """List transactions with optional filters."""
    transacoes, count = crud.get_transacoes(
        session=session,
        tipo=tipo,
        categoria=categoria,
        data_inicio=data_inicio,
        data_fim=data_fim,
        service_id=service_id,
        skip=skip,
        limit=limit,
    )
    return TransacoesPublic(data=transacoes, count=count)


@router.post("/", response_model=TransacaoPublic, status_code=201)
def create_transacao(
    session: SessionDep,
    transacao_in: TransacaoCreate,
    _: None = ManageGuard,
) -> TransacaoPublic:
    """Create a new transaction."""
    return crud.create_transacao(session=session, transacao_in=transacao_in)


@router.get("/{transacao_id}", response_model=TransacaoPublic)
def read_transacao(
    session: SessionDep,
    transacao_id: uuid.UUID,
    _: None = ViewGuard,
) -> TransacaoPublic:
    """Get a single transaction by ID."""
    transacao = crud.get_transacao(session=session, transacao_id=transacao_id)
    if transacao is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transacao


@router.patch("/{transacao_id}", response_model=TransacaoPublic)
def update_transacao(
    session: SessionDep,
    transacao_id: uuid.UUID,
    transacao_in: TransacaoUpdate,
    _: None = ManageGuard,
) -> TransacaoPublic:
    """Update a transaction. tipo is immutable."""
    db_transacao = session.get(Transacao, transacao_id)
    if db_transacao is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return crud.update_transacao(
        session=session, db_transacao=db_transacao, transacao_in=transacao_in
    )


@router.delete("/{transacao_id}", status_code=204)
def delete_transacao(
    session: SessionDep,
    transacao_id: uuid.UUID,
    _: None = ManageGuard,
) -> None:
    """Delete a transaction."""
    db_transacao = session.get(Transacao, transacao_id)
    if db_transacao is None:
        raise HTTPException(status_code=404, detail="Transaction not found")
    crud.delete_transacao(session=session, db_transacao=db_transacao)
