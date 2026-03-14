import uuid
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

router = APIRouter(prefix="/products", tags=["products"])

ViewGuard = Depends(require_permission("view_estoque"))
ManageGuard = Depends(require_permission("manage_estoque"))


def _to_product_read(p: Product) -> ProductRead:

    fornecedor_ref = None
    if p.fornecedor is not None:
        fornecedor_ref = FornecedorRef(
            id=p.fornecedor.id, company_name=p.fornecedor.company_name
        )
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
    )


@router.post("", response_model=ProductRead, status_code=HTTPStatus.CREATED)
def create_product(
    session: SessionDep,
    body: ProductCreate,
    _: None = ManageGuard,
) -> ProductRead:
    product = crud.create_product(session=session, product_in=body)
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
    return [_to_product_read(p) for p in products]


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
    return _to_product_read(product)


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
    updated = crud.update_product(session=session, product=product, product_in=body)
    return _to_product_read(updated)


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
