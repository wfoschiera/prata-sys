import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select

import app.crud as crud
from app.api.deps import SessionDep, require_permission
from app.models import (
    Fornecedor,
    FornecedorCategoryEnum,
    FornecedorContato,
    FornecedorContatoCreate,
    FornecedorContatoPublic,
    FornecedorContatoUpdate,
    FornecedorCreate,
    FornecedorPublic,
    FornecedorUpdate,
)

router = APIRouter(prefix="/fornecedores", tags=["fornecedores"])

ViewGuard = Depends(require_permission("view_fornecedores"))
ManageGuard = Depends(require_permission("manage_fornecedores"))


def _to_public(f: object) -> FornecedorPublic:
    from app.models import Fornecedor

    assert isinstance(f, Fornecedor)
    return FornecedorPublic(
        id=f.id,
        company_name=f.company_name,
        cnpj=f.cnpj,
        address=f.address,
        notes=f.notes,
        categories=[FornecedorCategoryEnum(c.category) for c in f.categorias],
        contatos=[
            FornecedorContatoPublic(
                id=c.id,
                fornecedor_id=c.fornecedor_id,
                name=c.name,
                telefone=c.telefone,
                whatsapp=c.whatsapp,
                description=c.description,
            )
            for c in f.contatos
        ],
    )


@router.get("", response_model=list[FornecedorPublic])
def list_fornecedores(
    session: SessionDep,
    search: str | None = None,
    category: FornecedorCategoryEnum | None = None,
    _: None = ViewGuard,
) -> list[FornecedorPublic]:
    fornecedores = crud.get_fornecedores(
        session=session, search=search, category=category
    )
    return [_to_public(f) for f in fornecedores]


@router.post("", response_model=FornecedorPublic, status_code=HTTPStatus.CREATED)
def create_fornecedor(
    session: SessionDep,
    body: FornecedorCreate,
    _: None = ManageGuard,
) -> FornecedorPublic:
    if body.cnpj:
        existing = session.exec(
            select(Fornecedor).where(Fornecedor.cnpj == body.cnpj)
        ).first()
        if existing:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="A fornecedor with this CNPJ already exists",
            )
    fornecedor = crud.create_fornecedor(session=session, data=body)
    return _to_public(fornecedor)


@router.get("/{fornecedor_id}", response_model=FornecedorPublic)
def get_fornecedor(
    fornecedor_id: uuid.UUID,
    session: SessionDep,
    _: None = ViewGuard,
) -> FornecedorPublic:
    fornecedor = crud.get_fornecedor(session=session, fornecedor_id=fornecedor_id)
    if not fornecedor:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Fornecedor not found"
        )
    return _to_public(fornecedor)


@router.patch("/{fornecedor_id}", response_model=FornecedorPublic)
def update_fornecedor(
    fornecedor_id: uuid.UUID,
    session: SessionDep,
    body: FornecedorUpdate,
    _: None = ManageGuard,
) -> FornecedorPublic:
    fornecedor = crud.get_fornecedor(session=session, fornecedor_id=fornecedor_id)
    if not fornecedor:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Fornecedor not found"
        )
    if body.cnpj and body.cnpj != fornecedor.cnpj:
        existing = session.exec(
            select(Fornecedor).where(Fornecedor.cnpj == body.cnpj)
        ).first()
        if existing:
            raise HTTPException(
                status_code=HTTPStatus.CONFLICT,
                detail="A fornecedor with this CNPJ already exists",
            )
    updated = crud.update_fornecedor(session=session, fornecedor=fornecedor, data=body)
    return _to_public(updated)


@router.delete("/{fornecedor_id}", status_code=HTTPStatus.NO_CONTENT)
def delete_fornecedor(
    fornecedor_id: uuid.UUID,
    session: SessionDep,
    _: None = ManageGuard,
) -> None:
    fornecedor = crud.get_fornecedor(session=session, fornecedor_id=fornecedor_id)
    if not fornecedor:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Fornecedor not found"
        )
    crud.delete_fornecedor(session=session, fornecedor=fornecedor)


@router.post(
    "/{fornecedor_id}/contatos",
    response_model=FornecedorContatoPublic,
    status_code=HTTPStatus.CREATED,
)
def create_contato(
    fornecedor_id: uuid.UUID,
    session: SessionDep,
    body: FornecedorContatoCreate,
    _: None = ManageGuard,
) -> FornecedorContatoPublic:
    fornecedor = crud.get_fornecedor(session=session, fornecedor_id=fornecedor_id)
    if not fornecedor:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Fornecedor not found"
        )
    contato = crud.create_contato(
        session=session, fornecedor_id=fornecedor_id, data=body
    )
    return FornecedorContatoPublic(
        id=contato.id,
        fornecedor_id=contato.fornecedor_id,
        name=contato.name,
        telefone=contato.telefone,
        whatsapp=contato.whatsapp,
        description=contato.description,
    )


@router.patch(
    "/{fornecedor_id}/contatos/{contato_id}",
    response_model=FornecedorContatoPublic,
)
def update_contato(
    fornecedor_id: uuid.UUID,
    contato_id: uuid.UUID,
    session: SessionDep,
    body: FornecedorContatoUpdate,
    _: None = ManageGuard,
) -> FornecedorContatoPublic:
    contato = session.exec(
        select(FornecedorContato).where(
            FornecedorContato.id == contato_id,
            FornecedorContato.fornecedor_id == fornecedor_id,
        )
    ).first()
    if not contato:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Contato not found"
        )
    contato = crud.update_contato(session=session, contato=contato, data=body)
    return FornecedorContatoPublic(
        id=contato.id,
        fornecedor_id=contato.fornecedor_id,
        name=contato.name,
        telefone=contato.telefone,
        whatsapp=contato.whatsapp,
        description=contato.description,
    )


@router.delete(
    "/{fornecedor_id}/contatos/{contato_id}",
    status_code=HTTPStatus.NO_CONTENT,
)
def delete_contato(
    fornecedor_id: uuid.UUID,
    contato_id: uuid.UUID,
    session: SessionDep,
    _: None = ManageGuard,
) -> None:
    contato = session.exec(
        select(FornecedorContato).where(
            FornecedorContato.id == contato_id,
            FornecedorContato.fornecedor_id == fornecedor_id,
        )
    ).first()
    if not contato:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Contato not found"
        )
    crud.delete_contato(session=session, contato=contato)
