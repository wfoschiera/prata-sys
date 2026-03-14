import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

import app.crud as crud
from app.api.deps import SessionDep, require_permission
from app.models import ProductTypeCreate, ProductTypeRead, ProductTypeUpdate

router = APIRouter(prefix="/product-types", tags=["product-types"])

ViewGuard = Depends(require_permission("view_estoque"))
ManageGuard = Depends(require_permission("manage_estoque"))


@router.post("", response_model=ProductTypeRead, status_code=HTTPStatus.CREATED)
def create_product_type(
    session: SessionDep,
    body: ProductTypeCreate,
    _: None = ManageGuard,
) -> ProductTypeRead:
    try:
        pt = crud.create_product_type(session=session, pt_in=body)
    except ValueError as exc:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(exc))
    return ProductTypeRead.model_validate(pt)


@router.get("", response_model=list[ProductTypeRead])
def list_product_types(
    session: SessionDep,
    _: None = ViewGuard,
) -> list[ProductTypeRead]:
    pts = crud.get_product_types(session=session)
    return [ProductTypeRead.model_validate(pt) for pt in pts]


@router.get("/{product_type_id}", response_model=ProductTypeRead)
def get_product_type(
    product_type_id: uuid.UUID,
    session: SessionDep,
    _: None = ViewGuard,
) -> ProductTypeRead:
    pt = crud.get_product_type(session=session, product_type_id=product_type_id)
    if not pt:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="ProductType not found"
        )
    return ProductTypeRead.model_validate(pt)


@router.patch("/{product_type_id}", response_model=ProductTypeRead)
def update_product_type(
    product_type_id: uuid.UUID,
    session: SessionDep,
    body: ProductTypeUpdate,
    _: None = ManageGuard,
) -> ProductTypeRead:
    pt = crud.get_product_type(session=session, product_type_id=product_type_id)
    if not pt:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="ProductType not found"
        )
    updated = crud.update_product_type(session=session, pt=pt, pt_in=body)
    return ProductTypeRead.model_validate(updated)


@router.delete("/{product_type_id}", status_code=HTTPStatus.NO_CONTENT)
def delete_product_type(
    product_type_id: uuid.UUID,
    session: SessionDep,
    _: None = ManageGuard,
) -> None:
    pt = crud.get_product_type(session=session, product_type_id=product_type_id)
    if not pt:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="ProductType not found"
        )
    try:
        crud.delete_product_type(session=session, product_type_id=product_type_id)
    except ValueError as exc:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail=str(exc))
