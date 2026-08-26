import uuid
from datetime import date
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, Request

import app.crud as crud
from app.api.deps import SessionDep, require_permission
from app.core.permissions import get_effective_permissions
from app.models import (
    CustoAjusteCreate,
    CustoAjusteRead,
    EntradaEstoque,
    EntradaEstoqueCreate,
    EntradaEstoqueListRead,
    EntradaEstoqueRead,
    EntradaItemRead,
    FornecedorRef,
    ProductRef,
    User,
)

router = APIRouter(prefix="/entradas-estoque", tags=["entradas-estoque"])

ViewGuard = Depends(require_permission("view_estoque"))
ManageGuard = Depends(require_permission("manage_estoque"))

_PERMISSIONS_CACHE_KEY = "_cached_permissions"


def _has_permission(
    request: Request, session: SessionDep, user: User, permission: str
) -> bool:
    """Imperative permission check reusing the per-request cache from deps."""
    if user.is_superuser:
        return True
    if not hasattr(request.state, _PERMISSIONS_CACHE_KEY):
        request.state._cached_permissions = get_effective_permissions(session, user)
    effective: set[str] = request.state._cached_permissions
    return permission in effective


def _fornecedor_ref(entrada: EntradaEstoque) -> FornecedorRef | None:
    if entrada.fornecedor is None:
        return None
    return FornecedorRef(
        id=entrada.fornecedor.id, company_name=entrada.fornecedor.company_name
    )


def _to_entrada_read(entrada: EntradaEstoque) -> EntradaEstoqueRead:
    total_produtos, total_ajustes, reais = crud.compute_entrada_costs(entrada)
    itens = [
        EntradaItemRead(
            id=item.id,
            product_id=item.product_id,
            product=(
                ProductRef(id=item.product.id, name=item.product.name)
                if item.product is not None
                else None
            ),
            quantity=item.quantity,
            status=item.status,
            custo_unitario_nf=item.custo_unitario_nf,
            custo_unitario_real=reais.get(item.id),
        )
        for item in entrada.items
    ]
    return EntradaEstoqueRead(
        id=entrada.id,
        fornecedor_id=entrada.fornecedor_id,
        fornecedor=_fornecedor_ref(entrada),
        data_entrada=entrada.data_entrada,
        numero_documento=entrada.numero_documento,
        observacao=entrada.observacao,
        transacao_id=entrada.transacao_id,
        total_produtos=total_produtos,
        total_ajustes=total_ajustes,
        total_real=total_produtos + total_ajustes,
        itens=itens,
        ajustes=[CustoAjusteRead.model_validate(a) for a in entrada.ajustes],
        created_at=entrada.created_at,
        updated_at=entrada.updated_at,
    )


def _to_entrada_list_read(entrada: EntradaEstoque) -> EntradaEstoqueListRead:
    total_produtos, total_ajustes, _ = crud.compute_entrada_costs(entrada)
    return EntradaEstoqueListRead(
        id=entrada.id,
        fornecedor_id=entrada.fornecedor_id,
        fornecedor=_fornecedor_ref(entrada),
        data_entrada=entrada.data_entrada,
        numero_documento=entrada.numero_documento,
        transacao_id=entrada.transacao_id,
        total_produtos=total_produtos,
        total_ajustes=total_ajustes,
        total_real=total_produtos + total_ajustes,
        created_at=entrada.created_at,
    )


@router.post("", response_model=EntradaEstoqueRead, status_code=HTTPStatus.CREATED)
def create_entrada_estoque(
    request: Request,
    session: SessionDep,
    body: EntradaEstoqueCreate,
    current_user: User = ManageGuard,
) -> EntradaEstoqueRead:
    # Booking the expense writes to the financial ledger, so it needs finance
    # rights on top of stock rights. Checked before anything is created.
    if body.criar_transacao and not _has_permission(
        request, session, current_user, "manage_financeiro"
    ):
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN, detail="Insufficient permissions"
        )
    try:
        entrada = crud.create_entrada_estoque(
            session=session, entrada_in=body, created_by_id=current_user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(exc))
    return _to_entrada_read(entrada)


@router.get("", response_model=list[EntradaEstoqueListRead])
def list_entradas_estoque(
    session: SessionDep,
    fornecedor_id: uuid.UUID | None = None,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    _: None = ViewGuard,
) -> list[EntradaEstoqueListRead]:
    entradas = crud.get_entradas_estoque(
        session=session,
        fornecedor_id=fornecedor_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
    )
    return [_to_entrada_list_read(e) for e in entradas]


@router.get("/{entrada_id}", response_model=EntradaEstoqueRead)
def get_entrada_estoque(
    entrada_id: uuid.UUID,
    session: SessionDep,
    _: None = ViewGuard,
) -> EntradaEstoqueRead:
    entrada = crud.get_entrada_estoque(session=session, entrada_id=entrada_id)
    if not entrada:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="EntradaEstoque not found"
        )
    return _to_entrada_read(entrada)


@router.post(
    "/{entrada_id}/ajustes",
    response_model=CustoAjusteRead,
    status_code=HTTPStatus.CREATED,
)
def create_custo_ajuste(
    entrada_id: uuid.UUID,
    session: SessionDep,
    body: CustoAjusteCreate,
    _: None = ManageGuard,
) -> CustoAjusteRead:
    try:
        ajuste = crud.add_custo_ajuste(
            session=session, entrada_id=entrada_id, ajuste_in=body
        )
    except ValueError as exc:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(exc))
    return CustoAjusteRead.model_validate(ajuste)


@router.delete("/{entrada_id}/ajustes/{ajuste_id}", status_code=HTTPStatus.NO_CONTENT)
def delete_custo_ajuste(
    entrada_id: uuid.UUID,
    ajuste_id: uuid.UUID,
    session: SessionDep,
    _: None = ManageGuard,
) -> None:
    try:
        crud.delete_custo_ajuste(
            session=session, entrada_id=entrada_id, ajuste_id=ajuste_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(exc))
