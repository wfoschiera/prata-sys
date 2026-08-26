import uuid
from datetime import date
from decimal import Decimal
from http import HTTPStatus

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

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
    ImportacaoAjusteSugerido,
    ImportacaoItemPreview,
    ImportacaoNfePreview,
    ProductRef,
    TipoCustoAjuste,
    User,
)
from app.nfe import NfeParseError, parse_nfe_xml

router = APIRouter(prefix="/entradas-estoque", tags=["entradas-estoque"])

# NF-e files are tens of KB at most; anything larger is not an invoice.
MAX_XML_BYTES = 512 * 1024

ViewGuard = Depends(require_permission("view_estoque"))
ManageGuard = Depends(require_permission("manage_estoque"))

_PERMISSIONS_CACHE_KEY = "_cached_permissions"


@router.post(
    "/importar-xml",
    response_model=ImportacaoNfePreview,
    responses={409: {"description": "Chave de acesso já importada"}},
)
def importar_nfe_xml(
    session: SessionDep,
    file: UploadFile = File(...),  # noqa: B008
    _: None = ManageGuard,
) -> ImportacaoNfePreview:
    """Parse an NF-e XML into a preview. Persists nothing.

    Submission happens through the regular create endpoint after the user
    resolves product matches in the UI (parse-preview-submit, phase-12).
    """
    data = file.file.read()
    if len(data) > MAX_XML_BYTES:
        raise HTTPException(
            status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
            detail="Arquivo muito grande. O XML de uma NF-e tem poucas dezenas de KB.",
        )
    try:
        parsed = parse_nfe_xml(data)
    except NfeParseError as exc:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY, detail=str(exc))

    existing = crud.find_entrada_by_numero_documento(
        session=session, numero_documento=parsed.chave
    )
    if existing is not None:
        raise HTTPException(
            status_code=HTTPStatus.CONFLICT,
            detail={
                "message": "Esta nota já foi importada.",
                "existing_entrada_id": str(existing.id),
            },
        )

    fornecedor = (
        crud.find_fornecedor_by_cnpj(
            session=session, cnpj_digits=parsed.emitter_cnpj_digits
        )
        if parsed.emitter_cnpj_digits
        else None
    )

    suggestions = crud.suggest_products_for_lines(
        session=session,
        fornecedor_id=fornecedor.id if fornecedor else None,
        descriptions=[item.description for item in parsed.items],
    )
    itens = [
        ImportacaoItemPreview(
            description=item.description,
            product_code=item.product_code,
            quantity=item.quantity,
            custo_unitario_nf=item.unit_price,
            unit=item.unit,
            cfop=item.cfop,
            product_sugerido_id=product.id if product else None,
            product_sugerido_name=product.name if product else None,
            match_status=status,
        )
        for item, (status, product) in zip(parsed.items, suggestions, strict=True)
    ]

    chave = parsed.chave
    totals = parsed.totals

    def _sugerido(tipo: TipoCustoAjuste, valor: Decimal | None) -> ImportacaoAjusteSugerido | None:
        if valor is None or valor <= 0:
            return None
        return ImportacaoAjusteSugerido(
            tipo=tipo, valor=valor, documento_referencia=chave
        )

    ajustes_sugeridos_raw = [
        _sugerido(TipoCustoAjuste.frete, totals.freight),
        _sugerido(TipoCustoAjuste.seguro, totals.insurance),
        _sugerido(TipoCustoAjuste.icms_st, totals.icms_st),
        _sugerido(TipoCustoAjuste.ipi, totals.ipi),
        (
            ImportacaoAjusteSugerido(
                tipo=TipoCustoAjuste.desconto_comercial,
                valor=-totals.discount,
                documento_referencia=chave,
            )
            if totals.discount is not None and totals.discount > 0
            else None
        ),
    ]
    ajustes_sugeridos = [a for a in ajustes_sugeridos_raw if a is not None]

    return ImportacaoNfePreview(
        chave=chave,
        numero_nota=parsed.numero,
        data_entrada=parsed.emission_date,
        emitter_cnpj_digits=parsed.emitter_cnpj_digits,
        fornecedor_sugerido=(
            FornecedorRef(id=fornecedor.id, company_name=fornecedor.company_name)
            if fornecedor
            else None
        ),
        itens=itens,
        ajustes_sugeridos=ajustes_sugeridos,
        totals_produtos=totals.products,
        totals_nota=totals.invoice_total,
    )


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
