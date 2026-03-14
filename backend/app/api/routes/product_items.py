import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException

import app.crud as crud
from app.api.deps import SessionDep, require_permission
from app.models import ProductItemCreate, ProductItemRead, ProductItemStatus

router = APIRouter(prefix="/product-items", tags=["product-items"])

ViewGuard = Depends(require_permission("view_estoque"))
ManageGuard = Depends(require_permission("manage_estoque"))


@router.post("", response_model=ProductItemRead, status_code=HTTPStatus.CREATED)
def create_product_item(
    session: SessionDep,
    body: ProductItemCreate,
    _: None = ManageGuard,
) -> ProductItemRead:
    try:
        item = crud.create_product_item(session=session, item_in=body)
    except ValueError as exc:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=str(exc))
    return ProductItemRead.model_validate(item)


@router.get("", response_model=list[ProductItemRead])
def list_product_items(
    session: SessionDep,
    product_id: uuid.UUID | None = None,
    status: ProductItemStatus | None = None,
    service_id: uuid.UUID | None = None,
    _: None = ViewGuard,
) -> list[ProductItemRead]:
    items = crud.get_product_items(
        session=session,
        product_id=product_id,
        status=status,
        service_id=service_id,
    )
    return [ProductItemRead.model_validate(i) for i in items]
