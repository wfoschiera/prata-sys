import uuid
from decimal import Decimal
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

import app.crud as crud
from app.api.deps import SessionDep, require_permission
from app.models import (
    FornecedorRef,
    Product,
    ProductCategory,
    ProductCreate,
    ProductItemRead,
    ProductRead,
    ProductTypeRead,
    ProductUpdate,
    StockPredictionRead,
)

_NO_COST: tuple[Decimal | None, int] = (None, 0)

router = APIRouter(prefix="/products", tags=["products"])

ViewGuard = Depends(require_permission("view_estoque"))
ManageGuard = Depends(require_permission("manage_estoque"))


def _to_product_read(
    p: Product, costs: tuple[Decimal | None, int] = _NO_COST
) -> ProductRead:

    fornecedor_ref = None
    if p.fornecedor is not None:
        fornecedor_ref = FornecedorRef(
            id=p.fornecedor.id, company_name=p.fornecedor.company_name
        )
    custo_medio, lotes_sem_custo = costs
    return ProductRead(
        id=p.id,
        product_type_id=p.product_type_id,
        product_type=ProductTypeRead.model_validate(p.product_type),
        name=p.name,
        fornecedor_id=p.fornecedor_id,
        fornecedor=fornecedor_ref,
        unit_price=p.unit_price,
        description=p.description,
        created_at=p.created_at,
        custo_medio_ponderado=custo_medio,
        lotes_sem_custo=lotes_sem_custo,
    )


@router.post("", response_model=ProductRead, status_code=HTTPStatus.CREATED)
def create_product(
    session: SessionDep,
    body: ProductCreate,
    _: None = ManageGuard,
) -> ProductRead:
    try:
        product = crud.create_product(session=session, product_in=body)
    except ValueError as exc:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(exc))
    return _to_product_read(product)


@router.get("", response_model=list[ProductRead])
def list_products(
    session: SessionDep,
    category: ProductCategory | None = None,
    fornecedor_id: uuid.UUID | None = None,
    _: None = ViewGuard,
) -> list[ProductRead]:
    products = crud.get_products(
        session=session, category=category, fornecedor_id=fornecedor_id
    )
    # One aggregate for the whole page, not one per product.
    costs = crud.get_custo_medio_ponderado(
        session=session, product_ids=[p.id for p in products]
    )
    return [_to_product_read(p, costs.get(p.id, _NO_COST)) for p in products]


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: uuid.UUID,
    session: SessionDep,
    _: None = ViewGuard,
) -> ProductRead:
    product = crud.get_product(session=session, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Product not found"
        )
    costs = crud.get_custo_medio_ponderado(session=session, product_ids=[product.id])
    return _to_product_read(product, costs.get(product.id, _NO_COST))


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: uuid.UUID,
    session: SessionDep,
    body: ProductUpdate,
    _: None = ManageGuard,
) -> ProductRead:
    product = crud.get_product(session=session, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Product not found"
        )
    try:
        updated = crud.update_product(session=session, product=product, product_in=body)
    except ValueError as exc:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(exc))
    costs = crud.get_custo_medio_ponderado(session=session, product_ids=[updated.id])
    return _to_product_read(updated, costs.get(updated.id, _NO_COST))


@router.delete("/{product_id}", status_code=HTTPStatus.NO_CONTENT)
def delete_product(
    product_id: uuid.UUID,
    session: SessionDep,
    _: None = ManageGuard,
) -> None:
    product = crud.get_product(session=session, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Product not found"
        )
    try:
        crud.delete_product(session=session, product_id=product_id)
    except ValueError as exc:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(exc))


@router.get("/{product_id}/items", response_model=list[ProductItemRead])
def get_product_items(
    product_id: uuid.UUID,
    session: SessionDep,
    _: None = ViewGuard,
) -> list[ProductItemRead]:
    product = crud.get_product(session=session, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Product not found"
        )
    items = crud.get_product_items_by_product(session=session, product_id=product_id)
    return [ProductItemRead.model_validate(i) for i in items]


@router.get("/{product_id}/prediction", response_model=StockPredictionRead)
def get_product_prediction(
    product_id: uuid.UUID,
    session: SessionDep,
    _: None = ViewGuard,
) -> StockPredictionRead:
    product = crud.get_product(session=session, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Product not found"
        )
    return crud.get_stock_prediction(session=session, product_id=product_id)
